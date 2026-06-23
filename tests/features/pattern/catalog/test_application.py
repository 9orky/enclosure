from __future__ import annotations

from pathlib import Path

from enclosure.features.pattern.catalog.application import describe, preview, validate
from enclosure.shared.scaffolding import scaffolding


def test_list_and_show_patterns_from_manifest_catalog(tmp_path: Path) -> None:
    _write_pattern(
        tmp_path,
        "module",
        """
schema_version: 1
role: container
description: Pattern container.
archetypes:
  - component
""",
    )
    _write_pattern(
        tmp_path,
        "component",
        """
schema_version: 1
role: archetype
description: Component Pattern.
ladder:
  family: module
  rung: component
  slots:
    domain: file
files:
  - source: templates/domain.py.tmpl
    target: "{{ target.path }}/domain.py"
""",
    )

    patterns = describe.list_patterns(pattern_root=tmp_path)
    component = describe.show_pattern("component", pattern_root=tmp_path)

    assert tuple(item["name"] for item in patterns) == ("component", "module")
    assert component is not None
    assert component["description"] == "Component Pattern."
    assert component["role"] == "archetype"
    assert component["files"] == ("{{ target.path }}/domain.py",)


def test_validate_catalog_accepts_container_and_roles_map(tmp_path: Path) -> None:
    _write_pattern(tmp_path, "module", _container_manifest(("component",)))
    _write_pattern(tmp_path, "component", _archetype_manifest())

    report = validate.validate_catalog(
        pattern_root=tmp_path,
        roles_map={"feature/component": "component"},
    )

    assert report.passed()
    assert report.patterns_checked == 2


def test_validate_catalog_reports_missing_container_archetype(tmp_path: Path) -> None:
    _write_pattern(tmp_path, "module", _container_manifest(()))
    _write_pattern(tmp_path, "component", _archetype_manifest())

    report = validate.validate_catalog(
        pattern_root=tmp_path,
        roles_map={"feature/component": "component"},
    )

    assert "missing_container_archetypes" in {
        violation.code for violation in report.violations
    }


def test_validate_catalog_reports_missing_roles_map_pattern(tmp_path: Path) -> None:
    _write_pattern(tmp_path, "module", _container_manifest(("component",)))
    _write_pattern(tmp_path, "component", _archetype_manifest())

    report = validate.validate_catalog(
        pattern_root=tmp_path,
        roles_map={"feature/component": "missing"},
    )

    assert "missing_role_pattern" in {
        violation.code for violation in report.violations
    }


def test_composed_role_merges_included_ladder_slots(tmp_path: Path) -> None:
    _write_pattern(
        tmp_path,
        "base",
        """
schema_version: 1
role: fragment
ladder:
  family: module-slot
  rung: domain
  slots:
    domain: file
""",
    )
    _write_pattern(
        tmp_path,
        "support",
        """
schema_version: 1
role: fragment
ladder:
  family: module-slot
  rung: infrastructure
  slots:
    infrastructure: file
""",
    )

    patterns_by_name = {
        pattern.name: pattern
        for pattern in scaffolding.load_all(tmp_path)
    }
    role_pattern = preview.pattern_for_role("base+support", patterns_by_name)

    assert role_pattern is not None
    assert role_pattern.role == "archetype"
    ladder = preview.composed_ladder_for(role_pattern, patterns_by_name)
    assert ladder["family"] == "composed"
    assert ladder["rung"] == "base+support"
    assert set(ladder["slots"]) == {"domain", "infrastructure"}


def _write_pattern(
    pattern_root: Path,
    name: str,
    manifest: str,
) -> None:
    pattern_path = pattern_root / name
    pattern_path.mkdir(parents=True)
    (pattern_path / "recipe.yaml").write_text(manifest.strip() + "\n", encoding="utf-8")
    template_path = pattern_path / "templates" / "domain.py.tmpl"
    template_path.parent.mkdir()
    template_path.write_text("from __future__ import annotations\n", encoding="utf-8")


def _container_manifest(archetypes: tuple[str, ...]) -> str:
    if not archetypes:
        return """
schema_version: 1
role: container
"""
    archetype_lines = "".join(f"  - {archetype}\n" for archetype in archetypes)
    return f"""
schema_version: 1
role: container
archetypes:
{archetype_lines}"""


def _archetype_manifest() -> str:
    return """
schema_version: 1
role: archetype
ladder:
  family: module
  rung: component
  slots:
    domain: file
files:
  - source: templates/domain.py.tmpl
    target: "{{ target.path }}/domain.py"
"""
