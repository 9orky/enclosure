from __future__ import annotations

from .errors import ScaffoldError
from .scaffold import Scaffold, _ScaffoldInput


class _ScaffoldComposer:
    def compose(
        self,
        scaffold: Scaffold,
        scaffolds: tuple[Scaffold, ...],
    ) -> tuple[Scaffold, ...]:
        scaffolds_by_name = self._scaffolds_by_name(scaffolds)
        return self._included_scaffolds_for(
            scaffold,
            scaffolds_by_name,
            trail=(scaffold.name,),
        ) + (scaffold,)

    def input_specs_for(
        self,
        composed_scaffolds: tuple[Scaffold, ...],
    ) -> tuple[_ScaffoldInput, ...]:
        input_specs: list[_ScaffoldInput] = []
        for scaffold in composed_scaffolds:
            input_specs.extend(scaffold.inputs)
        return tuple(input_specs)

    def _scaffolds_by_name(self, scaffolds: tuple[Scaffold, ...]) -> dict[str, Scaffold]:
        return {scaffold.name: scaffold for scaffold in scaffolds}

    def _included_scaffolds_for(
        self,
        scaffold: Scaffold,
        scaffolds_by_name: dict[str, Scaffold],
        trail: tuple[str, ...],
    ) -> tuple[Scaffold, ...]:
        included_scaffolds: list[Scaffold] = []
        for include_name in scaffold.includes:
            self._assert_no_cycle(include_name, trail)
            included_scaffold = self._included_scaffold(include_name, scaffolds_by_name)
            included_scaffolds.extend(
                self._included_scaffolds_for(
                    included_scaffold,
                    scaffolds_by_name,
                    trail=trail + (include_name,),
                )
            )
            included_scaffolds.append(included_scaffold)
        return tuple(included_scaffolds)

    def _assert_no_cycle(self, include_name: str, trail: tuple[str, ...]) -> None:
        if include_name in trail:
            cycle = " -> ".join(trail + (include_name,))
            raise ScaffoldError(f"Scaffold include cycle: {cycle}")

    def _included_scaffold(
        self,
        include_name: str,
        scaffolds_by_name: dict[str, Scaffold],
    ) -> Scaffold:
        included_scaffold = scaffolds_by_name.get(include_name)
        if included_scaffold is None:
            raise ScaffoldError(f"Scaffold include not found: {include_name}")
        return included_scaffold
