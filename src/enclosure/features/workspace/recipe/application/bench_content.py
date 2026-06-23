from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .. import domain

_BENCH_CONTENT_LIMIT = 12_000


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


__all__ = [
    "bench_modules_with_content_weights",
    "module_file_contents",
]
