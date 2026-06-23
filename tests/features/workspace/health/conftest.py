from __future__ import annotations

from collections.abc import Callable

import pytest

from enclosure.features.workspace.health import application as health_application
from enclosure.features.workspace.recipe import application as recipe_application
from enclosure.features.workspace.rules import application as rules_application
from enclosure.shared.config.facade import SettingsFacade
from enclosure.shared.config.manifest import Manifest
from tests.support.projects import FixtureProject


@pytest.fixture
def use_project(monkeypatch: pytest.MonkeyPatch) -> Callable[[FixtureProject], None]:
    def apply(project: FixtureProject) -> None:
        project_settings = SettingsFacade(Manifest(project.root))
        monkeypatch.setattr(health_application, "settings", project_settings)
        monkeypatch.setattr(recipe_application, "settings", project_settings)
        monkeypatch.setattr(rules_application, "settings", project_settings)

    return apply
