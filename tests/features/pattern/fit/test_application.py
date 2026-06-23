from __future__ import annotations

from pathlib import Path

from enclosure.features.pattern.fit import application, domain


def test_missing_pattern_returns_not_found_report(tmp_path: Path) -> None:
    pattern_root = tmp_path / "patterns"
    project_root = tmp_path / "project"
    pattern_root.mkdir()
    project_root.mkdir()

    report = _service(pattern_root).preview("missing", project_root, "target", {})

    assert not report.pattern_found
    assert report.preview_files == ()


def test_empty_pattern_returns_empty_report(tmp_path: Path) -> None:
    pattern_root = tmp_path / "patterns"
    project_root = tmp_path / "project"
    pattern_root.mkdir()
    project_root.mkdir()
    _write_pattern(
        pattern_root,
        "empty",
        """
schema_version: 1
role: archetype
""",
    )

    report = _service(pattern_root).preview("empty", project_root, "target", {})

    assert report.pattern_found
    assert report.pattern_empty
    assert report.preview_files == ()


def test_preview_renders_pattern_files_without_writing(tmp_path: Path) -> None:
    pattern_root = tmp_path / "patterns"
    project_root = tmp_path / "project"
    pattern_root.mkdir()
    project_root.mkdir()
    _write_pattern(
        pattern_root,
        "component",
        _manifest(
            """
  - source: templates/sample.py.tmpl
    target: "{{ target.path }}/{{ target.snake }}.py"
""",
        ),
        {"templates/sample.py.tmpl": "class {{ target.class }}:\n    pass\n"},
    )

    report = _service(pattern_root).preview("component", project_root, "src/sample", {})

    assert report.pattern_found
    assert not report.pattern_empty
    assert len(report.preview_files) == 1
    preview_file = report.preview_files[0]
    assert preview_file.status is domain.PatternPreviewStatus.CREATE
    assert preview_file.relative_path.as_posix() == "src/sample/sample.py"
    assert preview_file.content == "class Sample:\n    pass\n"
    assert not preview_file.target_path.exists()


def test_preview_marks_existing_and_config_skipped_files(tmp_path: Path) -> None:
    pattern_root = tmp_path / "patterns"
    project_root = tmp_path / "project"
    pattern_root.mkdir()
    project_root.mkdir()
    existing_path = project_root / "generated" / "sample.py"
    existing_path.parent.mkdir()
    existing_path.write_text("old\n", encoding="utf-8")
    _write_pattern(
        pattern_root,
        "existing",
        _manifest(
            """
  - source: templates/sample.py.tmpl
    target: "generated/sample.py"
""",
        ),
        {"templates/sample.py.tmpl": "new\n"},
    )
    _write_pattern(
        pattern_root,
        "ignored",
        _manifest(
            """
  - source: templates/cache.tmp
    target: "generated/cache.tmp"
""",
        ),
        {"templates/cache.tmp": "cache\n"},
    )

    existing_report = _service(pattern_root).preview(
        "existing",
        project_root,
        "target",
        {},
    )
    ignored_report = _service(
        pattern_root,
        domain.PatternFitConfig(skip=("generated/*.tmp",)),
    ).preview("ignored", project_root, "target", {})

    assert existing_report.preview_files[0].status is (
        domain.PatternPreviewStatus.SKIP_EXISTS
    )
    assert ignored_report.preview_files[0].status is (
        domain.PatternPreviewStatus.SKIP_CONFIG
    )


def test_preview_renders_includes_with_shared_input_resolution(tmp_path: Path) -> None:
    pattern_root = tmp_path / "patterns"
    project_root = tmp_path / "project"
    pattern_root.mkdir()
    project_root.mkdir()
    _write_pattern(
        pattern_root,
        "support",
        """
schema_version: 1
role: fragment
inputs:
  feature:
    default_from: target_name
files:
  - source: templates/support.py.tmpl
    target: "{{ target.path }}/{{ feature.snake }}_support.py"
""",
        {"templates/support.py.tmpl": "SUPPORT = '{{ feature.class }}'\n"},
    )
    _write_pattern(
        pattern_root,
        "component",
        """
schema_version: 1
role: archetype
includes:
  - support
files:
  - source: templates/component.py.tmpl
    target: "{{ target.path }}/{{ feature.snake }}.py"
""",
        {"templates/component.py.tmpl": "COMPONENT = '{{ feature.class }}'\n"},
    )

    report = _service(pattern_root).preview("component", project_root, "src/widget", {})

    assert tuple(
        preview_file.relative_path.as_posix()
        for preview_file in report.preview_files
    ) == (
        "src/widget/widget_support.py",
        "src/widget/widget.py",
    )
    assert tuple(preview_file.content for preview_file in report.preview_files) == (
        "SUPPORT = 'Widget'\n",
        "COMPONENT = 'Widget'\n",
    )


def test_materialize_writes_only_create_paths(tmp_path: Path) -> None:
    pattern_root = tmp_path / "patterns"
    project_root = tmp_path / "project"
    pattern_root.mkdir()
    project_root.mkdir()
    _write_pattern(
        pattern_root,
        "component",
        _manifest(
            """
  - source: templates/sample.py.tmpl
    target: "{{ target.path }}/sample.py"
""",
        ),
        {"templates/sample.py.tmpl": "new\n"},
    )

    result = _service(pattern_root).materialize("component", project_root, "generated", {})
    created_path = project_root / "generated" / "sample.py"

    assert result.pattern_found
    assert tuple(path.resolve() for path in result.created_paths) == (
        created_path.resolve(),
    )
    assert created_path.read_text(encoding="utf-8") == "new\n"


def _service(
    pattern_root: Path,
    config: domain.PatternFitConfig | None = None,
) -> application.PatternFitService:
    return application.PatternFitService(
        pattern_root,
        config or domain.PatternFitConfig(),
    )


def _write_pattern(
    pattern_root: Path,
    name: str,
    manifest: str,
    templates: dict[str, str] | None = None,
) -> None:
    pattern_path = pattern_root / name
    pattern_path.mkdir(parents=True)
    (pattern_path / "recipe.yaml").write_text(manifest.strip() + "\n", encoding="utf-8")
    for template_name, content in (templates or {}).items():
        template_path = pattern_path / template_name
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(content, encoding="utf-8")


def _manifest(files: str) -> str:
    return f"""
schema_version: 1
role: archetype
ladder:
  family: module
  rung: component
  slots:
    domain: file
files:
{files}"""
