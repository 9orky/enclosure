from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import pytest
import yaml

from enclosure.features.workspace.rules import application
from tests.support.projects import FixtureProject


class ConfigNode(SimpleNamespace):
    @property
    def architecture_root(self) -> str:
        return getattr(self, "root", "")

    @property
    def rules(self) -> object:
        if "rules" in self.__dict__:
            return self.__dict__["rules"]
        return getattr(self, "boundaries", SimpleNamespace())

    @property
    def excluded_patterns(self) -> tuple[str, ...]:
        return (
            *tuple(getattr(self, "except_", ())),
            *tuple(getattr(self, "exclude", ())),
        )


class ProjectSettings:
    def __init__(self, project: FixtureProject) -> None:
        self._project = project
        target_dir = project.root / ".enclosure"
        self.metadata = SimpleNamespace(
            project_root=project.root,
            rules_dir=target_dir / "rules",
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
                ("except_" if key == "except" else key): _config_object(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, list):
        return tuple(_config_object(item) for item in value)
    return value


@pytest.fixture
def use_project(monkeypatch: pytest.MonkeyPatch) -> Callable[[FixtureProject], None]:
    def apply(project: FixtureProject) -> None:
        monkeypatch.setattr(
            application,
            "settings",
            ProjectSettings(project),
        )

    return apply
