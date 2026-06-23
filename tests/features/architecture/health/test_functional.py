from __future__ import annotations

import shutil

import pytest

from enclosure.__main__ import app
from tests.features.architecture.support import use_architecture_settings
from tests.features.architecture.support import write_architecture_config


def test_architecture_health_supports_three_verbosity_levels(
    fixture_project,
    use_project,
    monkeypatch,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    use_architecture_settings(monkeypatch, project.root)

    summary = cli_runner.invoke(app, ["architecture", "health", "--v"])
    standard = cli_runner.invoke(app, ["architecture", "health", "--vv"])
    detailed = cli_runner.invoke(app, ["architecture", "health", "--vvv"])

    assert summary.exit_code == 0, summary.output
    assert standard.exit_code == 0, standard.output
    assert detailed.exit_code == 0, detailed.output
    assert "Architecture Health (summary):" in summary.output
    assert "\nFindings:" not in summary.output
    assert "Architecture Health:" in standard.output
    assert "\nFindings:" in standard.output
    assert "Architecture Health (detailed):" in detailed.output
    assert "Report:" in detailed.output


@pytest.mark.parametrize(
    ("language", "runtime"),
    (("typescript", "node"), ("php", "php")),
)
def test_architecture_health_runs_for_non_python_language_fixtures(
    fixture_project,
    monkeypatch,
    cli_runner,
    language: str,
    runtime: str,
) -> None:
    if shutil.which(runtime) is None:
        pytest.skip(f"{runtime} runtime is not available")
    project = fixture_project(f"minimal-{language}")
    write_architecture_config(project.root, language)
    use_architecture_settings(monkeypatch, project.root)
    result = cli_runner.invoke(app, ["architecture", "health", "--v"])

    assert "Architecture Health (summary):" in result.output
    assert f"Language: {language}" in result.output
    assert "Traceback" not in result.output
