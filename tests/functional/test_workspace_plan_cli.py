from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_plan_without_active_event_stream_reports_none(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "plan")

    assert result.returncode == 0, result.stderr
    assert "Plan report." in result.stdout
    assert "Event store: .enclosure/.cache/plans.sqlite" in result.stdout
    assert "Current plan: none" in result.stdout
    assert "Status: ok" in result.stdout


def test_plan_start_records_active_plan_event(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Planning Workflow")
    status = run_cli(project_root, "workspace", "plan")

    assert started.returncode == 0, started.stderr
    assert "Started plan " in started.stdout
    assert "Title: Planning Workflow" in started.stdout
    assert "State: active" in started.stdout
    assert "Version: 1" in started.stdout
    assert status.returncode == 0, status.stderr
    assert "Current plan: none" not in status.stdout
    assert "Title: Planning Workflow" in status.stdout
    assert "Questions: 0" in status.stdout
    assert "Projections: 0" in status.stdout


def test_plan_start_rejects_second_active_plan(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    first = run_cli(project_root, "workspace", "plan", "start", "First")
    second = run_cli(project_root, "workspace", "plan", "start", "Second")
    status = run_cli(project_root, "workspace", "plan")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 1
    assert "Only one active plan may exist" in second.stderr
    assert status.returncode == 0, status.stderr
    assert "Title: First" in status.stdout
    assert "Title: Second" not in status.stdout


def test_plan_start_requires_title_without_writing(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "plan", "start")

    assert result.returncode == 1
    assert "Plan title is required" in result.stderr
    assert not (project_root / ".enclosure" / ".cache" / "plans.sqlite").exists()


def test_root_plan_alias_reports_event_backed_status(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "plan", "start", "Alias Plan")
    result = run_cli(project_root, "plan")

    assert started.returncode == 0, started.stderr
    assert result.returncode == 0, result.stderr
    assert "Title: Alias Plan" in result.stdout
