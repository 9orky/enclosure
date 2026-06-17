from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from enclosure.shared import layout
from enclosure.features.pattern.catalog.application import describe
from enclosure.features.pattern.catalog.application import preview
from enclosure.features.pattern.catalog.application import validate
from enclosure.features.pattern.catalog.domain import manifest
from enclosure.features.pattern.catalog.domain import report as report_domain


class PatternCatalogTest(unittest.TestCase):
    def test_list_and_show_patterns_from_manifest_catalog(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            pattern_root = Path(temporary_directory)
            _write_pattern(
                pattern_root / "module",
                """
schema_version: 1
role: container
description: Pattern container.
archetypes:
  - component
""",
            )
            _write_pattern(
                pattern_root / "component",
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

            patterns = describe.list_patterns(pattern_root=pattern_root)
            component = describe.show_pattern("component", pattern_root=pattern_root)

        self.assertEqual(("component", "module"), tuple(item["name"] for item in patterns))
        self.assertIsNotNone(component)
        assert component is not None
        self.assertEqual("Component Pattern.", component["description"])
        self.assertEqual("archetype", component["role"])
        self.assertEqual(("{{ target.path }}/domain.py",), component["files"])

    def test_validate_catalog_accepts_container_and_roles_map(self) -> None:
        report = _validate_catalog(
            {
                "module": _container_manifest(("component",)),
                "component": _archetype_manifest(),
            },
            roles_map={"feature/component": "component"},
        )

        self.assertTrue(report.passed())
        self.assertEqual(2, report.patterns_checked)

    def test_validate_catalog_reports_missing_container_archetype(self) -> None:
        report = _validate_catalog(
            {
                "module": _container_manifest(()),
                "component": _archetype_manifest(),
            },
            roles_map={"feature/component": "component"},
        )

        self.assertEqual(
            ("missing_container_archetypes",),
            tuple(violation.code for violation in report.violations),
        )

    def test_validate_catalog_reports_missing_roles_map_pattern(self) -> None:
        report = _validate_catalog(
            {
                "module": _container_manifest(("component",)),
                "component": _archetype_manifest(),
            },
            roles_map={"feature/component": "missing"},
        )

        self.assertEqual(
            ("missing_role_pattern",),
            tuple(violation.code for violation in report.violations),
        )

    def test_composed_role_merges_included_ladder_slots(self) -> None:
        patterns_by_name = {
            "base": manifest.Pattern(
                name="base",
                root_path=Path("base"),
                role=manifest.PatternRole.ARCHETYPE,
                ladder=manifest.PatternLadder(
                    family="module",
                    rung="base",
                    slots=(
                        manifest.PatternSlot(
                            name=manifest.PatternSlotName("domain"),
                            state=manifest.PatternSlotState.FILE,
                        ),
                    ),
                    declared=True,
                ),
            ),
            "support": manifest.Pattern(
                name="support",
                root_path=Path("support"),
                role=manifest.PatternRole.FRAGMENT,
                ladder=manifest.PatternLadder(
                    family="module-slot",
                    rung="support",
                    slots=(
                        manifest.PatternSlot(
                            name=manifest.PatternSlotName("infrastructure"),
                            state=manifest.PatternSlotState.FILE,
                        ),
                    ),
                    declared=True,
                ),
            ),
        }

        pattern = preview.pattern_for_role("base+support", patterns_by_name)
        assert pattern is not None
        ladder = preview.composed_ladder_for(pattern, patterns_by_name)

        self.assertEqual(
            ("domain", "infrastructure"),
            tuple(slot.name.value for slot in ladder.slots),
        )


def _validate_catalog(
    manifests: dict[str, str],
    *,
    roles_map: dict[str, str],
) -> report_domain.PatternCatalogReport:
    with TemporaryDirectory() as temporary_directory:
        pattern_root = Path(temporary_directory)
        for pattern_name, manifest in manifests.items():
            _write_pattern(pattern_root / pattern_name, manifest)
        return validate.validate_catalog(
            pattern_root=pattern_root,
            roles_map=roles_map,
        )


def _write_pattern(pattern_path: Path, manifest: str) -> None:
    pattern_path.mkdir(parents=True)
    layout.recipe_manifest_path(pattern_path).write_text(
        manifest.strip() + "\n",
        encoding="utf-8",
    )
    templates_path = pattern_path / "templates"
    templates_path.mkdir()
    (templates_path / "domain.py.tmpl").write_text(
        "from __future__ import annotations\n",
        encoding="utf-8",
    )


def _container_manifest(archetypes: tuple[str, ...]) -> str:
    if not archetypes:
        return """
schema_version: 1
role: container
"""
    archetype_lines = "\n".join(f"  - {archetype}" for archetype in archetypes)
    return f"""
schema_version: 1
role: container
archetypes:
{archetype_lines}
"""


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
