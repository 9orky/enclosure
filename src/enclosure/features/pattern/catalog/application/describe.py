from __future__ import annotations

from pathlib import Path

from enclosure.shared.scaffolding import Scaffold, scaffolding

from ..domain import reference
from ..infrastructure import workspace


def list_patterns(
    *,
    pattern_root: Path,
) -> tuple[reference.PatternSummary, ...]:
    return tuple(_summarize(pattern) for pattern in scaffolding.load_all(pattern_root))


def list_current_patterns(
) -> tuple[reference.PatternSummary, ...]:
    return list_patterns(pattern_root=workspace.current_pattern_root())


def show_pattern(
    pattern_name: str,
    *,
    pattern_root: Path,
) -> reference.PatternSummary | None:
    try:
        return _summarize(scaffolding.load(pattern_root, pattern_name))
    except LookupError:
        return None


def _summarize(
    pattern: Scaffold,
) -> reference.PatternSummary:
    return {
        "name": pattern.name,
        "description": pattern.description,
        "role": pattern.role,
        "ladder": pattern.ladder.summary(),
        "includes": pattern.includes,
        "archetypes": pattern.archetypes,
        "roles_map": pattern.roles_map,
        "inputs": tuple(input_spec.name for input_spec in pattern.inputs),
        "files": tuple(pattern_file.target for pattern_file in pattern.files),
    }


__all__ = [
    "list_current_patterns",
    "list_patterns",
    "show_pattern",
]
