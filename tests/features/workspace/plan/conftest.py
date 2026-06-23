from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import pytest

from enclosure.features.workspace.plan import application
from enclosure.shared import layout as project_layout
from tests.support.projects import FixtureProject


class ProjectSettings:
    def __init__(self, project: FixtureProject) -> None:
        target_dir = project.root / ".enclosure"
        self.metadata = SimpleNamespace(
            project_root=project.root,
            target_dir=target_dir,
            plans_dir=target_dir / "plans",
        )


@pytest.fixture
def use_project(monkeypatch: pytest.MonkeyPatch) -> Callable[[FixtureProject], None]:
    def apply(project: FixtureProject) -> None:
        monkeypatch.setattr(application, "settings", ProjectSettings(project))
        monkeypatch.setattr(project_layout, "current_project_root", lambda: project.root)

    return apply
