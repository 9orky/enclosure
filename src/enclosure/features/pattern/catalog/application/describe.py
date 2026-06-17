from __future__ import annotations

from pathlib import Path

from ..domain import manifest, reference
from ..infrastructure import repository, templates, workspace


def list_patterns(
    *,
    pattern_root: Path,
) -> tuple[reference.PatternSummary, ...]:
    return tuple(_summarize(pattern) for pattern in _repository(pattern_root).find_all())


def list_current_patterns(
) -> tuple[reference.PatternSummary, ...]:
    return list_patterns(pattern_root=workspace.current_pattern_root())


def show_pattern(
    pattern_name: str,
    *,
    pattern_root: Path,
) -> reference.PatternSummary | None:
    try:
        return _summarize(_repository(pattern_root).get_by_name(pattern_name))
    except LookupError:
        return None


def _repository(
    pattern_root: Path,
) -> repository.FilePatternRepository:
    return repository.FilePatternRepository(pattern_root)


def _summarize(
    pattern: manifest.Pattern,
) -> reference.PatternSummary:
    return {
        "name": pattern.name,
        "description": pattern.description,
        "role": pattern.role.value,
        "ladder": reference.ladder_summary(pattern.ladder),
        "includes": pattern.includes,
        "archetypes": pattern.archetypes,
        "roles_map": pattern.roles_map,
        "inputs": tuple(input_spec.name for input_spec in pattern.inputs),
        "files": templates.pattern_template_targets(pattern),
    }


__all__ = [
    "list_current_patterns",
    "list_patterns",
    "show_pattern",
]
