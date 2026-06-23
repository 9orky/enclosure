from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_workspace_recipe_check_cli_succeeds() -> None:
    project_root = Path(__file__).resolve().parents[4]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "enclosure",
            "workspace",
            "recipe",
            "--check",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Recipe check passed." in result.stdout
