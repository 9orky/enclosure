from __future__ import annotations

from pathlib import Path
import shutil
from types import SimpleNamespace

from modwire import CodeMap
from modwire.definitions import SourceFile
from modwire.extraction import ExtractionResult, ExtractionSummary
from modwire.graph import DependencyGraph
import pytest

from enclosure.__main__ import app
from enclosure.features.architecture.boundaries.application import (
    _internal_dependency_graph,
)
from enclosure.features.architecture.boundaries.domain import BoundaryRule
from enclosure.features.architecture.boundaries.domain import ConfigTagRule
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


def test_boundaries_cli_reports_package_prefixed_deep_imports(
    tmp_path: Path,
    monkeypatch,
    cli_runner,
) -> None:
    project_root = tmp_path / "project"
    write_nested_project(
        project_root,
        {
            "src/enclosure/features/sales/orders/application.py": (
                "import enclosure.features.sales.payments.domain\n"
            ),
            "src/enclosure/features/sales/orders/domain.py": "VALUE = 1\n",
            "src/enclosure/features/sales/payments/__init__.py": "VALUE = 1\n",
            "src/enclosure/features/sales/payments/domain.py": "VALUE = 2\n",
        },
    )
    monkeypatch.setattr(project_layout, "current_project_root", lambda: project_root)

    result = cli_runner.invoke(app, ["architecture", "boundaries"])

    assert result.exit_code == 1, result.output
    assert "sales/orders/application" in result.output
    assert "sales/payments/domain" in result.output


def test_boundaries_resolves_configured_public_seam_without_python_filename() -> None:
    graph = _internal_dependency_graph(
        code_map(
            source_ids=(
                "sales/orders/application",
                "sales/payments/index",
            ),
            edges=(
                ("sales/orders/application", "vendor/sales/payments"),
            ),
        ),
        SimpleNamespace(
            language="typescript",
            architecture_root="",
            rules=SimpleNamespace(
                tags=(
                    ConfigTagRule(
                        name="module_api",
                        match="*/*/index",
                        **{"except": []},
                        exclude=[],
                    ),
                ),
                boundaries=(
                    BoundaryRule(
                        source="*/*",
                        disallow=["*/*"],
                        allow=["*/*/index"],
                        allow_same_match=True,
                    ),
                ),
            ),
        ),
    )

    assert graph.edges_between(
        "sales/orders/application",
        "sales/payments/index",
    )


@pytest.mark.parametrize(
    ("source_kind", "runtime"),
    (("typescript", "node"), ("php", "php")),
)
def test_boundaries_cli_runs_for_non_python_source_fixtures(
    fixture_project,
    use_project,
    cli_runner,
    source_kind: str,
    runtime: str,
) -> None:
    if shutil.which(runtime) is None:
        pytest.skip(f"{runtime} runtime is not available")
    project = fixture_project(f"minimal-{source_kind}")
    use_project(project)

    sync = cli_runner.invoke(app, ["workspace", "sync", "init"])
    result = cli_runner.invoke(app, ["architecture", "boundaries"])

    assert sync.exit_code == 0, sync.output
    assert result.exit_code == 0, result.output
    assert "Architecture Boundaries Passed" in result.output
    assert "Error:" not in result.output


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


def write_nested_project(project_root: Path, files: dict[str, str]) -> None:
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
  root: src/enclosure/features
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
      - { name: module, match: &module "*/*", except: ["*/__init__"], exclude: [] }
      - { name: module_api, match: &module_api "*/*/__init__", except: [], exclude: [] }
    rules:
      - { source: *module, disallow: [*module], allow: [*module_api], allow_same_match: true }
    flow:
      layers: []
      module_tag: module
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


def code_map(
    source_ids: tuple[str, ...],
    edges: tuple[tuple[str, str], ...],
) -> CodeMap:
    graph = DependencyGraph()
    for source_id in source_ids:
        graph.add_node(source_id)
    for source_id, target_id in edges:
        graph.add_edge(source_id, target_id)
    return CodeMap(
        graph=graph,
        extraction_result=ExtractionResult(
            files={
                source_id: SourceFile(
                    imports=[],
                    classes=[],
                    functions=[],
                    line_count=1,
                    code_line_count=1,
                    public_symbol_count=0,
                )
                for source_id in source_ids
            },
            summary=ExtractionSummary(
                files_found=len(source_ids),
                files_checked=len(source_ids),
                files_excluded=0,
            ),
        ),
        runtime_command="",
    )
