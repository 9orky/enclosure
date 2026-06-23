from __future__ import annotations

from pathlib import Path
from typing import Any

from enclosure.shared import naming

from .composition import _input_specs_for
from .errors import ScaffoldError
from .relative_path import _relative_path_value
from .scaffold import Scaffold, _ScaffoldInput, _validate_input_value


def parse_variables(values: tuple[str, ...]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for raw_value in values:
        if "=" not in raw_value:
            raise ScaffoldError(f"Scaffold variables must use key=value syntax: {raw_value}")
        name, value = raw_value.split("=", 1)
        normalized_name = name.strip()
        if not normalized_name:
            raise ScaffoldError("Scaffold variable names must not be empty")
        variables[normalized_name] = value
    return variables


def resolve_context(
    composed_scaffolds: tuple[Scaffold, ...],
    target_relative_path: Path,
    variables: dict[str, str],
) -> dict[str, Any]:
    raw_variables = dict(variables)
    defaults = _target_defaults_for(target_relative_path)
    context: dict[str, Any] = {
        "target": _target_context_for(target_relative_path),
    }
    context.update(_resolve_inputs(_input_specs_for(composed_scaffolds), raw_variables, defaults))
    for name, value in raw_variables.items():
        if name not in context:
            context[name] = _variable_context_for(value)
    return context


def _resolve_inputs(
    input_specs: tuple[_ScaffoldInput, ...],
    raw_variables: dict[str, str],
    defaults: dict[str, str],
) -> dict[str, Any]:
    return {
        input_spec.name: _variable_context_for(
            _resolve_input(input_spec, raw_variables, defaults)
        )
        for input_spec in input_specs
    }


def _resolve_input(
    input_spec: _ScaffoldInput,
    raw_variables: dict[str, str],
    defaults: dict[str, str],
) -> Any:
    if input_spec.name in raw_variables:
        value = raw_variables[input_spec.name]
    elif input_spec.default_from and input_spec.default_from in defaults:
        value = defaults[input_spec.default_from]
    elif input_spec.default:
        value = input_spec.default
    elif input_spec.required:
        raise ScaffoldError(f"Missing required scaffold variable: {input_spec.name}")
    else:
        value = ""
    return _validate_input_value(input_spec, value)


def _variable_context_for(value: Any) -> Any:
    if isinstance(value, tuple):
        return value

    text = str(value)
    return {
        "value": text,
        "class": naming.pascal_case(text),
        "pascal": naming.pascal_case(text),
        "camel": naming.camel_case(text),
        "variable": naming.camel_case(text),
        "snake": naming.snake_case(text),
        "kebab": naming.kebab_case(text),
        "slug": naming.kebab_case(text),
        "upper": text.upper(),
        "lower": text.lower(),
        "name": text,
    }


def _target_context_for(relative_path: Path) -> dict[str, Any]:
    target_path = _relative_path_value(relative_path)
    text = target_path.as_posix()
    name = target_path.name
    return {
        "path": text,
        "name": name,
        "class": naming.pascal_case(name),
        "pascal": naming.pascal_case(name),
        "camel": naming.camel_case(name),
        "variable": naming.camel_case(name),
        "snake": naming.snake_case(name),
        "kebab": naming.kebab_case(name),
        "slug": naming.kebab_case(name),
        "parts": target_path.parts,
        "parent": target_path.parent.as_posix()
        if target_path.parent != Path(".")
        else "",
    }


def _target_defaults_for(relative_path: Path) -> dict[str, str]:
    target = _target_context_for(relative_path)
    return {
        "target_path": target["path"],
        "target_name": target["name"],
        "target_class": target["class"],
        "target_pascal": target["pascal"],
        "target_camel": target["camel"],
        "target_variable": target["variable"],
        "target_snake": target["snake"],
        "target_kebab": target["kebab"],
        "target_slug": target["slug"],
        "target_parent": target["parent"],
    }
