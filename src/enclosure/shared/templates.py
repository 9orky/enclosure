from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from . import naming

_TEMPLATE_PATTERN = re.compile(r"{{\s*(?P<expression>[^{}]+?)\s*}}")
_RAW_PATTERN = re.compile(
    r"{%\s*raw\s*%}(?P<value>.*?){%\s*endraw\s*%}",
    re.DOTALL,
)


def render_recipe_template(template: str, context: Mapping[str, Any]) -> str:
    raw_blocks: dict[str, str] = {}

    def stash_raw(match: re.Match[str]) -> str:
        key = f"__enclosure_raw_{len(raw_blocks)}__"
        raw_blocks[key] = match.group("value")
        return key

    protected_template = _RAW_PATTERN.sub(stash_raw, template)

    def replace(match: re.Match[str]) -> str:
        return str(evaluate_expression(match.group("expression"), context))

    rendered = _TEMPLATE_PATTERN.sub(replace, protected_template)
    for key, value in raw_blocks.items():
        rendered = rendered.replace(key, value)
    return rendered


def evaluate_expression(expression: str, context: Mapping[str, Any]) -> Any:
    parts = tuple(part.strip() for part in expression.split("|") if part.strip())
    if not parts:
        raise ValueError("Empty template expression")

    value = lookup_context_value(parts[0], context)
    for filter_name in parts[1:]:
        value = apply_filter(value, filter_name)
    return value


def lookup_context_value(path: str, context: Mapping[str, Any]) -> Any:
    value: Any = context
    for part in path.split("."):
        if isinstance(value, Mapping) and part in value:
            value = value[part]
            continue
        raise ValueError(f"Unknown template variable: {path}")
    return value


def apply_filter(value: Any, filter_name: str) -> str:
    text = str(value)
    if filter_name == "pascal":
        return naming.pascal_case(text)
    if filter_name == "camel":
        return naming.camel_case(text)
    if filter_name == "snake":
        return naming.snake_case(text)
    if filter_name == "kebab":
        return naming.kebab_case(text)
    if filter_name == "lower":
        return text.lower()
    if filter_name == "upper":
        return text.upper()
    raise ValueError(f"Unsupported template filter: {filter_name}")


__all__ = [
    "apply_filter",
    "evaluate_expression",
    "lookup_context_value",
    "render_recipe_template",
]
