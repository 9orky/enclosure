from __future__ import annotations

import re
from functools import cache

from code_map.extractors.loader import normalize_source_id


def match_node(node_id, pattern, config, exclusions, *, scope=True, exclude=()):
    language = config.language
    path = normalize_source_id(language, node_id)
    for ignored in (*exclusions.get(pattern, ()), *exclude):
        for normalized_ignored in _normalized_patterns(language, ignored, config):
            if _regex(normalized_ignored, True).match(path):
                return None
    for normalized in _normalized_patterns(language, pattern, config):
        match = _regex(normalized, scope).match(path)
        if match is not None:
            return match.group(1), "*" in normalized or "?" in normalized
    return None


def _normalized_patterns(language, pattern, config):
    normalized = normalize_source_id(language, pattern).strip("/")
    architecture_root = normalize_source_id(
        language,
        getattr(config, "architecture_root", None) or "",
    ).strip("/")
    if not architecture_root:
        return (normalized,)

    root_anchor = architecture_root.split("/", 1)[0]
    is_full_path = normalized == architecture_root or normalized.startswith(
        (f"{architecture_root}/", f"{root_anchor}/")
    )
    if is_full_path:
        return (normalized,)
    return (f"{architecture_root}/{normalized}",)


@cache
def _regex(pattern: str, scope: bool):
    parts = ["^("]
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            is_deep = i + 1 < len(pattern) and pattern[i + 1] == "*"
            parts.append("(.*)" if is_deep else "([^/]*)")
            i += 2 if is_deep else 1
        elif char == "?":
            parts.append("([^/])")
            i += 1
        else:
            parts.append(re.escape(char))
            i += 1
    parts.append(")(?:/.*)?" if scope else ")")
    return re.compile("".join(parts) + "$")
