from __future__ import annotations

import shutil

import pytest

from enclosure.__main__ import app


def test_architecture_health_supports_three_verbosity_levels(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

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
    use_project,
    cli_runner,
    language: str,
    runtime: str,
) -> None:
    if shutil.which(runtime) is None:
        pytest.skip(f"{runtime} runtime is not available")
    project = fixture_project(f"minimal-{language}")
    use_project(project)

    sync = cli_runner.invoke(app, ["workspace", "sync", "init"])
    result = cli_runner.invoke(app, ["architecture", "health", "--v"])

    assert sync.exit_code == 0, sync.output
    assert "Architecture Health (summary):" in result.output
    assert f"Language: {language}" in result.output
    assert "Traceback" not in result.output
