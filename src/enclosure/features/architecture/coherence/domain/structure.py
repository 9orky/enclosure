from __future__ import annotations

from collections import defaultdict

from . import models


def findings(
    stream_files: dict[str, tuple[models.FileMap, ...]],
    has_api_rule: bool,
) -> tuple[models.CoherenceFinding, ...]:
    tree_findings: list[models.CoherenceFinding] = []
    for stream, files in stream_files.items():
        if has_api_rule and not any(file.is_api for file in files):
            tree_findings.append(
                models.CoherenceFinding(
                    stream=stream,
                    axis="tree_shape",
                    subject="public seam",
                    detail="Stream has no node matching the configured public seam tag.",
                    evidence=stream,
                    impact=20,
                )
            )

        for root_part, grouped_files in unclassified_roots(files).items():
            evidence = ", ".join(file.source_id for file in grouped_files)
            tree_findings.append(
                models.CoherenceFinding(
                    stream=stream,
                    axis="tree_shape",
                    subject=root_part,
                    detail="Tree node is outside configured layer/API tags.",
                    evidence=evidence,
                    impact=15,
                )
            )

        for layer, layer_files in files_by_layer(files).items():
            compact_sources = tuple(
                file.source_id for file in layer_files if file.source_id == file.layer_root
            )
            nested_sources = tuple(
                file.source_id
                for file in layer_files
                if file.source_id.startswith(f"{file.layer_root}/")
            )
            if compact_sources and nested_sources:
                tree_findings.append(
                    models.CoherenceFinding(
                        stream=stream,
                        axis="tree_shape",
                        subject=layer,
                        detail="Layer mixes root-node and nested-node shapes.",
                        evidence=compact_sources[0],
                        impact=10,
                    )
                )
    return tuple(tree_findings)


def unclassified_roots(
    files: tuple[models.FileMap, ...],
) -> dict[str, tuple[models.FileMap, ...]]:
    grouped: dict[str, list[models.FileMap]] = defaultdict(list)
    for file in files:
        if file.is_api or file.layer:
            continue
        grouped[file.root_part].append(file)
    return {
        root: tuple(sorted(root_files, key=lambda file: file.source_id))
        for root, root_files in sorted(grouped.items())
    }


def files_by_layer(
    files: tuple[models.FileMap, ...],
) -> dict[str, tuple[models.FileMap, ...]]:
    grouped: dict[str, list[models.FileMap]] = defaultdict(list)
    for file in files:
        if file.layer:
            grouped[file.layer].append(file)
    return {
        layer: tuple(sorted(layer_files, key=lambda file: file.source_id))
        for layer, layer_files in sorted(grouped.items())
    }


__all__ = [
    "files_by_layer",
    "findings",
    "unclassified_roots",
]
