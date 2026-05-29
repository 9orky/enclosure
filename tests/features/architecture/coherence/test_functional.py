from __future__ import annotations

from pathlib import Path

from enclosure.__main__ import app
from enclosure.shared import layout as project_layout


def test_coherence_cli_reports_clean_abstract_tree(
    tmp_path: Path,
    monkeypatch,
    cli_runner,
) -> None:
    project_root = write_project(
        tmp_path,
        tags=DEFAULT_TAGS,
        files={
            "src/sales/orders/api.py": "import sales.orders.application\n",
            "src/sales/orders/domain.py": "VALUE = 1\n",
            "src/sales/orders/application.py": "import sales.orders.domain\n",
            "src/sales/orders/ui/cli.py": "import sales.orders.application\n",
        },
    )
    monkeypatch.setattr(project_layout, "current_project_root", lambda: project_root)

    result = cli_runner.invoke(app, ["architecture", "coherence", "--top", "-1"])

    assert result.exit_code == 0, result.output
    assert "Architecture Coherence:" in result.output
    assert "sales/orders" in result.output
    assert "tree-shape 100" in result.output
    assert "Architecture Coherence Passed! No findings." in result.output


def test_coherence_cli_reports_incoherent_abstract_tree(
    tmp_path: Path,
    monkeypatch,
    cli_runner,
) -> None:
    project_root = write_project(
        tmp_path,
        tags=DEFAULT_TAGS,
        files={
            "src/sales/BadStream/api.py": "VALUE = 1\n",
            "src/sales/BadStream/domain.py": "import sales.BadStream.application\n",
            "src/sales/BadStream/domain/model.py": "VALUE = 1\n",
            "src/sales/BadStream/application.py": "import sales.BadStream.toolbox\n",
            "src/sales/BadStream/toolbox.py": "import sales.Other.domain\n",
            "src/sales/Other/domain.py": "VALUE = 1\n",
        },
    )
    monkeypatch.setattr(project_layout, "current_project_root", lambda: project_root)

    result = cli_runner.invoke(app, ["architecture", "coherence", "--top", "-1"])

    assert result.exit_code == 0, result.output
    assert "sales/BadStream" in result.output
    assert "tree-shape" in result.output
    assert "Cross-stream edge bypasses the target API seam." in result.output
    assert "Stream has no node matching the module API seam tag." in result.output


def test_coherence_cli_reports_missing_module_tag(
    tmp_path: Path,
    monkeypatch,
    cli_runner,
) -> None:
    project_root = write_project(
        tmp_path,
        tags=[tag for tag in DEFAULT_TAGS if "name: module," not in tag],
        files={"src/sales/orders/api.py": "VALUE = 1\n"},
    )
    monkeypatch.setattr(project_layout, "current_project_root", lambda: project_root)

    result = cli_runner.invoke(app, ["architecture", "coherence"])

    assert result.exit_code == 0, result.output
    assert "No feature-module stream tag configured." in result.output


DEFAULT_TAGS = [
    '{ name: feature, match: "*", except: [], exclude: [] }',
    '{ name: module, match: "*/*", except: [], exclude: [] }',
    '{ name: module_api, match: "*/*/api", except: [], exclude: [] }',
    '{ name: domain, match: "*/*/domain", except: [], exclude: [] }',
    '{ name: infrastructure, match: "*/*/infrastructure", except: [], exclude: [] }',
    '{ name: application, match: "*/*/application", except: [], exclude: [] }',
    '{ name: ui, match: "*/*/ui", except: [], exclude: [] }',
]


def write_project(
    tmp_path: Path,
    *,
    tags: list[str],
    files: dict[str, str],
) -> Path:
    project_root = tmp_path / "project"
    enclosure_dir = project_root / ".enclosure"
    enclosure_dir.mkdir(parents=True)
    for relative_path, content in files.items():
        path = project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    tag_lines = "\n".join(f"      - {tag}" for tag in tags)
    (enclosure_dir / "enclosure.yaml").write_text(
        f"""
architecture:
  language: python
  root: src
  exclusions: [.enclosure/**]
  shape:
    max_classes_per_file: -1
    max_interfaces_per_file: -1
    max_types_per_file: -1
    max_abstract_classes_per_file: -1
    max_functions_per_file: -1
    max_methods_per_class: -1
    max_declared_args_per_function: -1
    max_declared_args_per_method: -1
    max_lines_count_per_function: -1
    max_lines_count_per_method: -1
    max_lines_count_per_class: -1
    allow_optional_function_args: true
    allow_optional_method_args: true
    allow_optional_class_properties: true
    allow_imports_aliases: true
    enforce_joined_imports: false
    allowed_imports_crossing_types: [module, symbol]
  boundaries:
    tags:
{tag_lines}
    rules: []
    flow:
      layers: [ui, application, infrastructure, domain]
      module_tag: feature
      analyzers: []
  map:
    top: 20
  clusters:
    group_depth: 5
    top: 20
    files_top: 5
  health:
    top: 5
workspace:
  recipe:
    skip: []
  rules:
    local:
      max_content_chars: 2400
  sync: {{}}
""".lstrip(),
        encoding="utf-8",
    )
    return project_root
