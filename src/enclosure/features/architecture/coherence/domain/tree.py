from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

from modwire import CodeMap
from modwire.architecture import TagMatcher

from enclosure.features.architecture import flow

from . import models


def map_files(
    code_map: CodeMap,
    config: object,
    stream_rule: object,
    api_rule: object | None,
    layer_rules: dict[str, object],
) -> dict[str, models.FileMap]:
    matcher = TagMatcher(config)
    file_maps: dict[str, models.FileMap] = {}
    for source_id in sorted(code_map.extraction_result.files):
        stream = matched_tag_path(source_id, matcher, stream_rule)
        if not stream:
            continue
        parts = relative_parts(source_id, stream)
        if not parts:
            continue
        layer, layer_root = layer_match(source_id, matcher, layer_rules)
        file_maps[source_id] = models.FileMap(
            source_id=source_id,
            stream=stream,
            layer=layer,
            layer_root=layer_root,
            is_api=is_api_match(source_id, matcher, api_rule),
            root_part=parts[0],
            parts=parts,
        )
    return file_maps


def stream_files(
    file_maps: dict[str, models.FileMap],
) -> dict[str, tuple[models.FileMap, ...]]:
    builders: dict[str, list[models.FileMap]] = defaultdict(list)
    for file_map in file_maps.values():
        builders[file_map.stream].append(file_map)
    return {
        stream: tuple(sorted(files, key=lambda file: file.source_id))
        for stream, files in sorted(builders.items())
    }


def tag_rule(config: object, name: str) -> object | None:
    for rule in getattr(config.rules, "tags", ()):
        if getattr(rule, "name", "") == name:
            return rule
    return None


def stream_rule(config: object) -> object | None:
    tag_rules = {
        getattr(rule, "name", ""): rule for rule in getattr(config.rules, "tags", ())
    }
    realms = tuple(
        realm for realm in flow.configured_realms(config) if realm.module_tag in tag_rules
    )
    for realm in realms:
        if realm.layers:
            return tag_rules[realm.module_tag]
    if realms:
        return tag_rules[realms[0].module_tag]
    return None


def public_seam_rule(config: object, stream_rule: object) -> object | None:
    tag_rules = {
        getattr(rule, "match", ""): rule for rule in getattr(config.rules, "tags", ())
    }
    for pattern in flow.public_seam_patterns(
        config,
        getattr(stream_rule, "match", ""),
    ):
        rule = tag_rules.get(pattern)
        if rule is not None:
            return rule
    return None


def layer_rules(config: object) -> dict[str, object]:
    tag_rules = {
        getattr(rule, "name", ""): rule for rule in getattr(config.rules, "tags", ())
    }
    return {
        name: tag_rules[name]
        for name in getattr(config.rules.flow, "layers", ())
        if name in tag_rules
    }


def target_from_path(
    target_path: str,
    streams: set[str],
    file_maps: dict[str, models.FileMap],
) -> models.ImportTarget | None:
    normalized = target_path.strip("/")
    for stream in sorted(streams, key=lambda value: (-len(value), value)):
        if normalized == stream:
            return stream_api_target(stream, file_maps)
        if normalized.startswith(f"{stream}/"):
            return node_target(stream, normalized, file_maps)
        suffix = f"/{stream}"
        if normalized.endswith(suffix):
            return stream_api_target(stream, file_maps)
        marker = f"/{stream}/"
        marker_index = normalized.rfind(marker)
        if marker_index == -1:
            continue
        remainder = normalized[marker_index + len(marker) :]
        return node_target(stream, f"{stream}/{remainder}", file_maps)
    return None


def stream_api_target(
    stream: str,
    file_maps: dict[str, models.FileMap],
) -> models.ImportTarget:
    api_sources = tuple(
        file.source_id
        for file in file_maps.values()
        if file.stream == stream and file.is_api
    )
    if api_sources:
        return models.ImportTarget(stream=stream, source_id=api_sources[0], is_api=True)
    return models.ImportTarget(stream=stream, source_id=stream, is_api=False)


def node_target(
    stream: str,
    source_id: str,
    file_maps: dict[str, models.FileMap],
) -> models.ImportTarget:
    file = file_maps.get(source_id)
    return models.ImportTarget(
        stream=stream,
        source_id=source_id,
        is_api=False if file is None else file.is_api,
    )


def matched_tag_path(source_id: str, matcher: TagMatcher, rule: object) -> str:
    match = matcher.match(source_id, getattr(rule, "name", ""))
    if match is None:
        return ""
    return matcher.display_path(match.captured_path)


def is_api_match(source_id: str, matcher: TagMatcher, api_rule: object | None) -> bool:
    if api_rule is None:
        return False
    return bool(matched_tag_path(source_id, matcher, api_rule))


def layer_match(
    source_id: str,
    matcher: TagMatcher,
    layer_rules_by_name: dict[str, object],
) -> tuple[str, str]:
    for layer, rule in layer_rules_by_name.items():
        layer_root = matched_tag_path(source_id, matcher, rule)
        if not layer_root:
            continue
        return layer, layer_root
    return "", ""


def relative_parts(source_id: str, stream: str) -> tuple[str, ...]:
    normalized = source_id.strip("/")
    prefix = stream.strip("/")
    if normalized == prefix:
        return ()
    if normalized.startswith(f"{prefix}/"):
        return PurePosixPath(normalized[len(prefix) + 1 :]).parts
    return ()


__all__ = [
    "layer_rules",
    "map_files",
    "public_seam_rule",
    "stream_files",
    "stream_rule",
    "tag_rule",
    "target_from_path",
]
