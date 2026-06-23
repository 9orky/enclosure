from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from enclosure.shared.scaffolding import Scaffold, catalog_policy
from .. import infrastructure


@dataclass(frozen=True)
class _ComposedLadder:
    family: str = ""
    rung: str = ""
    slots: tuple[Any, ...] = ()
    declared: bool = False

    def is_declared(self) -> bool:
        return self.declared


def recipe_for_role(
    role_name: str,
    recipes_by_name: Mapping[str, Scaffold],
) -> Scaffold | None:
    return catalog_policy.scaffold_for_role(
        role_name,
        recipes_by_name,
        composed_name="composed-role",
        composed_description="Composed recipe role",
        composed_ladder=_ComposedLadder(
            family="composed",
            rung=role_name,
            declared=True,
        ),
    )


def composed_recipe_inputs(
    recipe: Scaffold,
    recipes_by_name: Mapping[str, Scaffold],
) -> tuple[Any, ...]:
    composed_recipes = infrastructure.compose_recipes(
        recipe,
        tuple(recipes_by_name.values()),
    )
    return tuple(input_spec for scaffold in composed_recipes for input_spec in scaffold.inputs)


def composed_ladder_for(
    recipe: Scaffold,
    recipes_by_name: Mapping[str, Scaffold],
) -> Any:
    slots_by_name: dict[str, Any] = {}
    for composed_recipe in infrastructure.compose_recipes(
        recipe,
        tuple(recipes_by_name.values()),
    ):
        for slot in composed_recipe.ladder.slots:
            slots_by_name[slot_name(slot)] = slot
    return _ComposedLadder(
        family=recipe.ladder.family,
        rung=recipe.ladder.rung,
        slots=tuple(slots_by_name.values()),
        declared=recipe.ladder.is_declared(),
    )


def slot_name(slot: Any) -> str:
    name = slot.name
    return name.value if hasattr(name, "value") else str(name)


def slot_state(slot: Any) -> str:
    state = slot.state
    return state.value if hasattr(state, "value") else str(state)


__all__ = [
    "composed_ladder_for",
    "composed_recipe_inputs",
    "recipe_for_role",
    "slot_name",
    "slot_state",
]
