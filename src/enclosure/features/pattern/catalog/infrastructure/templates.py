from __future__ import annotations

from ..domain import manifest


def pattern_template_targets(
    pattern: manifest.Pattern,
) -> tuple[str, ...]:
    return tuple(pattern_file.target for pattern_file in pattern.files)


__all__ = ["pattern_template_targets"]
