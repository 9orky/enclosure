from __future__ import annotations

from fnmatch import fnmatch

from enclosure.shared.scaffolding import RenderedScaffoldFile

from .. import domain


def preview_status_for(
    rendered_file: RenderedScaffoldFile,
    pattern_config: domain.PatternFitConfig,
) -> domain.PatternPreviewStatus:
    relative_path = rendered_file.relative_path.as_posix()
    if any(fnmatch(relative_path, pattern) for pattern in pattern_config.skip):
        return domain.PatternPreviewStatus.SKIP_CONFIG
    if rendered_file.target_path.exists():
        return domain.PatternPreviewStatus.SKIP_EXISTS
    return domain.PatternPreviewStatus.CREATE


__all__ = ["preview_status_for"]
