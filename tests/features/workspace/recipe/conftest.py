from __future__ import annotations

from collections.abc import Callable

import pytest

from enclosure.features.workspace.recipe import application
from enclosure.shared.config.facade import SettingsFacade
from enclosure.shared.config.manifest import Manifest
from tests.support.projects import FixtureProject


@pytest.fixture
def use_project(monkeypatch: pytest.MonkeyPatch) -> Callable[[FixtureProject], None]:
    def apply(project: FixtureProject) -> None:
        monkeypatch.setattr(
            application,
            "settings",
            SettingsFacade(Manifest(project.root)),
        )

    return apply
