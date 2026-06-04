from __future__ import annotations

from pathlib import Path

from enclosure.features.architecture.gui import application
from enclosure.shared import layout as project_layout


def test_gui_snapshot_includes_boundaries_symbols_and_shape(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = _write_project(tmp_path)
    monkeypatch.setattr(project_layout, "current_project_root", lambda: project_root)

    snapshot = application.build_gui_snapshot()
    data = snapshot.to_json_dict()

    assert data["architecture_root"] == "src"
    assert data["files_checked"] == 2
    files = {file["source_id"]: file for file in data["files"]}
    assert set(files) == {"sales/orders/application", "sales/orders/domain"}
    assert files["sales/orders/application"]["symbols"]
    assert files["sales/orders/application"]["shape_findings"]
    assert files["sales/orders/domain"]["boundary_findings"]
    assert data["boundary_rules"]
    assert data["exclusions"] == [".enclosure/**"]


def _write_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    enclosure_dir = project_root / ".enclosure"
    source_dir = project_root / "src" / "sales" / "orders"
    enclosure_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    (source_dir / "application.py").write_text(
        "def run():\n    return 1\n",
        encoding="utf-8",
    )
    (source_dir / "domain.py").write_text(
        "import sales.orders.application\n",
        encoding="utf-8",
    )
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
    max_functions_per_file: 0
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
      - { name: feature, match: "*", except: [], exclude: [] }
      - { name: module, match: "*/*", except: [], exclude: [] }
      - { name: module_api, match: "*/*/__init__", except: [], exclude: [] }
      - { name: domain, match: "*/*/domain", except: [], exclude: [] }
      - { name: application, match: "*/*/application", except: [], exclude: [] }
    rules:
      - { source: "*/*/domain", disallow: ["*/*/application"], allow: [], allow_same_match: false }
    flow:
      layers: [application, domain]
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
  sync: {}
""".lstrip(),
        encoding="utf-8",
    )
    return project_root
