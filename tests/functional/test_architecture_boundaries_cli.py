from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from conftest import copy_fixture, run_cli


def test_boundaries_pass_for_allowed_application_to_domain_import(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 0, result.stderr
    assert "Boundaries Summary:" in result.stdout
    assert "Architecture Boundaries Passed! No violations found." in result.stdout


def test_boundaries_report_forbidden_domain_import_and_cycle(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")

    result = run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 1
    assert result.stderr == ""
    assert "=== Architectural Violations Detected ===" in result.stdout
    assert (
        "- sales/report/domain -> [sales/report/application] "
        "blocked by */*/domain -> */*/application"
    ) in result.stdout
    assert (
        "- sales/report/application -> sales/report/domain -> "
        "[sales/report/application]  no-cycles"
    ) in result.stdout


def test_boundaries_report_cross_module_ui_and_domain_violations(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 1
    assert "Edge Rule Violations:" in result.stdout
    assert (
        "- sales/report/application -> [sales/ledger/application] "
        "blocked by */* -> */*"
    ) in result.stdout
    assert (
        "- sales/report/domain -> [sales/report/application] "
        "blocked by */*/domain -> */*/application"
    ) in result.stdout
    assert (
        "- sales/report/ui -> [sales/report/infrastructure] "
        "blocked by */*/ui -> */*/infrastructure"
    ) in result.stdout
    assert "Cycle Violations:" in result.stdout
    assert (
        "- sales/report/application -> sales/report/domain -> "
        "[sales/report/application]  no-cycles"
    ) in result.stdout


def test_boundaries_do_not_report_cycles_when_cycle_analyzer_is_disabled(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")
    config_path = project_root / ".enclosure" / "enclosure.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "analyzers: [backward-flow, no-cycles]",
            "analyzers: [backward-flow]",
        ),
        encoding="utf-8",
    )

    result = run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 1
    assert "Edge Rule Violations:" in result.stdout
    assert "Cycle Violations:" not in result.stdout
    assert "no-cycles" not in result.stdout


def test_boundaries_allows_cross_module_public_api_import(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    _write_public_api_boundary_probe(project_root, private_import=False)

    result = run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 0, result.stderr
    assert "Architecture Boundaries Passed! No violations found." in result.stdout
    assert "blocked by */* -> */*" not in result.stdout


def test_boundaries_blocks_private_cross_module_import_when_api_seam_exists(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    _write_public_api_boundary_probe(project_root, private_import=True)

    result = run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 1
    assert "Edge Rule Violations:" in result.stdout
    assert (
        "- sales/report/application -> [sales/ledger/application] "
        "blocked by */* -> */*"
    ) in result.stdout
    assert "sales/report/application -> [sales/ledger/__init__]" not in result.stdout


def _write_public_api_boundary_probe(
    project_root: Path,
    *,
    private_import: bool,
) -> None:
    _write_file(
        project_root / ".enclosure" / "enclosure.yaml",
        """
        architecture:
          language: python
          root: src/enclosure/features
          exclusions: []
          boundaries:
            tags:
              - { name: _t_module, match: "*/*", except: ["*/__init__"], exclude: [] }
              - { name: _t_module_api, match: "*/*/__init__", except: [], exclude: [] }
              - { name: _t_domain, match: "*/*/domain", except: [], exclude: [] }
              - { name: _t_application, match: "*/*/application", except: [], exclude: [] }
            rules:
              - { source: "*/*", disallow: ["*/*"], allow: ["*/*/__init__"], allow_same_match: true }
              - { source: "*/*/domain", disallow: ["*/*/application"], allow: [], allow_same_match: false }
            flow:
              layers: [_t_application, _t_domain]
              realms:
                - { name: _r_module, module_tag: _t_module }
              analyzers: [backward-flow, no-cycles]
          map:
            top: -1
        """,
    )
    _write_file(
        project_root / "src/enclosure/features/sales/ledger/__init__.py",
        "from .application import summarize\n",
    )
    _write_file(
        project_root / "src/enclosure/features/sales/ledger/application.py",
        "def summarize():\n    return 1\n",
    )
    application_import = (
        "from ..ledger import application as ledger_application\n\n"
        "def run():\n"
        "    return ledger_application.summarize()\n"
        if private_import
        else "from ..ledger import summarize\n\n"
        "def run():\n"
        "    return summarize()\n"
    )
    _write_file(
        project_root / "src/enclosure/features/sales/report/application.py",
        application_import,
    )


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")
