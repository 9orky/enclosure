from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


FIXTURE_PROJECTS_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "projects"


@dataclass(frozen=True)
class FixtureProject:
    name: str
    root: Path

    @property
    def enclosure_dir(self) -> Path:
        return self.root / ".enclosure"

    @property
    def config_path(self) -> Path:
        return self.enclosure_dir / "enclosure.yaml"

    @property
    def rules_dir(self) -> Path:
        return self.enclosure_dir / "rules"

    @property
    def local_rules_dir(self) -> Path:
        return self.rules_dir / "local"

    @property
    def shared_rules_dir(self) -> Path:
        return self.rules_dir / "shared"

    @property
    def recipes_dir(self) -> Path:
        return self.enclosure_dir / "recipes"

    @property
    def copilot_instructions_path(self) -> Path:
        return self.root / ".github" / "copilot-instructions.md"

    @property
    def agent_instructions_path(self) -> Path:
        return self.root / "AGENTS.md"

    def read_text(self, relative_path: str) -> str:
        return self.root.joinpath(relative_path).read_text(encoding="utf-8")


def fixture_project_names() -> tuple[str, ...]:
    if not FIXTURE_PROJECTS_ROOT.is_dir():
        return ()
    return tuple(
        sorted(
            child.name
            for child in FIXTURE_PROJECTS_ROOT.iterdir()
            if child.is_dir() and not child.name.startswith(".")
        )
    )


def copy_fixture_project(name: str, destination_root: Path) -> FixtureProject:
    source = FIXTURE_PROJECTS_ROOT / name
    if not source.is_dir():
        available = ", ".join(fixture_project_names())
        raise LookupError(f"Unknown fixture project: {name}. Available: {available}")

    destination = destination_root / name
    shutil.copytree(source, destination)
    return FixtureProject(name=name, root=destination)
