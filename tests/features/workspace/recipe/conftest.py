from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import pytest
import yaml

from enclosure.features.workspace.recipe import application
from enclosure.features.workspace.recipe.ui import cli
from enclosure.shared import layout as project_layout
from tests.support.projects import FixtureProject


class ConfigNode(SimpleNamespace):
    pass


class ProjectSettings:
    def __init__(self, project: FixtureProject) -> None:
        self._project = project
        self.metadata = SimpleNamespace(
            project_root=project.root,
            recipes_dir=project.recipes_dir,
        )

    def query(self, path: str) -> object:
        value: object = yaml.safe_load(
            self._project.config_path.read_text(encoding="utf-8")
        )
        for part in tuple(part.strip() for part in path.split(".") if part.strip()):
            value = value[part]
        return _config_object(value)


def _config_object(value: object) -> object:
    if isinstance(value, dict):
        return ConfigNode(
            **{
                key: item if key == "roles_map" else _config_object(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, list):
        return tuple(_config_object(item) for item in value)
    return value


@pytest.fixture
def use_project(monkeypatch: pytest.MonkeyPatch) -> Callable[[FixtureProject], None]:
    def apply(project: FixtureProject) -> None:
        project_settings = ProjectSettings(project)
        monkeypatch.setattr(application, "settings", project_settings)
        monkeypatch.setattr(cli, "settings", project_settings)
        monkeypatch.setattr(project_layout, "current_project_root", lambda: project.root)

    return apply
