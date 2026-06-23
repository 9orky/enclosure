from __future__ import annotations

from collections.abc import Mapping
from fnmatch import fnmatch
from pathlib import Path

from enclosure.shared.scaffolding import RenderedScaffoldFile, Scaffold, scaffolding

from . import domain, infrastructure


class PatternFitService:
    def __init__(
        self,
        pattern_root: Path,
        pattern_config: domain.PatternFitConfig,
    ) -> None:
        self._pattern_root = pattern_root
        self._pattern_config = pattern_config

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
            pattern_empty=pattern.is_empty(),
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

        scaffolding.write(
            tuple(
                _preview_file_to_rendered_file(preview_file)
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

    def _load_pattern(self, pattern_name: str) -> Scaffold | None:
        try:
            return scaffolding.load(self._pattern_root, pattern_name)
        except LookupError:
            return None

    def _render_files(
        self,
        pattern: Scaffold,
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
    ) -> tuple[RenderedScaffoldFile, ...]:
        return scaffolding.render(
            pattern,
            scaffolding.load_all(self._pattern_root),
            project_root,
            target_path,
            dict(variables),
        )

    def _plan_preview_files(
        self,
        rendered_files: tuple[RenderedScaffoldFile, ...],
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


def _current_service() -> PatternFitService:
    return PatternFitService(
        infrastructure.current_pattern_root(),
        infrastructure.load_fit_config(),
    )


def _preview_file_to_rendered_file(
    preview_file: domain.PatternPreviewFile,
) -> RenderedScaffoldFile:
    return RenderedScaffoldFile(
        source_path=preview_file.source_path,
        target_path=preview_file.target_path,
        relative_path=preview_file.relative_path,
        content=preview_file.content,
    )


def _preview_status_for(
    rendered_file: RenderedScaffoldFile,
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


__all__ = [
    "PatternFitService",
    "materialize_pattern",
    "preview_pattern",
]
