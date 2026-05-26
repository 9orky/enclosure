from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_PLAN_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

PLAN_SECTION_HEADINGS = (
    "Problem Or Goal",
    "Target Users Or Callers",
    "Proposed Module Ownership",
    "Public Seam",
    "Private Internals",
    "Expected Layers",
    "Inputs, Outputs, And Data",
    "Dependencies",
    "Recipe Or Scaffold",
    "Verification Checklist",
    "Open Questions",
    "Notes For The Implementing Agent",
)


@dataclass(frozen=True)
class PlanName:
    value: str

    def __post_init__(self) -> None:
        normalized_value = self.value.strip()
        normalized_path = PurePosixPath(normalized_value)
        if (
            not normalized_value
            or normalized_path.is_absolute()
            or len(normalized_path.parts) != 1
            or normalized_value in {".", ".."}
            or ".." in normalized_path.parts
            or not _PLAN_NAME_PATTERN.match(normalized_value)
        ):
            raise ValueError(
                "Plan name must be a kebab-case slug without path separators"
            )
        object.__setattr__(self, "value", normalized_value)

    def document_path(self, plans_root: Path) -> Path:
        return plans_root / f"{self.value}.md"


@dataclass(frozen=True)
class PlanDocument:
    name: PlanName
    project_root: Path
    plans_root: Path
    target_path: Path
    content: str


@dataclass(frozen=True)
class PlanWriteResult:
    document: PlanDocument
    created: bool = False
    overwritten: bool = False
    preserved: bool = False


def render_plan_scaffold(plan_name: PlanName) -> str:
    title = plan_name.value.replace("-", " ").title()
    return f"""# {title}

Status: Draft

## Problem Or Goal

What should change, and why is this worth doing now?


## Target Users Or Callers

Who will use this module or call into its public seam?


## Proposed Module Ownership

Which feature or module owns this responsibility?


## Public Seam

What should other modules be allowed to import or call?


## Private Internals

What helpers, policies, models, or intermediate details should stay private?


## Expected Layers

- Domain:
- Infrastructure:
- Application:
- UI:


## Inputs, Outputs, And Data

What data enters the module, what leaves it, and what must be preserved?


## Dependencies

Which dependencies are allowed, avoided, or uncertain?


## Recipe Or Scaffold

Which `.enclosure/recipes/` recipe or existing module shape should be used?


## Verification Checklist

- [ ] Run relevant unit tests.
- [ ] Run `enclosure architecture boundaries`.
- [ ] Run `enclosure architecture shape`.
- [ ] Run `enclosure architecture health`.


## Open Questions

What still needs a human architecture decision?


## Notes For The Implementing Agent

What should the agent know before editing files?
"""


__all__ = [
    "PLAN_SECTION_HEADINGS",
    "PlanDocument",
    "PlanName",
    "PlanWriteResult",
    "render_plan_scaffold",
]
