from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from enclosure.shared import layout as project_layout
from tests.support.projects import FixtureProject, copy_fixture_project


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def fixture_project(tmp_path: Path) -> Callable[[str], FixtureProject]:
    def copy(name: str) -> FixtureProject:
        return copy_fixture_project(name, tmp_path)

    return copy


@pytest.fixture
def use_project(monkeypatch: pytest.MonkeyPatch) -> Callable[[FixtureProject], None]:
    def apply(project: FixtureProject) -> None:
        monkeypatch.setattr(
            project_layout,
            "current_project_root",
            lambda: project.root,
        )

    return apply
