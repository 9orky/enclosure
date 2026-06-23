from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path

from enclosure.shared.scaffolding import ScaffoldError
from .. import domain, infrastructure
from . import catalog, drift

_BENCH_CONTENT_LIMIT = 12_000


class RecipeBenchService:
    def __init__(self, workspace: infrastructure.RecipeWorkspace) -> None:
        self._workspace = workspace

    def build_module_report(self, module_name: str) -> domain.RecipeBenchReport:
        project_root = self._workspace.project_root()
        selected_module = module_name.strip().replace("\\", "/")
        violations: list[domain.RecipeCheckViolation] = []
        try:
            recipes = self._workspace.load_recipes()
        except ScaffoldError as exc:
            return empty_bench_report(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=Path(),
                selected_module=selected_module,
                role_name="",
                violation=domain.RecipeCheckViolation(
                    code="invalid_manifest",
                    message=str(exc),
                ),
            )

        recipes_by_name = catalog.recipes_by_name(recipes)
        catalog.validate_recipe_catalog(violations, recipes, recipes_by_name)
        roles_map = self._workspace.config().roles_map
        catalog.validate_config_roles_map(
            violations,
            roles_map=roles_map,
            recipes_by_name=recipes_by_name,
        )

        subject_root = self._workspace.subject_root()
        role_name = roles_map.get(selected_module, "")
        if not role_name:
            return empty_bench_report(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=subject_root,
                selected_module=selected_module,
                role_name="",
                violation=domain.RecipeCheckViolation(
                    code="module_unmapped",
                    message=(
                        "Module is not mapped in workspace.recipe.roles_map: "
                        f"{selected_module}"
                    ),
                    recipe_name="workspace.recipe.roles_map",
                ),
            )

        role_recipe = catalog.recipe_for_role(role_name, recipes_by_name)
        if role_recipe is None:
            return empty_bench_report(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=subject_root,
                selected_module=selected_module,
                role_name=role_name,
                violation=domain.RecipeCheckViolation(
                    code="missing_role_recipe",
                    message=(
                        f"roles_map references missing recipe {role_name} "
                        f"for {selected_module}"
                    ),
                    recipe_name="workspace.recipe.roles_map",
                ),
            )

        selected_path = subject_root / selected_module
        if not selected_path.is_dir():
            return empty_bench_report(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=subject_root,
                selected_module=selected_module,
                role_name=role_name,
                violation=domain.RecipeCheckViolation(
                    code="mapped_module_missing",
                    message=f"Mapped module does not exist: {selected_module}",
                    recipe_name="workspace.recipe.roles_map",
                ),
            )

        same_role_module_names = tuple(
            sorted(
                candidate_module
                for candidate_module, candidate_role in roles_map.items()
                if candidate_role == role_name
            )
        )
        modules: list[domain.RecipeBenchModule] = []
        for candidate_module in same_role_module_names:
            module_path = subject_root / candidate_module
            if not module_path.is_dir():
                violations.append(
                    domain.RecipeCheckViolation(
                        code="mapped_module_missing",
                        message=f"Mapped module does not exist: {candidate_module}",
                        recipe_name="workspace.recipe.roles_map",
                    )
                )
                continue

            target_path = self._workspace.subject_target_root() / candidate_module
            try:
                rendered_files = self._workspace.render_files(
                    role_recipe,
                    recipes_by_name=recipes_by_name,
                    project_root=project_root,
                    target_path=target_path,
                    variables=catalog.sample_variables_for_rendering(
                        role_recipe,
                        recipes_by_name,
                    ),
                )
            except ValueError as exc:
                violations.append(
                    domain.RecipeCheckViolation(
                        code="role_render_failed",
                        message=f"{role_name}: {exc}",
                        recipe_name="workspace.recipe.roles_map",
                    )
                )
                continue

            expected_files = drift.module_relative_rendered_paths(
                rendered_files,
                target_path=target_path,
            )
            actual_files = drift.actual_files_for(
                module_path,
                project_root=project_root,
                config=self._workspace.config(),
            )
            missing_files, residue_files = drift.drift_files_for(
                role_recipe,
                recipes_by_name=recipes_by_name,
                expected_files=set(expected_files),
                actual_files=set(actual_files),
            )
            slot_growth_files = tuple(
                sorted(set(actual_files) - set(expected_files) - set(residue_files))
            )
            modules.append(
                domain.RecipeBenchModule(
                    module_name=candidate_module,
                    actual_files=tuple(sorted(actual_files)),
                    expected_files=expected_files,
                    residue_files=residue_files,
                    slot_growth_files=slot_growth_files,
                    missing_files=missing_files,
                    file_contents=module_file_contents(module_path, actual_files)
                    if candidate_module == selected_module
                    else (),
                )
            )

        modules = list(
            bench_modules_with_content_weights(
                architecture_root=subject_root,
                modules=tuple(modules),
            )
        )
        selected = next(
            (
                bench_module
                for bench_module in modules
                if bench_module.module_name == selected_module
            ),
            domain.RecipeBenchModule(module_name=""),
        )
        recurrence = bench_recurrence_for(modules, signal="residue")
        slot_growth_recurrence = bench_recurrence_for(modules, signal="slot_growth")
        content_weight_recurrence = bench_recurrence_for(
            modules,
            signal="content_weight",
        )
        classification = bench_classification(
            selected=selected,
            modules=tuple(modules),
            recurrence=recurrence,
            slot_growth_recurrence=slot_growth_recurrence,
            content_weight_recurrence=content_weight_recurrence,
        )
        return domain.RecipeBenchReport(
            project_root=project_root,
            recipe_root=self._workspace.recipe_root(),
            architecture_root=subject_root,
            selected_module=selected_module,
            role_name=role_name,
            classification=classification,
            same_role_modules=tuple(modules),
            recurrence=recurrence,
            slot_growth_recurrence=slot_growth_recurrence,
            content_weight_recurrence=content_weight_recurrence,
            selected=selected,
            violations=tuple(violations),
        )

    def build_workspace_report(self) -> domain.RecipeBenchAllReport:
        project_root = self._workspace.project_root()
        try:
            subject_root = self._workspace.subject_root()
        except RuntimeError as exc:
            return domain.RecipeBenchAllReport(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=Path(),
                classification="local",
                violations=(
                    domain.RecipeCheckViolation(
                        code="config_error",
                        message=str(exc),
                    ),
                ),
            )

        reports = tuple(
            self.build_module_report(module_name)
            for module_name in sorted(self._workspace.config().roles_map)
        )
        violations = tuple(
            violation
            for report in reports
            for violation in report.violations
        )
        return domain.RecipeBenchAllReport(
            project_root=project_root,
            recipe_root=self._workspace.recipe_root(),
            architecture_root=subject_root,
            classification=bench_all_classification(reports),
            reports=reports,
            violations=violations,
        )



def bench_recurrence_for(
    modules: tuple[domain.RecipeBenchModule, ...] | list[domain.RecipeBenchModule],
    *,
    signal: str,
) -> tuple[domain.RecipeBenchRecurrence, ...]:
    modules_by_path: dict[str, list[str]] = {}
    for bench_module in modules:
        for signal_path in _bench_signal_paths(bench_module, signal=signal):
            modules_by_path.setdefault(signal_path, []).append(bench_module.module_name)

    counts = Counter(
        signal_path
        for bench_module in modules
        for signal_path in _bench_signal_paths(bench_module, signal=signal)
    )
    module_count = len(tuple(modules))
    return tuple(
        domain.RecipeBenchRecurrence(
            path=signal_path,
            count=count,
            modules=tuple(sorted(modules_by_path[signal_path])),
            label=_bench_recurrence_label(count, module_count),
        )
        for signal_path, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _bench_signal_paths(
    bench_module: domain.RecipeBenchModule,
    *,
    signal: str,
) -> tuple[str, ...]:
    if signal == "residue":
        return bench_module.residue_files
    if signal == "slot_growth":
        return bench_module.slot_growth_files
    if signal == "content_weight":
        return tuple(weight.path for weight in bench_module.content_weights)
    raise ValueError(f"Unsupported bench signal: {signal}")


def _bench_recurrence_label(count: int, module_count: int) -> str:
    if count <= 1:
        return "local"
    if module_count and count / module_count >= 0.67:
        return "established"
    return "emerging"


def bench_classification(
    *,
    selected: domain.RecipeBenchModule,
    modules: tuple[domain.RecipeBenchModule, ...],
    recurrence: tuple[domain.RecipeBenchRecurrence, ...],
    slot_growth_recurrence: tuple[domain.RecipeBenchRecurrence, ...],
    content_weight_recurrence: tuple[domain.RecipeBenchRecurrence, ...],
) -> str:
    if not selected.module_name or not selected.has_warp():
        return "clean"

    selected_recurrence = (
        _selected_recurrence_for(selected.residue_files, recurrence)
        + _selected_recurrence_for(
            selected.slot_growth_files,
            slot_growth_recurrence,
        )
        + _selected_recurrence_for(
            tuple(weight.path for weight in selected.content_weights),
            content_weight_recurrence,
        )
    )
    if _same_role_warp_is_unstable(modules):
        return "unstable"
    if any(item.label == "established" for item in selected_recurrence):
        return "established"
    if any(item.count > 1 for item in selected_recurrence):
        return "emerging"
    return "local"


def _selected_recurrence_for(
    paths: tuple[str, ...],
    recurrence: tuple[domain.RecipeBenchRecurrence, ...],
) -> tuple[domain.RecipeBenchRecurrence, ...]:
    recurrence_by_path = {item.path: item for item in recurrence}
    return tuple(
        recurrence_by_path[path]
        for path in paths
        if path in recurrence_by_path
    )


def _same_role_warp_is_unstable(
    modules: tuple[domain.RecipeBenchModule, ...],
) -> bool:
    warped_modules = tuple(module for module in modules if module.has_warp())
    if len(warped_modules) <= 1:
        return False

    fingerprints = {
        _bench_module_warp_fingerprint(module)
        for module in warped_modules
    }
    if len(fingerprints) <= 1:
        return False

    common_paths = set(_bench_module_warp_paths(warped_modules[0]))
    for module in warped_modules[1:]:
        common_paths &= set(_bench_module_warp_paths(module))
    return not common_paths


def _bench_module_warp_fingerprint(
    module: domain.RecipeBenchModule,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            (
                *(f"missing:{path}" for path in module.missing_files),
                *(f"residue:{path}" for path in module.residue_files),
                *(f"slot:{path}" for path in module.slot_growth_files),
                *(f"weight:{weight.path}" for weight in module.content_weights),
            )
        )
    )


def _bench_module_warp_paths(module: domain.RecipeBenchModule) -> tuple[str, ...]:
    return tuple(
        sorted(
            (
                *module.missing_files,
                *module.residue_files,
                *module.slot_growth_files,
                *(weight.path for weight in module.content_weights),
            )
        )
    )


def bench_all_classification(
    reports: tuple[domain.RecipeBenchReport, ...],
) -> str:
    if not any(report.local_warp_count for report in reports):
        return "clean"
    classifications = {report.classification for report in reports}
    if "unstable" in classifications:
        return "unstable"
    if "established" in classifications:
        return "established"
    if "emerging" in classifications:
        return "emerging"
    return "local"


def reports_by_role(
    reports: tuple[domain.RecipeBenchReport, ...],
) -> dict[str, tuple[domain.RecipeBenchReport, ...]]:
    reports_by_role: dict[str, list[domain.RecipeBenchReport]] = {}
    for report in reports:
        reports_by_role.setdefault(report.role_name or "unknown", []).append(report)
    return {
        role_name: tuple(role_reports)
        for role_name, role_reports in sorted(reports_by_role.items())
    }


def empty_bench_report(
    *,
    project_root: Path,
    recipe_root: Path,
    selected_module: str,
    architecture_root: Path,
    role_name: str,
    violation: domain.RecipeCheckViolation,
) -> domain.RecipeBenchReport:
    return domain.RecipeBenchReport(
        project_root=project_root,
        recipe_root=recipe_root,
        architecture_root=architecture_root,
        selected_module=selected_module,
        role_name=role_name,
        classification="local",
        violations=(violation,),
    )


def bench_modules_with_content_weights(
    *,
    architecture_root: Path,
    modules: tuple[domain.RecipeBenchModule, ...],
) -> tuple[domain.RecipeBenchModule, ...]:
    metrics_by_module: dict[str, dict[str, tuple[int, int]]] = {}
    metrics_by_path: dict[str, list[tuple[int, int]]] = {}
    for module in modules:
        module_metrics: dict[str, tuple[int, int]] = {}
        module_path = architecture_root / module.module_name
        for relative_path in module.actual_files:
            metrics = _content_metrics_for(module_path / relative_path)
            if metrics is None:
                continue
            module_metrics[relative_path] = metrics
            metrics_by_path.setdefault(relative_path, []).append(metrics)
        metrics_by_module[module.module_name] = module_metrics

    weighted_modules: list[domain.RecipeBenchModule] = []
    for module in modules:
        weights: list[domain.RecipeBenchContentWeight] = []
        for relative_path, metrics in metrics_by_module[module.module_name].items():
            reason = _content_weight_reason(
                metrics,
                baseline_metrics=tuple(metrics_by_path.get(relative_path, ())),
            )
            if not reason:
                continue
            line_count, symbol_count = metrics
            weights.append(
                domain.RecipeBenchContentWeight(
                    path=relative_path,
                    line_count=line_count,
                    symbol_count=symbol_count,
                    reason=reason,
                )
            )
        weighted_modules.append(
            replace(
                module,
                content_weights=tuple(sorted(weights, key=lambda weight: weight.path)),
            )
        )
    return tuple(weighted_modules)


def _content_metrics_for(path: Path) -> tuple[int, int] | None:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    return len(content.splitlines()), 0


def _content_weight_reason(
    metrics: tuple[int, int],
    *,
    baseline_metrics: tuple[tuple[int, int], ...],
) -> str:
    line_count, symbol_count = metrics
    reasons: list[str] = []
    if line_count >= 300:
        reasons.append(f"{line_count} lines")
    if symbol_count >= 20:
        reasons.append(f"{symbol_count} symbols")

    if len(baseline_metrics) > 1:
        median_lines = _median(tuple(item[0] for item in baseline_metrics))
        median_symbols = _median(tuple(item[1] for item in baseline_metrics))
        if median_lines and line_count >= 80 and line_count >= median_lines * 2:
            reasons.append(f"{line_count} lines vs median {median_lines}")
        if median_symbols and symbol_count >= 8 and symbol_count >= median_symbols * 2:
            reasons.append(f"{symbol_count} symbols vs median {median_symbols}")

    return "; ".join(dict.fromkeys(reasons))


def _median(values: tuple[int, ...]) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) // 2


def module_file_contents(
    module_path: Path,
    actual_files: set[str],
) -> tuple[domain.RecipeBenchFileContent, ...]:
    contents: list[domain.RecipeBenchFileContent] = []
    for relative_path in sorted(actual_files):
        path = module_path / relative_path
        try:
            content = path.read_text(encoding="utf-8")
            truncated = len(content) > _BENCH_CONTENT_LIMIT
            if truncated:
                content = content[:_BENCH_CONTENT_LIMIT]
        except UnicodeDecodeError:
            content = "[binary or non-UTF-8 file]"
            truncated = False
        contents.append(
            domain.RecipeBenchFileContent(
                path=relative_path,
                content=content,
                truncated=truncated,
            )
        )
    return tuple(contents)




__all__ = [
    "RecipeBenchService",
    "bench_all_classification",
    "bench_classification",
    "bench_modules_with_content_weights",
    "bench_recurrence_for",
    "module_file_contents",
    "reports_by_role",
]
