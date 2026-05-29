from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import PurePosixPath

from . import models


def findings(
    stream_files: dict[str, tuple[models.FileMap, ...]],
) -> tuple[models.CoherenceFinding, ...]:
    sibling_findings: list[models.CoherenceFinding] = []
    for parent, streams in sibling_groups(stream_files).items():
        if len(streams) < 3:
            continue
        signatures = {
            stream: tree_signature(stream_files[stream]) for stream in streams
        }
        dominant_signature, dominant_count = dominant_tree_signature(signatures)
        if dominant_count < 2:
            continue
        for stream in streams:
            signature = signatures[stream]
            if signature == dominant_signature:
                continue
            sibling_findings.append(
                models.CoherenceFinding(
                    stream=stream,
                    axis="sibling_pattern",
                    subject=parent or ".",
                    detail="Stream tree shape differs from sibling majority.",
                    evidence=signature_evidence(signature, dominant_signature),
                    impact=20,
                )
            )
    return tuple(sibling_findings)


def sibling_groups(
    stream_files: dict[str, tuple[models.FileMap, ...]],
) -> dict[str, tuple[str, ...]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for stream in stream_files:
        groups[parent_stream(stream)].append(stream)
    return {
        parent: tuple(sorted(streams))
        for parent, streams in sorted(groups.items())
    }


def parent_stream(stream: str) -> str:
    parts = PurePosixPath(stream).parts
    if len(parts) <= 1:
        return ""
    return "/".join(parts[:-1])


def tree_signature(files: tuple[models.FileMap, ...]) -> tuple[str, ...]:
    entries: set[str] = set()
    for file in files:
        if file.is_api:
            entries.add("api")
        elif file.layer:
            entries.add(file.layer)
        else:
            entries.add(f"unclassified:{file.root_part}")
    return tuple(sorted(entries))


def dominant_tree_signature(
    signatures: dict[str, tuple[str, ...]],
) -> tuple[tuple[str, ...], int]:
    signature_counts = Counter(signatures.values())
    return sorted(
        signature_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[0]


def signature_evidence(
    actual: tuple[str, ...],
    expected: tuple[str, ...],
) -> str:
    actual_text = ", ".join(actual) if actual else "none"
    expected_text = ", ".join(expected) if expected else "none"
    return f"actual [{actual_text}], sibling-majority [{expected_text}]"


__all__ = ["findings"]
