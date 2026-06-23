from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_docs_and_llm_do_not_require_workspace_config(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "no_config_project")

    docs = run_cli(project_root, "--docs")
    llm = run_cli(project_root, "--llm")

    assert docs.returncode == 0, docs.stderr
    assert docs.stderr == ""
    assert "# Enclosure Command Docs" in docs.stdout
    assert "enclosure workspace sync init" in docs.stdout
    assert llm.returncode == 0, llm.stderr
    assert llm.stderr == ""
    assert "# Enclosure LLM Guide" in llm.stdout
    assert "Agent Operating Loop" in llm.stdout
