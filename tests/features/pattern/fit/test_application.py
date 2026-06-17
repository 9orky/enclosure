from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from enclosure.shared import layout
from enclosure.features.pattern.fit import application
from enclosure.features.pattern.fit import domain


class PatternFitTest(unittest.TestCase):
    def test_preview_renders_pattern_files_without_writing(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pattern_root = root / "patterns"
            project_root = root / "project"
            pattern_root.mkdir()
            project_root.mkdir()
            _write_pattern(
                pattern_root / "component",
                target="{{ target.path }}/{{ target.snake }}.py",
                content="class {{ target.class }}:\n    pass\n",
            )
            service = application.PatternFitService(
                pattern_root,
                _pattern_config(),
            )

            report = service.preview("component", project_root, "src/sample", {})

        self.assertTrue(report.pattern_found)
        self.assertFalse(report.pattern_empty)
        self.assertEqual(1, len(report.preview_files))
        preview_file = report.preview_files[0]
        self.assertEqual(domain.PatternPreviewStatus.CREATE, preview_file.status)
        self.assertEqual("src/sample/sample.py", preview_file.relative_path.as_posix())
        self.assertEqual("class Sample:\n    pass\n", preview_file.content)

    def test_preview_marks_existing_and_config_skipped_files(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pattern_root = root / "patterns"
            project_root = root / "project"
            pattern_root.mkdir()
            project_root.mkdir()
            existing_path = project_root / "generated" / "sample.py"
            existing_path.parent.mkdir()
            existing_path.write_text("old\n", encoding="utf-8")
            _write_pattern(
                pattern_root / "component",
                target="{{ target.path }}/sample.py",
                content="new\n",
            )
            _write_pattern(
                pattern_root / "ignored",
                target="{{ target.path }}/cache.tmp",
                content="cache\n",
            )

            existing_report = application.PatternFitService(
                pattern_root,
                _pattern_config(),
            ).preview("component", project_root, "generated", {})
            ignored_report = application.PatternFitService(
                pattern_root,
                _pattern_config(skip=("generated/*.tmp",)),
            ).preview("ignored", project_root, "generated", {})

        self.assertEqual(
            domain.PatternPreviewStatus.SKIP_EXISTS,
            existing_report.preview_files[0].status,
        )
        self.assertEqual(
            domain.PatternPreviewStatus.SKIP_CONFIG,
            ignored_report.preview_files[0].status,
        )

    def test_materialize_writes_only_create_paths(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pattern_root = root / "patterns"
            project_root = root / "project"
            pattern_root.mkdir()
            project_root.mkdir()
            _write_pattern(
                pattern_root / "component",
                target="{{ target.path }}/sample.py",
                content="new\n",
            )
            result = application.PatternFitService(
                pattern_root,
                _pattern_config(),
            ).materialize("component", project_root, "generated", {})

            created_path = project_root / "generated" / "sample.py"
            content = created_path.read_text(encoding="utf-8")

        self.assertTrue(result.pattern_found)
        self.assertEqual(
            (created_path.resolve(),),
            tuple(path.resolve() for path in result.created_paths),
        )
        self.assertEqual("new\n", content)

    def test_missing_pattern_returns_not_found_report(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pattern_root = root / "patterns"
            project_root = root / "project"
            pattern_root.mkdir()
            project_root.mkdir()

            report = application.PatternFitService(
                pattern_root,
                _pattern_config(),
            ).preview("missing", project_root, "generated", {})

        self.assertFalse(report.pattern_found)
        self.assertEqual((), report.preview_files)


def _write_pattern(pattern_path: Path, *, target: str, content: str) -> None:
    pattern_path.mkdir(parents=True)
    layout.recipe_manifest_path(pattern_path).write_text(
        f"""
schema_version: 1
role: archetype
ladder:
  family: module
  rung: component
  slots:
    domain: file
files:
  - source: templates/sample.py.tmpl
    target: "{target}"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    template_path = pattern_path / "templates" / "sample.py.tmpl"
    template_path.parent.mkdir()
    template_path.write_text(content, encoding="utf-8")


def _pattern_config(
    *,
    skip: tuple[str, ...] = (),
) -> domain.PatternFitConfig:
    return domain.PatternFitConfig(skip=skip)
