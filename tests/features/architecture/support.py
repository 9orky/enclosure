from __future__ import annotations

from pathlib import Path

import pytest

from enclosure.shared import architecture_code
from enclosure.shared.config.facade import SettingsFacade
from enclosure.shared.config.manifest import Manifest


def use_architecture_settings(
    monkeypatch: pytest.MonkeyPatch,
    project_root: Path,
) -> None:
    monkeypatch.setattr(
        architecture_code,
        "settings",
        SettingsFacade(Manifest(project_root)),
    )


def write_architecture_config(project_root: Path, language: str) -> None:
    enclosure_dir = project_root / ".enclosure"
    enclosure_dir.mkdir(parents=True, exist_ok=True)
    (enclosure_dir / "enclosure.yaml").write_text(
        f"""
architecture:
  language: {language}
  root: .
  exclusions: [.enclosure/**, ignored/**]
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
    tags: []
    rules: []
    flow:
      layers: []
      module_tag: ""
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
  sync: {{}}
""".lstrip(),
        encoding="utf-8",
    )
