from __future__ import annotations

from . import errors, scaffold


class _ScaffoldComposer:
    def compose(
        self,
        selected_scaffold: scaffold.Scaffold,
        scaffolds: tuple[scaffold.Scaffold, ...],
    ) -> tuple[scaffold.Scaffold, ...]:
        scaffolds_by_name = self._scaffolds_by_name(scaffolds)
        return self._included_scaffolds_for(
            selected_scaffold,
            scaffolds_by_name,
            trail=(selected_scaffold.name,),
        ) + (selected_scaffold,)

    def input_specs_for(
        self,
        composed_scaffolds: tuple[scaffold.Scaffold, ...],
    ) -> tuple[scaffold._ScaffoldInput, ...]:
        input_specs: list[scaffold._ScaffoldInput] = []
        for composed_scaffold in composed_scaffolds:
            input_specs.extend(composed_scaffold.inputs)
        return tuple(input_specs)

    def _scaffolds_by_name(
        self,
        scaffolds: tuple[scaffold.Scaffold, ...],
    ) -> dict[str, scaffold.Scaffold]:
        return {candidate.name: candidate for candidate in scaffolds}

    def _included_scaffolds_for(
        self,
        selected_scaffold: scaffold.Scaffold,
        scaffolds_by_name: dict[str, scaffold.Scaffold],
        trail: tuple[str, ...],
    ) -> tuple[scaffold.Scaffold, ...]:
        included_scaffolds: list[scaffold.Scaffold] = []
        for include_name in selected_scaffold.includes:
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
            raise errors.ScaffoldError(f"Scaffold include cycle: {cycle}")

    def _included_scaffold(
        self,
        include_name: str,
        scaffolds_by_name: dict[str, scaffold.Scaffold],
    ) -> scaffold.Scaffold:
        included_scaffold = scaffolds_by_name.get(include_name)
        if included_scaffold is None:
            raise errors.ScaffoldError(f"Scaffold include not found: {include_name}")
        return included_scaffold
