from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from modwire.definitions import SourceFile, SourceImport
from modwire.extraction import CodeMap, ExtractionResult, ExtractionSummary
from modwire.graph import build_dependency_graph

from enclosure.shared import architecture_code, architecture_code_cache


class ArchitectureCodeCacheTest(unittest.TestCase):
    def test_cache_miss_extracts_and_writes_cache_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            extract_code = _extract_code_mock(_fake_code_map())

            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()

            extract_code.assert_called_once_with("python", project_root, ())
            self.assertEqual(1, len(_cache_files(project_root)))
            self.assertTrue((project_root / ".enclosure" / ".cache").is_dir())

    def test_cache_hit_reuses_extraction_and_rebuilds_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            extract_code = _extract_code_mock(_fake_code_map())

            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                cached = architecture_code.extract_architecture_code()

            extract_code.assert_called_once()
            outgoing = cached.code_map.graph.outgoing("app")
            self.assertEqual(1, len(outgoing))
            self.assertEqual("dep", outgoing[0].to_id)

    def test_modified_source_file_invalidates_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            extract_code = _extract_code_mock(_fake_code_map())

            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                (project_root / "app.py").write_text("import dep\nVALUE = 1\n")
                architecture_code.extract_architecture_code()

            self.assertEqual(2, extract_code.call_count)

    def test_added_and_deleted_source_files_invalidate_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            extract_code = _extract_code_mock(_fake_code_map())

            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                (project_root / "extra.py").write_text("VALUE = 1\n")
                architecture_code.extract_architecture_code()
                (project_root / "extra.py").unlink()
                architecture_code.extract_architecture_code()

            self.assertEqual(3, extract_code.call_count)

    def test_changing_exclusions_uses_different_cache_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            extract_code = _extract_code_mock(_fake_code_map())
            configs = (
                SimpleNamespace(language="python", exclusions=[]),
                SimpleNamespace(language="python", exclusions=["ignored/**"]),
            )

            with _architecture_config(project_root, configs=configs), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                architecture_code.extract_architecture_code()

            self.assertEqual(2, extract_code.call_count)
            self.assertEqual(2, len(_cache_files(project_root)))

    def test_changing_language_uses_different_cache_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            extract_code = _extract_code_mock(_fake_code_map())
            configs = (
                SimpleNamespace(language="python", exclusions=[]),
                SimpleNamespace(language="php", exclusions=[]),
            )

            with _architecture_config(project_root, configs=configs), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                architecture_code.extract_architecture_code()

            self.assertEqual(2, extract_code.call_count)
            self.assertEqual(
                ("python", project_root, ()),
                extract_code.call_args_list[0].args,
            )
            self.assertEqual(
                ("php", project_root, ()),
                extract_code.call_args_list[1].args,
            )
            self.assertEqual(2, len(_cache_files(project_root)))

    def test_configured_architecture_root_is_extracted_with_workspace_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            source_root = project_root / "src"
            source_root.mkdir()
            (source_root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            extract_code = _extract_code_mock(_fake_code_map())
            config = SimpleNamespace(
                language="python",
                exclusions=[],
                architecture_root="src",
            )

            with _architecture_config(project_root, configs=(config,)), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                code_analysis = architecture_code.extract_architecture_code()

            extract_code.assert_called_once_with(
                "python",
                source_root.resolve(),
                architecture_code.DEFAULT_ARCHITECTURE_EXCLUSIONS,
            )
            self.assertEqual(1, len(_cache_files(project_root)))
            self.assertFalse((source_root / ".enclosure").exists())
            self.assertEqual(
                ("app", "dep"),
                tuple(code_analysis.code_map.graph.node_ids()),
            )
            self.assertEqual(
                "dep",
                code_analysis.code_map.graph.outgoing("app")[0].to_id,
            )

    def test_out_of_scope_source_file_does_not_invalidate_scoped_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            source_root = project_root / "src"
            source_root.mkdir()
            (source_root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (project_root / "outside.py").write_text("VALUE = 1\n", encoding="utf-8")
            extract_code = _extract_code_mock(_fake_code_map())
            config = SimpleNamespace(
                language="python",
                exclusions=[],
                architecture_root="src",
            )

            with _architecture_config(project_root, configs=(config,)), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                (project_root / "outside.py").write_text(
                    "VALUE = 2\n",
                    encoding="utf-8",
                )
                cached = architecture_code.extract_architecture_code()

            extract_code.assert_called_once()
            self.assertEqual(
                ("app", "dep"),
                tuple(cached.code_map.graph.node_ids()),
            )

    def test_out_of_scope_added_and_deleted_files_do_not_invalidate_scoped_cache(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            source_root = project_root / "src"
            source_root.mkdir()
            (source_root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            extract_code = _extract_code_mock(_fake_code_map())
            config = SimpleNamespace(
                language="python",
                exclusions=[],
                architecture_root="src",
            )

            with _architecture_config(project_root, configs=(config,)), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                outside_path = project_root / "outside.py"
                outside_path.write_text("VALUE = 1\n", encoding="utf-8")
                architecture_code.extract_architecture_code()
                outside_path.unlink()
                architecture_code.extract_architecture_code()

            extract_code.assert_called_once()

    def test_project_relative_exclusions_are_normalized_for_architecture_root(
        self,
    ) -> None:
        project_root = Path("/project")
        architecture_root = project_root / "src"
        config = SimpleNamespace(
            exclusions=["src/generated/**", "ignored/**"],
            architecture_root="src",
        )

        exclusions = architecture_code._extraction_exclusions(
            project_root,
            architecture_root,
            config,
        )

        self.assertIn("src/generated/**", exclusions)
        self.assertIn("generated/**", exclusions)
        self.assertIn("ignored/**", exclusions)

    def test_source_target_collection_prunes_excluded_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            (project_root / "src").mkdir()
            (project_root / "src" / "app.py").write_text("VALUE = 1\n")
            ignored_root = project_root / "src" / "ignored"
            ignored_root.mkdir()
            (ignored_root / "generated.py").write_text("VALUE = 1\n")

            targets, files_found, files_excluded = (
                architecture_code_cache._collect_source_targets(
                    project_root / "src",
                    (".py",),
                    ("ignored/**",),
                    source_prefix="",
                )
            )

        self.assertEqual(("app.py",), tuple(target.source_id for target in targets))
        self.assertEqual(1, files_found)
        self.assertEqual(0, files_excluded)

    def test_changing_non_extraction_config_reuses_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            first_config = SimpleNamespace(
                language="python",
                exclusions=[],
                marker="first",
            )
            second_config = SimpleNamespace(
                language="python",
                exclusions=[],
                marker="second",
            )
            extract_code = _extract_code_mock(_fake_code_map())

            with _architecture_config(
                project_root,
                configs=(first_config, second_config),
            ), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                cached = architecture_code.extract_architecture_code()

            extract_code.assert_called_once()
            self.assertIs(second_config, cached.config)

    def test_corrupt_cache_is_ignored_and_recomputed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            extract_code = _extract_code_mock(_fake_code_map())

            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                _cache_files(project_root)[0].write_text("{not-json", encoding="utf-8")
                architecture_code.extract_architecture_code()

            self.assertEqual(2, extract_code.call_count)

    def test_old_cache_schema_is_ignored_and_recomputed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            extract_code = _extract_code_mock(_fake_code_map())

            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ):
                architecture_code.extract_architecture_code()
                cache_file = _cache_files(project_root)[0]
                cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
                cache_data["schema_version"] = 0
                cache_file.write_text(json.dumps(cache_data), encoding="utf-8")
                architecture_code.extract_architecture_code()

            self.assertEqual(2, extract_code.call_count)

    def test_extraction_errors_still_propagate_on_cache_miss(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            error = RuntimeError("code map failed")

            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                side_effect=error,
            ):
                raised = self.assertRaises(RuntimeError)
                with raised:
                    architecture_code.extract_architecture_code()

            self.assertIs(error, raised.exception)

    def test_source_changes_during_extraction_are_not_cached(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)

            def extract_code(
                language: str,
                root: Path,
                exclusions: tuple[str, ...],
            ) -> CodeMap:
                self.assertEqual("python", language)
                self.assertEqual(project_root, root)
                self.assertEqual((), exclusions)
                (project_root / "changed_during_scan.py").write_text("VALUE = 1\n")
                return _fake_code_map()

            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                side_effect=extract_code,
            ) as extract_code_mock:
                architecture_code.extract_architecture_code()

            extract_code_mock.assert_called_once()
            self.assertEqual((), _cache_files(project_root))

    def test_successful_write_prunes_old_cache_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = _project_root(temporary_directory)
            cache_dir = project_root / ".enclosure" / ".cache" / "modwire"
            cache_dir.mkdir(parents=True)
            old_cache_files = tuple(
                cache_dir / f"old-{index}.json"
                for index in range(3)
            )
            for index, cache_file in enumerate(old_cache_files):
                cache_file.write_text("{}", encoding="utf-8")
                os.utime(cache_file, ns=(index + 1, index + 1))

            extract_code = _extract_code_mock(_fake_code_map())
            with _architecture_config(project_root), patch.object(
                architecture_code,
                "extract_code",
                extract_code,
            ), patch.object(
                architecture_code_cache,
                "MAX_CACHE_ENTRIES",
                2,
            ):
                architecture_code.extract_architecture_code()

            cache_files = _cache_files(project_root)
            self.assertEqual(2, len(cache_files))
            self.assertEqual(
                ["old-2.json"],
                sorted(
                    path.name
                    for path in cache_files
                    if path.name.startswith("old")
                ),
            )


def _project_root(temporary_directory: str) -> Path:
    project_root = Path(temporary_directory)
    (project_root / ".enclosure").mkdir()
    (project_root / ".enclosure" / "enclosure.yaml").write_text(
        "architecture: {}\n",
        encoding="utf-8",
    )
    (project_root / "app.py").write_text("import dep\n", encoding="utf-8")
    (project_root / "dep.py").write_text("VALUE = 1\n", encoding="utf-8")
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
            patch(
                "enclosure.features.architecture.config.domain."
                "ArchitectureConfig.validate_mapping",
                side_effect=validate_mapping,
            ),
        ]
        for active_patch in self._patches:
            active_patch.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for active_patch in reversed(self._patches):
            active_patch.stop()


def _fake_code_map(*, prefix: str = "") -> CodeMap:
    source_id = f"{prefix}/app" if prefix else "app"
    dependency_id = f"{prefix}/dep" if prefix else "dep"
    files = {
        source_id: SourceFile(
            imports=[
                SourceImport(
                    path="dep",
                    is_relative=False,
                    normalized_path=dependency_id,
                    imported_name="",
                    is_aliased=False,
                    crossing_type="module",
                    file_barrier_crossed=False,
                    statement_id=1,
                    join_key="",
                    uses_joined_import=False,
                )
            ],
            classes=[],
            functions=[],
            line_count=1,
            code_line_count=1,
            public_symbol_count=0,
        ),
        dependency_id: SourceFile(
            imports=[],
            classes=[],
            functions=[],
            line_count=1,
            code_line_count=1,
            public_symbol_count=0,
        ),
    }
    return CodeMap(
        graph=build_dependency_graph(files),
        extraction_result=ExtractionResult(
            files=files,
            summary=ExtractionSummary(
                files_found=2,
                files_checked=2,
                files_excluded=0,
            ),
        ),
        runtime_command="python",
    )


def _extract_code_mock(code_map: CodeMap):
    return Mock(return_value=code_map)


def _cache_files(project_root: Path) -> tuple[Path, ...]:
    cache_dir = project_root / ".enclosure" / ".cache" / "modwire"
    if not cache_dir.is_dir():
        return ()
    return tuple(sorted(cache_dir.glob("*.json")))


if __name__ == "__main__":
    unittest.main()
