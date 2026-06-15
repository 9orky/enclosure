from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class RuleTagSelection(BaseModel):
    model_config = ConfigDict(frozen=True)

    tag: str
    reason: str


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
    paths: tuple[Path, ...],
    task: str,
    project_root: Path,
    architecture_root: str,
) -> tuple[RuleTagSelection, ...]:
    selections: list[RuleTagSelection] = []
    for path in paths:
        selections.extend(
            _path_tag_selections(
                path,
                project_root=project_root,
                architecture_root=architecture_root,
            )
        )
    selections.extend(_task_tag_selections(task))
    return _unique_selections(tuple(selections))


def selected_tags(selections: tuple[RuleTagSelection, ...]) -> tuple[str, ...]:
    return tuple(selection.tag for selection in _unique_selections(selections))


def _path_tag_selections(
    path: Path,
    *,
    project_root: Path,
    architecture_root: str,
) -> tuple[RuleTagSelection, ...]:
    relative_path = _relative_project_path(path, project_root)
    parts = relative_path.parts
    if not parts:
        return ()

    selections: list[RuleTagSelection] = []
    label = relative_path.as_posix()
    if parts[0] == ".enclosure":
        selections.extend(_enclosure_path_selections(parts, label))
    elif parts[0] in {"test", "tests"}:
        selections.append(
            RuleTagSelection(
                tag="verification",
                reason=f"`{label}` is a test path.",
            )
        )
    elif _is_architecture_path(relative_path, architecture_root):
        selections.extend(_architecture_path_selections(relative_path, architecture_root))
    return tuple(selections)


def _enclosure_path_selections(
    parts: tuple[str, ...],
    label: str,
) -> tuple[RuleTagSelection, ...]:
    if len(parts) >= 2 and parts[1] == "rules":
        return (
            RuleTagSelection(
                tag="rules",
                reason=f"`{label}` is a workspace rule document path.",
            ),
        )
    if len(parts) >= 2 and parts[1].startswith("enclosure."):
        return (
            RuleTagSelection(
                tag="architecture",
                reason=f"`{label}` is the architecture contract.",
            ),
        )
    if len(parts) >= 2 and parts[1] == "recipes":
        return (
            RuleTagSelection(
                tag="execution",
                reason=f"`{label}` is a workspace recipe path.",
            ),
        )
    return ()


def _architecture_path_selections(
    path: Path,
    architecture_root: str,
) -> tuple[RuleTagSelection, ...]:
    label = path.as_posix()
    root = Path(architecture_root)
    try:
        architecture_relative_path = path.relative_to(root)
    except ValueError:
        architecture_relative_path = path

    selections = [
        RuleTagSelection(
            tag="structure",
            reason=f"`{label}` is under architecture.root `{architecture_root}`.",
        )
    ]
    if path.suffix == ".py":
        selections.append(
            RuleTagSelection(
                tag="python",
                reason=f"`{label}` is a Python source file.",
            )
        )
    if "__init__.py" in architecture_relative_path.parts:
        selections.append(
            RuleTagSelection(
                tag="module",
                reason=f"`{label}` touches a package seam.",
            )
        )
    layer_names = {"domain", "infrastructure", "application", "ui"}
    if any(part in layer_names for part in architecture_relative_path.parts) or (
        path.suffix == ".py" and path.stem in layer_names
    ):
        selections.append(
            RuleTagSelection(
                tag="layers",
                reason=f"`{label}` includes a known feature-layer segment.",
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
        "refactor": ("change", "refactoring"),
        "refactoring": ("change", "refactoring"),
        "rules": ("rules",),
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


def _relative_project_path(path: Path, project_root: Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        try:
            return candidate.resolve(strict=False).relative_to(project_root)
        except ValueError:
            return candidate
    return candidate


def _is_architecture_path(path: Path, architecture_root: str) -> bool:
    try:
        path.relative_to(Path(architecture_root))
        return True
    except ValueError:
        return False


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
    "RuleTagSelection",
    "explicit_rule_tag_selections",
    "infer_rule_tag_selections",
    "selected_tags",
]
