from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from enclosure.shared import architecture_code


@dataclass(frozen=True)
class BenchResult:
    name: str
    seconds: float
    files_found: int
    files_checked: int
    files_excluded: int

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "seconds": self.seconds,
            "files_found": self.files_found,
            "files_checked": self.files_checked,
            "files_excluded": self.files_excluded,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark enclosure's modwire-backed architecture extraction.",
    )
    parser.add_argument("--files", type=int, default=1000)
    parser.add_argument("--ignored-files", type=int, default=1000)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as temporary_directory:
        project_root = Path(temporary_directory)
        _write_project(project_root, args.files, args.ignored_files)
        previous_cwd = Path.cwd()
        os.chdir(project_root)
        try:
            results = [
                _measure("cold", architecture_code.extract_architecture_code),
                _measure("warm", architecture_code.extract_architecture_code),
            ]
            (project_root / "src" / "module_0.py").write_text(
                "VALUE = 2\n",
                encoding="utf-8",
            )
            results.append(
                _measure("in_scope_change", architecture_code.extract_architecture_code)
            )
            (project_root / "outside.py").write_text("VALUE = 1\n", encoding="utf-8")
            results.append(
                _measure(
                    "out_of_scope_change",
                    architecture_code.extract_architecture_code,
                )
            )
        finally:
            os.chdir(previous_cwd)

    print(
        json.dumps(
            {
                "files": args.files,
                "ignored_files": args.ignored_files,
                "results": [result.to_json_dict() for result in results],
            },
            indent=2,
        )
    )
    return 0


def _measure(
    name: str,
    callback: Callable[[], architecture_code.ArchitectureCodeMap],
) -> BenchResult:
    started_at = time.perf_counter()
    code_analysis = callback()
    seconds = time.perf_counter() - started_at
    summary = code_analysis.code_map.extraction_result.summary
    return BenchResult(
        name=name,
        seconds=round(seconds, 6),
        files_found=summary.files_found,
        files_checked=summary.files_checked,
        files_excluded=summary.files_excluded,
    )


def _write_project(project_root: Path, files_count: int, ignored_files_count: int) -> None:
    source_root = project_root / "src"
    ignored_root = project_root / "ignored"
    source_root.mkdir(parents=True)
    ignored_root.mkdir(parents=True)
    (project_root / ".enclosure").mkdir()
    (project_root / ".enclosure" / "enclosure.yaml").write_text(
        _contract_text(),
        encoding="utf-8",
    )

    for index in range(files_count):
        import_line = "import module_0\n" if index else ""
        (source_root / f"module_{index}.py").write_text(
            f"{import_line}VALUE = {index}\n",
            encoding="utf-8",
        )
    for index in range(ignored_files_count):
        (ignored_root / f"generated_{index}.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )


def _contract_text() -> str:
    contract = (
        resources.files("enclosure.resources")
        .joinpath("enclosure.yaml")
        .read_text(encoding="utf-8")
    )
    return contract.replace("root: src/enclosure/features", "root: src")


if __name__ == "__main__":
    raise SystemExit(main())
