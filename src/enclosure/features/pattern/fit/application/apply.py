from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .. import domain
from . import describe


def materialize_pattern(
    pattern_name: str,
    project_root: Path,
    target_path: Path | str,
    variables: Mapping[str, str],
) -> domain.MaterializePatternResult:
    return describe.current_fit_service().materialize(
        pattern_name,
        project_root,
        target_path,
        variables,
    )


__all__ = ["materialize_pattern"]
