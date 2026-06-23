from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import pytest

from enclosure.features.workspace.sync import application
from enclosure.shared.config import settings
from tests.support.projects import FixtureProject


def _metadata(project: FixtureProject) -> SimpleNamespace:
    target_dir = project.root / ".enclosure"
    rules_dir = target_dir / "rules"
    return SimpleNamespace(
        project_root=project.root,
        target_dir=target_dir,
        canonical_config_path=target_dir / "enclosure.yaml",
        rules_dir=rules_dir,
        local_rules_dir=rules_dir / "local",
        plans_dir=target_dir / "plans",
        recipes_dir=target_dir / "recipes",
        bootstrap_instruction_path=project.root / ".github" / "copilot-instructions.md",
        agent_instruction_path=project.root / "AGENTS.md",
    )


@pytest.fixture
def use_project(monkeypatch: pytest.MonkeyPatch) -> Callable[[FixtureProject], None]:
    def apply(project: FixtureProject) -> None:
        monkeypatch.setattr(
            application,
            "settings",
            SimpleNamespace(
                metadata=_metadata(project),
                dump_manifest=settings.dump_manifest,
            ),
        )

    return apply
