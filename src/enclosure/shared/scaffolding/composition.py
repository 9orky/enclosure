from __future__ import annotations

from .errors import ScaffoldError
from .scaffold import Scaffold, _ScaffoldInput


def compose_scaffolds(
    scaffold: Scaffold,
    scaffolds: tuple[Scaffold, ...],
) -> tuple[Scaffold, ...]:
    scaffolds_by_name = _scaffolds_by_name(scaffolds)
    return _included_scaffolds_for(
        scaffold,
        scaffolds_by_name,
        trail=(scaffold.name,),
    ) + (scaffold,)


def _scaffolds_by_name(scaffolds: tuple[Scaffold, ...]) -> dict[str, Scaffold]:
    return {scaffold.name: scaffold for scaffold in scaffolds}


def _included_scaffolds_for(
    scaffold: Scaffold,
    scaffolds_by_name: dict[str, Scaffold],
    trail: tuple[str, ...],
) -> tuple[Scaffold, ...]:
    included_scaffolds: list[Scaffold] = []
    for include_name in scaffold.includes:
        if include_name in trail:
            cycle = " -> ".join(trail + (include_name,))
            raise ScaffoldError(f"Scaffold include cycle: {cycle}")
        included_scaffold = scaffolds_by_name.get(include_name)
        if included_scaffold is None:
            raise ScaffoldError(f"Scaffold include not found: {include_name}")
        included_scaffolds.extend(
            _included_scaffolds_for(
                included_scaffold,
                scaffolds_by_name,
                trail=trail + (include_name,),
            )
        )
        included_scaffolds.append(included_scaffold)
    return tuple(included_scaffolds)


def _input_specs_for(composed_scaffolds: tuple[Scaffold, ...]) -> tuple[_ScaffoldInput, ...]:
    input_specs: list[_ScaffoldInput] = []
    for scaffold in composed_scaffolds:
        input_specs.extend(scaffold.inputs)
    return tuple(input_specs)
