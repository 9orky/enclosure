from __future__ import annotations

import re


def words(value: str) -> tuple[str, ...]:
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return tuple(part for part in re.split(r"[^A-Za-z0-9]+", expanded) if part)


def pascal_case(value: str) -> str:
    return "".join(part[:1].upper() + part[1:].lower() for part in words(value))


def camel_case(value: str) -> str:
    pascal = pascal_case(value)
    return pascal[:1].lower() + pascal[1:]


def snake_case(value: str) -> str:
    return "_".join(part.lower() for part in words(value))


def kebab_case(value: str) -> str:
    return "-".join(part.lower() for part in words(value))

