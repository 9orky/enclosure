from __future__ import annotations

from pathlib import Path

from enclosure.__main__ import app
from enclosure.shared import layout as project_layout


def test_boundaries_cli_renders_architectural_violations(
    tmp_path: Path,
    monkeypatch,
    cli_runner,
) -> None:
    project_root = tmp_path / "project"
    write_project(
        project_root,
        {
            "src/sales/orders/domain.py": "import sales.orders.application\n",
            "src/sales/orders/application.py": "VALUE = 1\n",
        },
    )
    monkeypatch.setattr(project_layout, "current_project_root", lambda: project_root)

    result = cli_runner.invoke(app, ["architecture", "boundaries"])

    assert result.exit_code == 1, result.output
    assert "Architectural Violations Detected" in result.output
    assert "Error: 'BoundariesReport' object is not iterable" not in result.output


def write_project(project_root: Path, files: dict[str, str]) -> None:
    enclosure_dir = project_root / ".enclosure"
    enclosure_dir.mkdir(parents=True)
    for relative_path, content in files.items():
        path = project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (enclosure_dir / "enclosure.yaml").write_text(
        """
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
      - { name: domain, match: "*/*/domain", except: [], exclude: [] }
      - { name: application, match: "*/*/application", except: [], exclude: [] }
    rules:
      - { source: "*/*/domain", disallow: ["*/*/application"], allow: [], allow_same_match: false }
    flow:
      layers: [application, domain]
      module_tag: domain
      analyzers: []
  map:
    top: 20
  pressure:
    top: 10
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
  sync: {}
""".lstrip(),
        encoding="utf-8",
    )
