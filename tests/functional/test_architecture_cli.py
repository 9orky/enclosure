from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_clean_probe_project_passes_architecture_cli_commands(tmp_path: Path) -> None:
    project_root = _copy_fixture(tmp_path, "clean_architecture")

    boundaries = _run_cli(project_root, "architecture", "boundaries")
    shape = _run_cli(project_root, "architecture", "shape")
    architecture_map = _run_cli(
        project_root,
        "architecture",
        "map",
        "--top",
        "-1",
    )

    assert boundaries.returncode == 0, boundaries.stderr
    assert "Architecture Boundaries Passed! No violations found." in boundaries.stdout
    assert shape.returncode == 0, shape.stderr
    assert "Architecture Shape Passed! No violations found." in shape.stdout
    assert architecture_map.returncode == 0, architecture_map.stderr
    assert "- Modules found: 1" in architecture_map.stdout
    assert "- Cross-module dependencies: 0" in architecture_map.stdout
    assert "- Unknown files: 0" in architecture_map.stdout
    assert "- sales/report: 3 file(s) (application 1, domain 1)" in architecture_map.stdout


def test_boundary_probe_project_reports_blocked_edge_and_cycle(
    tmp_path: Path,
) -> None:
    project_root = _copy_fixture(tmp_path, "violating_architecture")

    result = _run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 1
    assert result.stderr == ""
    assert "=== Architectural Violations Detected ===" in result.stdout
    assert (
        "- sales/report/domain -> [sales/report/application] "
        "blocked by */*/domain -> */*/application"
    ) in result.stdout
    assert (
        "- sales/report/application -> sales/report/domain -> "
        "[sales/report/application]  no-cycles"
    ) in result.stdout


def test_shape_probe_project_reports_function_limit_violation(
    tmp_path: Path,
) -> None:
    project_root = _copy_fixture(tmp_path, "violating_architecture")

    result = _run_cli(project_root, "architecture", "shape")

    assert result.returncode == 1
    assert result.stderr == ""
    assert "Shape Violations:" in result.stdout
    assert "- sales/report/domain max_functions_per_file actual 2, limit 1" in result.stdout


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    fixture_root = FIXTURE_ROOT / name
    project_root = tmp_path / name
    shutil.copytree(fixture_root, project_root)
    return project_root


def _run_cli(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "enclosure", *args],
        cwd=project_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
