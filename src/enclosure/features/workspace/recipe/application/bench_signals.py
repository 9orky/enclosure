from __future__ import annotations

from collections import Counter

from .. import domain


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
    grouped_reports: dict[str, list[domain.RecipeBenchReport]] = {}
    for report in reports:
        if not report.selected.module_name:
            continue
        if any(
            violation.code in {"missing_role_recipe", "non_archetype_role_recipe"}
            for violation in report.violations
        ):
            continue
        grouped_reports.setdefault(report.role_name or "unknown", []).append(report)
    return {
        role_name: tuple(role_reports)
        for role_name, role_reports in sorted(grouped_reports.items())
    }


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


__all__ = [
    "bench_all_classification",
    "bench_classification",
    "bench_recurrence_for",
    "reports_by_role",
]
