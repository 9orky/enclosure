from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from enclosure.shared import naming

from .composition import _ScaffoldComposer
from .errors import ScaffoldError
from .relative_path import _ScaffoldRelativePathNormalizer
from .scaffold import Scaffold, _ScaffoldInput, _ScaffoldInputValueValidator

_VARIABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class _ScaffoldVariableParser:
    def parse(self, values: tuple[str, ...]) -> dict[str, str]:
        variables: dict[str, str] = {}
        for raw_value in values:
            name, value = self._parse_pair(raw_value)
            variables[name] = value
        return variables

    def _parse_pair(self, raw_value: str) -> tuple[str, str]:
        if "=" not in raw_value:
            raise ScaffoldError(f"Scaffold variables must use key=value syntax: {raw_value}")
        name, value = raw_value.split("=", 1)
        return self._validate_name(name, raw_value), value

    def _validate_name(self, name: str, raw_value: str) -> str:
        normalized_name = name.strip()
        if not normalized_name:
            raise ScaffoldError("Scaffold variable names must not be empty")
        if not _VARIABLE_NAME_PATTERN.match(normalized_name):
            raise ScaffoldError(f"Invalid scaffold variable name in: {raw_value}")
        return normalized_name


class _ScaffoldContextFactory:
    def __init__(self) -> None:
        self._composer = _ScaffoldComposer()
        self._input_validator = _ScaffoldInputValueValidator()
        self._paths = _ScaffoldRelativePathNormalizer()

    def resolve(
        self,
        composed_scaffolds: tuple[Scaffold, ...],
        target_relative_path: Path,
        variables: dict[str, str],
    ) -> dict[str, Any]:
        raw_variables = dict(variables)
        defaults = self._target_defaults_for(target_relative_path)
        context: dict[str, Any] = {
            "target": self._target_context_for(target_relative_path),
        }
        context.update(
            self._resolve_inputs(
                self._composer.input_specs_for(composed_scaffolds),
                raw_variables,
                defaults,
            )
        )
        for name, value in raw_variables.items():
            if name not in context:
                context[name] = self._variable_context_for(value)
        return context

    def _resolve_inputs(
        self,
        input_specs: tuple[_ScaffoldInput, ...],
        raw_variables: dict[str, str],
        defaults: dict[str, str],
    ) -> dict[str, Any]:
        return {
            input_spec.name: self._variable_context_for(
                self._resolve_input(input_spec, raw_variables, defaults)
            )
            for input_spec in input_specs
        }

    def _resolve_input(
        self,
        input_spec: _ScaffoldInput,
        raw_variables: dict[str, str],
        defaults: dict[str, str],
    ) -> object:
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
        return self._input_validator.validate(input_spec, value)

    def _variable_context_for(self, value: object) -> object:
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

    def _target_context_for(self, relative_path: Path) -> dict[str, Any]:
        target_path = self._paths.normalize(relative_path, "Target path")
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

    def _target_defaults_for(self, relative_path: Path) -> dict[str, str]:
        target = self._target_context_for(relative_path)
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
