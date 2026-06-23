from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_extraction_uses_only_configured_exclusions(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    config_dir = tmp_path / ".enclosure"
    source_dir = tmp_path / "src"
    config_dir.mkdir()
    (source_dir / "build").mkdir(parents=True)
    (source_dir / "dist").mkdir(parents=True)
    (source_dir / "app.py").write_text("def app():\n    return 1\n", encoding="utf-8")
    (source_dir / "build" / "included.py").write_text(
        "def build():\n    return 2\n",
        encoding="utf-8",
    )
    (source_dir / "dist" / "included.py").write_text(
        "def dist():\n    return 3\n",
        encoding="utf-8",
    )
    (config_dir / "enclosure.yaml").write_text(
        """
architecture:
  language: python
  root: src
  exclusions: []
""".lstrip(),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        str(path)
        for path in (
            project_root / "src",
            env.get("PYTHONPATH", ""),
        )
        if path
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; "
                "from enclosure.shared import architecture_code; "
                "code = architecture_code.extract_architecture_code(); "
                "print(json.dumps(sorted(code.code_map.source_ids())))"
            ),
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [
        "app",
        "build/included",
        "dist/included",
    ]
    assert (config_dir / ".cache" / "modwire").is_dir()
