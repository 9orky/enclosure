from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def copy_fixture(tmp_path: Path, name: str) -> Path:
    fixture_root = FIXTURE_ROOT / name
    project_root = tmp_path / name
    shutil.copytree(fixture_root, project_root)
    return project_root


def run_cli(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
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
