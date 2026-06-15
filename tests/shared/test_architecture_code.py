from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from modwire import CodeMap, ExtractionCache, SourceRoots
from modwire.definitions import SourceFile
from modwire.extraction import ExtractionResult, ExtractionSummary
from modwire.graph import build_dependency_graph

from enclosure.features.architecture.config import domain
from enclosure.shared import architecture_code


class ArchitectureCodeTest(unittest.TestCase):
    def test_extract_architecture_code_delegates_cached_extraction_to_modwire(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            extract_code = Mock(return_value=_fake_code_map())

            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()

            extract_code.assert_called_once()
            kwargs = extract_code.call_args.kwargs
            self.assertEqual("python", kwargs["language"])
            self.assertEqual(project_root, kwargs["sources_root"])
            self.assertEqual((), kwargs["exclusions"])
            self.assertEqual(
                SourceRoots(workspace_root=project_root),
                kwargs["source_roots"],
            )
            self.assertEqual(
                ExtractionCache(
                    root=project_root / ".enclosure" / ".cache" / "modwire",
                    max_entries=3,
                ),
                kwargs["cache"],
            )

    def test_configured_architecture_root_uses_workspace_cache_and_default_exclusions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            source_root = project_root / "src"
            source_root.mkdir()
            config = SimpleNamespace(
                language="python",
                exclusions=["src/generated/**"],
                architecture_root="src",
            )
            extract_code = Mock(return_value=_fake_code_map())

            with _architecture_config(project_root, configs=(config,)), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                code_analysis = architecture_code.extract_architecture_code()

            kwargs = extract_code.call_args.kwargs
            self.assertEqual(source_root.resolve(), kwargs["sources_root"])
            self.assertEqual(
                (
                    "src/generated/**",
                    *architecture_code.DEFAULT_ARCHITECTURE_EXCLUSIONS,
                ),
                kwargs["exclusions"],
            )
            self.assertEqual(
                SourceRoots(workspace_root=project_root),
                kwargs["source_roots"],
            )
            self.assertEqual("", code_analysis.matching_config.architecture_root)

def _project_root(temporary_directory: str) -> Path:
    project_root = Path(temporary_directory)
    (project_root / ".enclosure").mkdir()
    (project_root / ".enclosure" / "enclosure.yaml").write_text(
        "architecture: {}\n",
        encoding="utf-8",
    )
    (project_root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    return project_root


def _architecture_config(
    project_root: Path,
    *,
    configs: tuple[SimpleNamespace, ...] | None = None,
):
    active_configs = configs or (SimpleNamespace(language="python", exclusions=[]),)
    return _ArchitectureConfigPatch(project_root, active_configs)


class _ArchitectureConfigPatch:
    def __init__(
        self,
        project_root: Path,
        configs: tuple[SimpleNamespace, ...],
    ) -> None:
        self.project_root = project_root
        self.configs = configs
        self._patches = []

    def __enter__(self):
        configs = list(self.configs)

        def validate_mapping(*args, **kwargs):
            if len(configs) > 1:
                return configs.pop(0)
            return configs[0]

        self._patches = [
            patch.object(
                architecture_code.config,
                "load_project_mapping",
                return_value=(
                    self.project_root,
                    self.project_root / ".enclosure" / "enclosure.yaml",
                    {},
                ),
            ),
            patch.object(
                domain.ArchitectureConfig,
                "validate_mapping",
                side_effect=validate_mapping,
            ),
        ]
        for active_patch in self._patches:
            active_patch.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for active_patch in reversed(self._patches):
            active_patch.stop()


def _fake_code_map() -> CodeMap:
    files = {
        "app": SourceFile(
            imports=[],
            classes=[],
            functions=[],
            line_count=1,
            code_line_count=1,
            public_symbol_count=0,
        )
    }
    return CodeMap(
        graph=build_dependency_graph(files),
        extraction_result=ExtractionResult(
            files=files,
            summary=ExtractionSummary(
                files_found=1,
                files_checked=1,
                files_excluded=0,
            ),
        ),
        runtime_command="python",
    )


if __name__ == "__main__":
    unittest.main()
