from __future__ import annotations

from pathlib import Path

import pytest

from enclosure.shared.scaffolding import (
    RenderedScaffoldFile,
    Scaffold,
    ScaffoldError,
    scaffolding,
)


def test_public_seam_exports_only_required_names() -> None:
    import enclosure.shared.scaffolding as package

    expected_exports = [
        "RenderedScaffoldFile",
        "Scaffold",
        "ScaffoldError",
        "scaffolding",
    ]
    assert package.__all__ == expected_exports
    assert sorted(name for name in expected_exports if hasattr(package, name)) == sorted(
        expected_exports
    )
    assert package.scaffolding.__class__.__name__ == "ScaffoldFacade"
    assert callable(package.scaffolding.load_all)
    assert callable(package.scaffolding.render)
    assert not hasattr(package, "ScaffoldFacade")
    assert not hasattr(package, "ManifestScaffoldRepository")
    assert not hasattr(package, "ScaffoldRenderer")
    assert not hasattr(package, "RenderedFileWriter")


def test_loads_valid_manifest_and_normalizes_values(tmp_path: Path) -> None:
    scaffold_root = _write_scaffold(
        tmp_path,
        "module",
        manifest="""
schema_version: 1
role: archetype
description: " Example module "
ladder:
  family: feature
  rung: module
  slots:
    application:
      state: split-files
      files:
        - application/commands.py
includes:
  - shared
archetypes:
  - base
roles_map:
  src/example: module
inputs:
  component:
    type: identifier
    required: true
files:
  - source: templates/component.py.tmpl
    target: "{{ target.path }}/{{ component.snake }}.py"
""",
        files={"templates/component.py.tmpl": "class {{ component.pascal }}:\n    pass\n"},
    )

    loaded = scaffolding.load(tmp_path, "module")
    assert isinstance(loaded, Scaffold)
    assert loaded.name == "module"
    assert loaded.source_root == scaffold_root
    assert loaded.role == "archetype"
    assert loaded.description == "Example module"
    assert loaded.ladder.summary() == {
        "family": "feature",
        "rung": "module",
        "slots": {
            "application": {
                "state": "split-files",
                "files": ("application/commands.py",),
                "packages": (),
            },
        },
    }
    assert loaded.includes == ("shared",)
    assert loaded.archetypes == ("base",)
    assert loaded.roles_map == {"src/example": "module"}
    assert loaded.inputs[0].name == "component"
    assert loaded.files[0].source.as_posix() == "templates/component.py.tmpl"


def test_load_all_discovers_child_manifests_in_name_order(tmp_path: Path) -> None:
    _write_scaffold(tmp_path, "beta")
    _write_scaffold(tmp_path, "alpha")
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "recipe.yaml").write_text("schema_version: 1\nrole: fragment\n", encoding="utf-8")

    assert tuple(scaffold.name for scaffold in scaffolding.load_all(tmp_path)) == ("alpha", "beta")
    assert scaffolding.load_all(tmp_path / "missing") == ()


@pytest.mark.parametrize(
    ("manifest", "message"),
    [
        ("[broken", "Invalid scaffold manifest syntax"),
        ("- item\n", "mapping at the top level"),
        ("schema_version: 2\nrole: fragment\n", "Unsupported scaffold schema_version"),
        ("schema_version: 1\nrole: invalid\n", "Unsupported scaffold role"),
        (
            "schema_version: 1\nrole: fragment\nfiles:\n  - source: ../bad.tmpl\n    target: x\n",
            "must not traverse outside",
        ),
        (
            "schema_version: 1\nrole: fragment\nfiles:\n  - source: C:/bad.tmpl\n    target: x\n",
            "must be relative",
        ),
    ],
)
def test_manifest_validation_fails_loudly(
    tmp_path: Path,
    manifest: str,
    message: str,
) -> None:
    _write_scaffold(tmp_path, "bad", manifest=manifest)

    with pytest.raises(ScaffoldError, match=message):
        scaffolding.load(tmp_path, "bad")


def test_variable_parsing_and_input_resolution_are_rendered_through_context(
    tmp_path: Path,
) -> None:
    scaffold = scaffolding.load(
        tmp_path,
        _write_scaffold(
            tmp_path,
            "with-inputs",
            manifest="""
schema_version: 1
role: fragment
inputs:
  component:
    type: identifier
    default_from: target_name
  package:
    type: dotted_name
    default: enclosure.demo
  mode:
    type: choice
    choices: [sync, async]
    default: sync
  items:
    type: list
    default: one, two
files:
  - source: template.tmpl
    target: "{{ target.parent }}/{{ component.snake }}_{{ mode.value }}.py"
""",
            files={
                "template.tmpl": (
                    "{{ target.path }}|{{ target.class }}|{{ component.camel }}|"
                    "{{ package.value }}|{{ items }}\n"
                ),
            },
        ).name,
    )

    variables = scaffolding.parse_variables(("component=HttpClient",))
    rendered = scaffolding.render(scaffold, (scaffold,), tmp_path, "src/service", variables)

    assert rendered == (
        RenderedScaffoldFile(
            source_path=scaffold.source_root / "template.tmpl",
            target_path=tmp_path.resolve() / "src" / "http_client_sync.py",
            relative_path=Path("src/http_client_sync.py"),
            content="src/service|Service|httpClient|enclosure.demo|('one', 'two')\n",
        ),
    )


def test_render_rejects_missing_required_invalid_variables_and_unsafe_targets(
    tmp_path: Path,
) -> None:
    scaffold = scaffolding.load(
        tmp_path,
        _write_scaffold(
            tmp_path,
            "strict",
            manifest="""
schema_version: 1
role: fragment
inputs:
  component:
    type: identifier
    required: true
files:
  - source: template.tmpl
    target: "{{ component.snake }}.py"
""",
            files={"template.tmpl": ""},
        ).name,
    )

    with pytest.raises(ScaffoldError, match="Missing required scaffold variable"):
        scaffolding.render(scaffold, (scaffold,), tmp_path, "src/example", {})
    with pytest.raises(ScaffoldError, match="must be an identifier"):
        scaffolding.render(scaffold, (scaffold,), tmp_path, "src/example", {"component": "not valid"})
    with pytest.raises(ScaffoldError, match="Target path must stay inside the target root"):
        scaffolding.render(
            scaffold,
            (scaffold,),
            tmp_path,
            tmp_path.parent / "outside",
            {"component": "valid"},
        )


def test_render_rejects_missing_templates_and_unsafe_rendered_targets(tmp_path: Path) -> None:
    missing_template = scaffolding.load(
        tmp_path,
        _write_scaffold(
            tmp_path,
            "missing-template",
            manifest="""
schema_version: 1
role: fragment
files:
  - source: missing.tmpl
    target: output.py
""",
        ).name,
    )
    unsafe_target = scaffolding.load(
        tmp_path,
        _write_scaffold(
            tmp_path,
            "unsafe-target",
            manifest="""
schema_version: 1
role: fragment
files:
  - source: template.tmpl
    target: "../escape.py"
""",
            files={"template.tmpl": ""},
        ).name,
    )

    with pytest.raises(ScaffoldError, match="Scaffold template does not exist"):
        scaffolding.render(missing_template, (missing_template,), tmp_path, "src/example", {})
    with pytest.raises(ScaffoldError, match="must not traverse outside"):
        scaffolding.render(unsafe_target, (unsafe_target,), tmp_path, "src/example", {})


def test_compose_orders_included_scaffolds_before_target(tmp_path: Path) -> None:
    shared = _write_scaffold(
        tmp_path,
        "shared",
        manifest="""
schema_version: 1
role: fragment
inputs:
  component:
    type: identifier
    default: SharedComponent
files:
  - source: shared.tmpl
    target: "{{ target.path }}/00_{{ component.snake }}.py"
""",
        files={"shared.tmpl": "shared={{ component.value }}\n"},
    )
    feature = _write_scaffold(
        tmp_path,
        "feature",
        manifest="""
schema_version: 1
role: fragment
includes:
  - shared
inputs:
  component:
    type: identifier
    default: FeatureComponent
files:
  - source: feature.tmpl
    target: "{{ target.path }}/10_{{ component.snake }}.py"
""",
        files={"feature.tmpl": "feature={{ component.value }}\n"},
    )
    scaffolds = scaffolding.load_all(tmp_path)
    shared_scaffold = scaffolding.load(tmp_path, shared.name)
    feature_scaffold = scaffolding.load(tmp_path, feature.name)

    assert tuple(item.name for item in scaffolding.compose(feature_scaffold, scaffolds)) == (
        "shared",
        "feature",
    )

    rendered = scaffolding.render(feature_scaffold, scaffolds, tmp_path, "src/app", {})

    assert rendered == (
        RenderedScaffoldFile(
            source_path=shared_scaffold.source_root / "shared.tmpl",
            target_path=tmp_path.resolve() / "src" / "app" / "00_feature_component.py",
            relative_path=Path("src/app/00_feature_component.py"),
            content="shared=FeatureComponent\n",
        ),
        RenderedScaffoldFile(
            source_path=feature_scaffold.source_root / "feature.tmpl",
            target_path=tmp_path.resolve() / "src" / "app" / "10_feature_component.py",
            relative_path=Path("src/app/10_feature_component.py"),
            content="feature=FeatureComponent\n",
        ),
    )


def test_compose_rejects_missing_includes_and_cycles(tmp_path: Path) -> None:
    missing_include = scaffolding.load(
        tmp_path,
        _write_scaffold(
            tmp_path,
            "missing-include",
            manifest="""
schema_version: 1
role: fragment
includes:
  - not-present
""",
        ).name,
    )
    _write_scaffold(
        tmp_path,
        "cycle-a",
        manifest="""
schema_version: 1
role: fragment
includes:
  - cycle-b
""",
    )
    cycle_b = scaffolding.load(
        tmp_path,
        _write_scaffold(
            tmp_path,
            "cycle-b",
            manifest="""
schema_version: 1
role: fragment
includes:
  - cycle-a
""",
        ).name,
    )
    scaffolds = scaffolding.load_all(tmp_path)

    with pytest.raises(ScaffoldError, match="Scaffold include not found: not-present"):
        scaffolding.compose(missing_include, scaffolds)
    with pytest.raises(ScaffoldError, match="Scaffold include cycle: cycle-b -> cycle-a -> cycle-b"):
        scaffolding.compose(cycle_b, scaffolds)


def test_write_materializes_only_selected_paths(tmp_path: Path) -> None:
    first = RenderedScaffoldFile(
        source_path=tmp_path / "first.tmpl",
        target_path=tmp_path / "created" / "first.py",
        relative_path=Path("created/first.py"),
        content="first\n",
    )
    second = RenderedScaffoldFile(
        source_path=tmp_path / "second.tmpl",
        target_path=tmp_path / "created" / "second.py",
        relative_path=Path("created/second.py"),
        content="second\n",
    )

    scaffolding.write((first, second), (first.target_path,))

    assert first.target_path.read_text(encoding="utf-8") == "first\n"
    assert not second.target_path.exists()


def _write_scaffold(
    root: Path,
    name: str,
    *,
    manifest: str = "schema_version: 1\nrole: fragment\n",
    files: dict[str, str] | None = None,
) -> Path:
    scaffold_root = root / name
    scaffold_root.mkdir(parents=True)
    (scaffold_root / "recipe.yaml").write_text(manifest.lstrip(), encoding="utf-8")
    for relative_path, content in (files or {}).items():
        path = scaffold_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return scaffold_root
