from __future__ import annotations

from collections.abc import Mapping
from fnmatch import fnmatch
from pathlib import Path

from . import domain, infrastructure


class PatternFitService:
    def __init__(
        self,
        pattern_root: Path,
        pattern_config: domain.PatternFitConfig,
    ) -> None:
        self._pattern_root = pattern_root
        self._pattern_config = pattern_config
        self._repository = infrastructure.FilePatternRepository(pattern_root)
        self._renderer = infrastructure.FilePatternRenderer()
        self._materializer = infrastructure.FilePatternMaterializer()

    def preview(
        self,
        pattern_name: str,
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
    ) -> domain.PatternFitReport:
        project_root = project_root.resolve()
        pattern = self._load_pattern(pattern_name)
        if pattern is None:
            return domain.PatternFitReport(
                pattern_name=pattern_name,
                project_root=project_root,
                pattern_found=False,
                pattern_empty=False,
                create_paths=(),
                skipped_paths=(),
                preview_files=(),
            )

        rendered_files = self._render_files(pattern, project_root, target_path, variables)
        preview_files = self._plan_preview_files(rendered_files)
        create_paths, skipped_paths = _paths_from_preview_files(preview_files)
        return domain.PatternFitReport(
            pattern_name=pattern.name,
            project_root=project_root,
            pattern_found=True,
            pattern_empty=_pattern_is_empty(pattern),
            create_paths=create_paths,
            skipped_paths=skipped_paths,
            preview_files=preview_files,
        )

    def materialize(
        self,
        pattern_name: str,
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
    ) -> domain.MaterializePatternResult:
        report = self.preview(pattern_name, project_root, target_path, variables)
        if not report.pattern_found:
            return domain.MaterializePatternResult(
                pattern_name=pattern_name,
                project_root=report.project_root,
                pattern_found=False,
                pattern_empty=False,
                created_paths=(),
                skipped_paths=(),
            )

        self._materializer.write_files(
            tuple(
                preview_file_to_rendered_file(preview_file)
                for preview_file in report.preview_files
            ),
            create_paths=report.create_paths,
        )
        return domain.MaterializePatternResult(
            pattern_name=report.pattern_name,
            project_root=report.project_root,
            pattern_found=True,
            pattern_empty=report.pattern_empty,
            created_paths=report.create_paths,
            skipped_paths=report.skipped_paths,
        )

    def _load_pattern(self, pattern_name: str) -> domain.Pattern | None:
        try:
            return self._repository.get_by_name(pattern_name)
        except LookupError:
            return None

    def _render_files(
        self,
        pattern: domain.Pattern,
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
    ) -> tuple[domain.RenderedPatternFile, ...]:
        patterns_by_name = {
            item.name: item
            for item in self._repository.find_all()
        }
        target_relative_path = infrastructure.normalize_target_path(project_root, target_path)
        context = self._render_context(
            pattern,
            patterns_by_name,
            target_relative_path,
            variables,
        )

        rendered_files: list[domain.RenderedPatternFile] = []
        for rendered_pattern in _patterns_for_rendering(pattern, patterns_by_name):
            rendered_files.extend(
                self._renderer.render_files(
                    rendered_pattern,
                    project_root=project_root,
                    context=context,
                )
            )
        return tuple(rendered_files)

    def _render_context(
        self,
        pattern: domain.Pattern,
        patterns_by_name: Mapping[str, domain.Pattern],
        target_relative_path: Path,
        variables: Mapping[str, str],
    ) -> dict[str, object]:
        raw_variables = dict(variables)
        defaults = domain.target_defaults_for(target_relative_path)
        context: dict[str, object] = {
            "target": domain.target_context_for(target_relative_path),
        }
        for input_spec in _input_specs_for(pattern, patterns_by_name):
            value = _resolve_input_value(input_spec, raw_variables, defaults)
            context[input_spec.name] = domain.variable_context_for(value)
        for name, value in raw_variables.items():
            if name not in context:
                context[name] = domain.variable_context_for(value)
        return context

    def _plan_preview_files(
        self,
        rendered_files: tuple[domain.RenderedPatternFile, ...],
    ) -> tuple[domain.PatternPreviewFile, ...]:
        return tuple(
            domain.PatternPreviewFile(
                source_path=rendered_file.source_path,
                target_path=rendered_file.target_path,
                relative_path=rendered_file.relative_path,
                status=_preview_status_for(rendered_file, self._pattern_config),
                content=rendered_file.content,
            )
            for rendered_file in rendered_files
        )


def preview_pattern(
    pattern_name: str,
    project_root: Path,
    target_path: Path | str,
    variables: Mapping[str, str],
) -> domain.PatternFitReport:
    return _current_service().preview(pattern_name, project_root, target_path, variables)


def materialize_pattern(
    pattern_name: str,
    project_root: Path,
    target_path: Path | str,
    variables: Mapping[str, str],
) -> domain.MaterializePatternResult:
    return _current_service().materialize(pattern_name, project_root, target_path, variables)


def preview_file_to_rendered_file(
    preview_file: domain.PatternPreviewFile,
) -> domain.RenderedPatternFile:
    return domain.RenderedPatternFile(
        source_path=preview_file.source_path,
        target_path=preview_file.target_path,
        relative_path=preview_file.relative_path,
        content=preview_file.content,
    )


def _current_service() -> PatternFitService:
    return PatternFitService(
        infrastructure.current_pattern_root(),
        infrastructure.load_fit_config(),
    )


def _patterns_for_rendering(
    pattern: domain.Pattern,
    patterns_by_name: Mapping[str, domain.Pattern],
) -> tuple[domain.Pattern, ...]:
    return included_patterns_for(pattern, patterns_by_name, trail=()) + (pattern,)


def _input_specs_for(
    pattern: domain.Pattern,
    patterns_by_name: Mapping[str, domain.Pattern],
) -> tuple[domain.PatternInputSpec, ...]:
    input_specs: list[domain.PatternInputSpec] = []
    for included_pattern in included_patterns_for(
        pattern,
        patterns_by_name,
        trail=(),
    ):
        input_specs.extend(included_pattern.inputs)
    input_specs.extend(pattern.inputs)
    return tuple(input_specs)


def _resolve_input_value(
    input_spec: domain.PatternInputSpec,
    variables: Mapping[str, str],
    defaults: Mapping[str, str],
) -> object:
    if input_spec.name in variables:
        return variables[input_spec.name]
    if input_spec.default_from and input_spec.default_from in defaults:
        return defaults[input_spec.default_from]
    if input_spec.default:
        return input_spec.default
    if input_spec.required:
        raise ValueError(f"Missing required Pattern variable: {input_spec.name}")
    return ""


def _preview_status_for(
    rendered_file: domain.RenderedPatternFile,
    pattern_config: domain.PatternFitConfig,
) -> domain.PatternPreviewStatus:
    relative_path = rendered_file.relative_path.as_posix()
    if any(fnmatch(relative_path, pattern) for pattern in pattern_config.skip):
        return domain.PatternPreviewStatus.SKIP_CONFIG
    if rendered_file.target_path.exists():
        return domain.PatternPreviewStatus.SKIP_EXISTS
    return domain.PatternPreviewStatus.CREATE


def _paths_from_preview_files(
    preview_files: tuple[domain.PatternPreviewFile, ...],
) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    create_paths = tuple(
        preview_file.target_path
        for preview_file in preview_files
        if preview_file.status is domain.PatternPreviewStatus.CREATE
    )
    skipped_paths = tuple(
        preview_file.target_path
        for preview_file in preview_files
        if preview_file.status is not domain.PatternPreviewStatus.CREATE
    )
    return create_paths, skipped_paths


def _pattern_is_empty(pattern: domain.Pattern) -> bool:
    return not pattern.files and not pattern.includes


def included_patterns_for(
    pattern: domain.Pattern,
    patterns_by_name: Mapping[str, domain.Pattern],
    *,
    trail: tuple[str, ...],
) -> tuple[domain.Pattern, ...]:
    patterns: list[domain.Pattern] = []
    for include_name in pattern.includes:
        if include_name in trail:
            cycle = " -> ".join(trail + (include_name,))
            raise ValueError(f"Pattern include cycle: {cycle}")
        included_pattern = patterns_by_name.get(include_name)
        if included_pattern is None:
            raise ValueError(f"Pattern include not found: {include_name}")
        patterns.extend(
            included_patterns_for(
                included_pattern,
                patterns_by_name,
                trail=trail + (pattern.name,),
            )
        )
        patterns.append(included_pattern)
    return tuple(patterns)


__all__ = [
    "PatternFitService",
    "included_patterns_for",
    "materialize_pattern",
    "preview_file_to_rendered_file",
    "preview_pattern",
]
