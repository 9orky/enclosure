from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath

from . import models


def findings(
    stream_files: dict[str, tuple[models.FileMap, ...]],
) -> tuple[models.CoherenceFinding, ...]:
    naming_findings: list[models.CoherenceFinding] = []
    for stream, files in stream_files.items():
        segment_styles: dict[str, str] = {}
        for segment in path_segments(stream, files):
            style = segment_style(segment)
            if style:
                segment_styles[segment] = style
        if not segment_styles:
            continue

        dominant_style = dominant_segment_style(segment_styles)
        for segment, style in sorted(segment_styles.items()):
            if style == dominant_style:
                continue
            naming_findings.append(
                models.CoherenceFinding(
                    stream=stream,
                    axis="naming",
                    subject=segment,
                    detail=(
                        f"Tree segment uses {style}; dominant stream style is "
                        f"{dominant_style}."
                    ),
                    evidence=segment,
                    impact=15,
                )
            )
    return tuple(naming_findings)


def dominant_segment_style(segment_styles: dict[str, str]) -> str:
    style_counts = Counter(segment_styles.values())
    return sorted(
        style_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[0][0]


def path_segments(
    stream: str,
    files: tuple[models.FileMap, ...],
) -> tuple[str, ...]:
    segments: list[str] = []
    for part in PurePosixPath(stream).parts:
        if part:
            segments.append(part)
    for file_map in files:
        if file_map.is_api:
            continue
        segments.extend(part for part in file_map.parts if part)
    return tuple(segments)


def segment_style(segment: str) -> str:
    if not segment or segment.startswith("__"):
        return ""
    has_underscore = "_" in segment
    has_hyphen = "-" in segment
    if segment.lower() == segment and not has_hyphen:
        return "snake_case" if has_underscore else "lowercase"
    if segment.lower() == segment and has_hyphen and not has_underscore:
        return "kebab-case"
    if segment[:1].isupper() and "_" not in segment and "-" not in segment:
        return "PascalCase"
    if segment[:1].islower() and any(char.isupper() for char in segment):
        return "camelCase"
    return "mixed"


__all__ = ["findings"]
