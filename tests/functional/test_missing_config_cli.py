from __future__ import annotations

from pathlib import Path

import pytest

from conftest import copy_fixture, run_cli


@pytest.mark.parametrize(
    "command",
    (
        ("architecture", "boundaries"),
        ("architecture", "shape"),
        ("architecture", "map"),
        ("architecture", "pressure"),
        ("architecture", "clusters"),
        ("architecture", "coherence"),
        ("architecture", "health"),
        ("workspace", "health"),
        ("health",),
    ),
)
def test_config_bound_commands_report_missing_config_without_traceback(
    tmp_path: Path,
    command: tuple[str, ...],
) -> None:
    project_root = copy_fixture(tmp_path, "no_config_project")

    result = run_cli(project_root, *command)
    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert "Could not find a configuration file" in output
    assert "Traceback" not in output
