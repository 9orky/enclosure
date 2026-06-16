from __future__ import annotations

from pathlib import Path

import pytest

from enclosure.__main__ import app
from enclosure.features.architecture.config.domain import ArchitectureConfig
from enclosure.shared import config as shared_config
from enclosure.shared import layout as project_layout


def test_architecture_reports_map_backend_and_gui_realms(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cli_runner,
) -> None:
    project_root = tmp_path / "project"
    write_multi_realm_project(project_root)
    monkeypatch.setattr(project_layout, "current_project_root", lambda: project_root)

    boundaries = cli_runner.invoke(app, ["architecture", "boundaries"])
    architecture_map = cli_runner.invoke(app, ["architecture", "map", "--top", "-1"])
    health = cli_runner.invoke(app, ["architecture", "health", "--vv", "--top", "-1"])

    assert boundaries.exit_code == 0, boundaries.output
    assert architecture_map.exit_code == 0, architecture_map.output
    assert health.exit_code == 0, health.output

    assert "Unknown files: 0" in architecture_map.output
    assert "- freeloader/block/catalog: " in architecture_map.output
    assert "- app: " in architecture_map.output
    assert "- app/pages: " in architecture_map.output
    assert "- app/pages/blocks: " in architecture_map.output
    assert "app/pages/blocks -> freeloader/block/catalog" in architecture_map.output

    assert "Map: 4 module(s)" in health.output
    assert "0 unknown file(s)" in health.output
    assert "outside configured module tags" not in health.output


def test_duplicate_architecture_tag_names_are_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "enclosure.yaml"
    raw_data = multi_realm_config(
        """
      - { name: module, match: "freeloader/*/*", except: [], exclude: [] }
      - { name: module, match: "app/pages/*", except: [], exclude: [] }
""",
    )

    with pytest.raises(shared_config.ConfigError) as raised:
        ArchitectureConfig.validate_mapping(raw_data, config_path)

    assert "duplicate architecture boundary tag name(s): module" in str(raised.value)


def write_multi_realm_project(project_root: Path) -> None:
    files = {
        "src/freeloader/block/catalog/domain.py": "VALUE = 1\n",
        "src/freeloader/block/catalog/application.py": (
            "from freeloader.block.catalog import domain\n"
            "RESULT = domain.VALUE\n"
        ),
        "src/app/__init__.py": "APP = 'app'\n",
        "src/app/pages/__init__.py": "PAGES = 'pages'\n",
        "src/app/pages/blocks.py": (
            "from freeloader.block.catalog import domain\n"
            "TITLE = domain.VALUE\n"
        ),
    }
    for relative_path, content in files.items():
        path = project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    enclosure_dir = project_root / ".enclosure"
    enclosure_dir.mkdir(parents=True)
    (enclosure_dir / "enclosure.yaml").write_text(
        multi_realm_config_text(
            """
      - { name: module, match: "freeloader/*/*", except: ["*/__init__"], exclude: [] }
      - { name: domain, match: "freeloader/*/*/domain", except: [], exclude: [] }
      - { name: application, match: "freeloader/*/*/application", except: [], exclude: [] }
      - { name: gui_app, match: "app", except: [], exclude: [] }
      - { name: gui_pages, match: "app/pages", except: [], exclude: [] }
      - { name: gui_page, match: "app/pages/*", except: ["app/pages/__init__"], exclude: [] }
""",
        ),
        encoding="utf-8",
    )


def multi_realm_config(tag_text: str) -> dict[str, object]:
    import yaml

    return yaml.safe_load(multi_realm_config_text(tag_text))


def multi_realm_config_text(tag_text: str) -> str:
    return f"""
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
{tag_text.rstrip()}
    rules:
      - {{ source: "freeloader/*/*/domain", disallow: ["freeloader/*/*/application"], allow: [], allow_same_match: true }}
    flow:
      realms:
        - name: freeloader
          module_tag: module
          layers: [application, domain]
        - name: gui
          module_tag: gui_app
          layers: []
        - name: gui
          module_tag: gui_pages
          layers: []
        - name: gui
          module_tag: gui_page
          layers: []
      analyzers: [backward-flow, no-cycles]
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
  sync: {{}}
""".lstrip()
