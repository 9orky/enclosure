from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEATURES_ROOT = PROJECT_ROOT / "src" / "enclosure" / "features"
SHARED_SCAFFOLDING_ROOT = PROJECT_ROOT / "src" / "enclosure" / "shared" / "scaffolding"
RECIPE_TEMPLATES_ROOT = PROJECT_ROOT / ".enclosure" / "recipes"

FORBIDDEN_DEEP_IMPORT = "enclosure.shared.scaffolding."

DUPLICATE_SCAFFOLD_MECHANICS = (
    "_PatternManifest",
    "_RecipeManifest",
    "FilePatternRepository",
    "FilePatternRenderer",
    "FilePatternMaterializer",
    "FileRecipe",
    "_load_yaml_mapping",
    "included_patterns_for",
    "included_recipes_for",
    "_patterns_for_rendering",
    "_recipes_for_rendering",
    "_input_specs_for",
    "target_defaults",
    "target_context",
    "variable_context",
    "normalize_target",
    "normalize_relative",
    "resolve_input",
    "PatternInputSpec",
    "PatternFile",
    "RenderedPatternFile",
    "RelativePath",
)


def test_features_do_not_deep_import_shared_scaffolding() -> None:
    violations = tuple(
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in _files_under(FEATURES_ROOT, suffixes=(".py",))
        if FORBIDDEN_DEEP_IMPORT in path.read_text(encoding="utf-8")
    )

    assert violations == ()


def test_shared_scaffolding_does_not_depend_on_features() -> None:
    violations = tuple(
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in _files_under(SHARED_SCAFFOLDING_ROOT, suffixes=(".py",))
        if "enclosure.features" in path.read_text(encoding="utf-8")
    )

    assert violations == ()


def test_features_and_recipe_templates_do_not_duplicate_scaffold_mechanics() -> None:
    violations: list[str] = []
    for root in (FEATURES_ROOT, RECIPE_TEMPLATES_ROOT):
        for path in _files_under(root, suffixes=(".py", ".tmpl", ".yaml", ".md")):
            content = path.read_text(encoding="utf-8")
            matches = tuple(
                name for name in DUPLICATE_SCAFFOLD_MECHANICS if name in content
            )
            if matches:
                relative_path = path.relative_to(PROJECT_ROOT).as_posix()
                violations.append(f"{relative_path}: {', '.join(matches)}")

    assert tuple(violations) == ()


def _files_under(root: Path, *, suffixes: tuple[str, ...]) -> tuple[Path, ...]:
    if not root.is_dir():
        return ()
    return tuple(
        sorted(
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix in suffixes
            and "__pycache__" not in path.parts
        )
    )
