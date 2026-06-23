from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RuleTagSelection(BaseModel):
    model_config = ConfigDict(frozen=True)

    tag: str
    reason: str


class RulePathFacts(BaseModel):
    model_config = ConfigDict(frozen=True)

    relative_path: str
    is_workspace_rules_path: bool = False
    is_workspace_recipe_path: bool = False
    is_architecture_contract_path: bool = False
    is_test_path: bool = False
    is_architecture_path: bool = False
    is_configured_source_file: bool = False
    matches_module: bool = False
    matches_layer: bool = False


def explicit_rule_tag_selections(tags: tuple[str, ...]) -> tuple[RuleTagSelection, ...]:
    return tuple(
        RuleTagSelection(
            tag=tag,
            reason="Explicit --tag selection.",
        )
        for tag in _normalize_tags(tags)
    )


def infer_rule_tag_selections(
    *,
    path_facts: tuple[RulePathFacts, ...],
    task: str,
) -> tuple[RuleTagSelection, ...]:
    selections: list[RuleTagSelection] = []
    for facts in path_facts:
        selections.extend(_path_tag_selections(facts))
    selections.extend(_task_tag_selections(task))
    return _unique_selections(tuple(selections))


def selected_tags(selections: tuple[RuleTagSelection, ...]) -> tuple[str, ...]:
    return tuple(selection.tag for selection in _unique_selections(selections))


def _path_tag_selections(
    facts: RulePathFacts,
) -> tuple[RuleTagSelection, ...]:
    label = facts.relative_path.strip()
    if not label:
        return ()

    selections: list[RuleTagSelection] = []
    if facts.is_workspace_rules_path:
        selections.append(
            RuleTagSelection(
                tag="rules",
                reason=f"`{label}` is a workspace rule document path.",
            )
        )
    if facts.is_architecture_contract_path:
        selections.append(
            RuleTagSelection(
                tag="architecture",
                reason=f"`{label}` is the architecture contract.",
            )
        )
    if facts.is_workspace_recipe_path:
        selections.append(
            RuleTagSelection(
                tag="execution",
                reason=f"`{label}` is a workspace recipe path.",
            )
        )
    if facts.is_test_path:
        selections.append(
            RuleTagSelection(
                tag="verification",
                reason=f"`{label}` is a test path.",
            )
        )
    if facts.is_architecture_path:
        selections.append(
            RuleTagSelection(
                tag="structure",
                reason=f"`{label}` is under architecture.root.",
            )
        )
    if facts.matches_module:
        selections.append(
            RuleTagSelection(
                tag="module",
                reason=f"`{label}` matches a configured module or public seam tag.",
            )
        )
    if facts.matches_layer:
        selections.append(
            RuleTagSelection(
                tag="layers",
                reason=f"`{label}` matches a configured architecture layer tag.",
            )
        )
    return tuple(selections)


def _task_tag_selections(task: str) -> tuple[RuleTagSelection, ...]:
    normalized_task = task.strip().lower().replace("_", "-")
    if not normalized_task:
        return ()
    tags_by_task = {
        "architecture": ("architecture",),
        "boundaries": ("architecture", "boundaries"),
        "calibration": ("execution", "calibration"),
        "change": ("change",),
        "execution": ("execution",),
        "implementation": ("execution",),
        "create module": ("module-start",),
        "module-start": ("module-start",),
        "new module": ("module-start",),
        "refactor": ("change", "refactoring"),
        "refactor feature module": ("module-start",),
        "refactor module": ("module-start",),
        "refactoring": ("change", "refactoring"),
        "rules": ("rules",),
        "start coding module": ("module-start",),
        "start module": ("module-start",),
        "structure": ("structure",),
        "test": ("verification", "testing"),
        "testing": ("verification", "testing"),
        "verification": ("verification",),
    }
    tags = tags_by_task.get(normalized_task, (normalized_task,))
    return tuple(
        RuleTagSelection(
            tag=tag,
            reason=f"Task category `{task}` maps to `{tag}`.",
        )
        for tag in tags
    )


def _unique_selections(
    selections: tuple[RuleTagSelection, ...],
) -> tuple[RuleTagSelection, ...]:
    unique: list[RuleTagSelection] = []
    seen: set[str] = set()
    for selection in selections:
        normalized_tag = selection.tag.strip().lower()
        if not normalized_tag or normalized_tag in seen:
            continue
        seen.add(normalized_tag)
        unique.append(
            RuleTagSelection(
                tag=normalized_tag,
                reason=selection.reason,
            )
        )
    return tuple(unique)


def _normalize_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        selection.tag
        for selection in _unique_selections(
            tuple(RuleTagSelection(tag=tag, reason="") for tag in tags)
        )
    )


__all__ = [
    "RulePathFacts",
    "RuleTagSelection",
    "explicit_rule_tag_selections",
    "infer_rule_tag_selections",
    "selected_tags",
]
