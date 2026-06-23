# Implementation Tree

```text
src/enclosure/features/workspace/recipe/
  domain.py
    recipe-specific report and bench dataclasses remain
    recipe-local duplicate scaffold inputs/files/render/context helpers removed
    compatibility role/ladder/slot exports remain only where public API requires them
  infrastructure.py
    deleted
  application.py
    RecipeService uses shared load/compose/render/write/parse behavior from package root
    recipe drift, bench, show, list, check, and CLI-facing result behavior preserved
  __init__.py
    public recipe API remains stable
tests/features/workspace/recipe/
  test_functional.py
    unchanged functional proof covers list, show, check, dry-run, shell preview,
    generate, bench, and bench-all behavior
```

Status: Complete.

# Goal

Integrate one bounded context as proof. Use `workspace.recipe` because it has the strongest current behavior surface and tests.

The goal is not just to call the shared package. The goal is measurable code and complexity reduction: delete recipe-local manifest parsing, repository discovery, include traversal, included input aggregation, rendering, materializer, relative path normalization, target context, defaults, and variable parsing where the shared package now owns them.

# Step Contract

- Inputs: completed and stable Step 01 shared scaffolding package.
- Outputs: `workspace.recipe` delegates scaffold mechanics to `from enclosure.shared.scaffolding import scaffolding`.
- Scope: `src/enclosure/features/workspace/recipe/` and its tests only.
- Out of scope: pattern catalog, pattern fit, recipe CLI redesign, recipe manifest schema redesign, drift/bench algorithm changes.
- Owner: `workspace.recipe` remains owner of recipe language, reports, drift checks, bench checks, and CLI-facing functions.
- Dependency direction: `workspace.recipe` may import only `scaffolding` and required DTOs/errors from the `enclosure.shared.scaffolding` package root, not internal shared modules.
- Step 02 must treat `shared.scaffolding` as complete. If recipe integration needs new shared behavior, stop and update `UML.md` and Step 01 before continuing.

## Step 01 Handoff

The shared package is stable and sufficient for workspace recipe needs.

Available public seam:

- `scaffolding.load_all(scaffold_root)`
- `scaffolding.load(scaffold_root, name)`
- `scaffolding.parse_variables(values)`
- `scaffolding.compose(scaffold, scaffolds)`
- `scaffolding.render(scaffold, scaffolds, target_root, target_path, variables)`
- `scaffolding.write(rendered_files, create_paths)`
- `Scaffold`
- `RenderedScaffoldFile`
- `ScaffoldError`

Use exported `Scaffold` for recipe-local synthetic composed roles created from
`workspace.recipe.roles_map` strings such as `a+b`. Keep the role string,
report naming, drift/bench classification, skip policy, preview statuses, and
CLI output local to `workspace.recipe`.

# Execution

1. Resolve `scaffold_root` in recipe code from `settings.metadata.recipes_dir`; pass that path into shared calls and do not let shared code import settings.
2. Replace `FileRecipeRepository` usage with `scaffolding.load_all()` and `scaffolding.load()`.
3. Replace recipe include traversal and included input aggregation with `scaffolding.compose()` and `scaffolding.render(..., scaffolds, ...)`.
4. Replace `FileRecipeRenderer.render_files()` usage with `scaffolding.render()`.
5. Replace `FileRecipeMaterializer.write_files()` usage with `scaffolding.write()`.
6. Replace recipe-local `parse_variables()` with `scaffolding.parse_variables()`.
7. Replace recipe-local `normalize_target_path()`, `normalize_rendered_target()`, target defaults, and variable context helpers with shared render behavior.
8. Keep recipe-specific result names such as `RecipeGenerationReport`, `GenerateRecipeResult`, `RecipePreviewFile`, `RecipeDriftReport`, and bench reports.
9. Convert shared `RenderedScaffoldFile` to recipe preview/result structures only at the feature boundary where statuses are applied.
10. Keep recipe `roles_map` composition strings, drift, bench, preview status planning, and architecture module mapping local.
11. Use `Scaffold.ladder.summary()` or `scaffolding.compose()` results for
    drift/bench ladder reads; do not add a shared composed-ladder API.
12. Delete recipe-local duplicate pydantic manifest DTO, YAML reader, repository, renderer, materializer, include traversal, and input aggregation after all call sites move.
13. Remove any compatibility aliases that are not imported by tests, CLI, or another production module.
14. Do not add back-calls from `shared.scaffolding` into recipe code.

# Verification

- Run `uv run pytest tests/features/workspace/recipe`.
- Run `uv run pytest tests/shared/scaffolding tests/features/workspace/recipe`.
- Run `uv run ruff check src/enclosure/features/workspace/recipe tests/features/workspace/recipe`.
- Confirm the existing functional test still covers list, show, check, dry-run, shell preview, generate, bench, and bench-all behavior.
- Use `rg` to confirm `FileRecipeRepository`, `FileRecipeRenderer`, `FileRecipeMaterializer`, `_RecipeManifest`, recipe-local `_load_yaml_mapping`, `_included_recipes_for`, and recipe-local `_input_specs_for` are gone unless a compatibility alias is explicitly justified.
- Confirm `src/enclosure/shared/scaffolding/` still has no imports from `src/enclosure/features/`.
- Confirm `src/enclosure/features/workspace/recipe/` imports only from the
  `enclosure.shared.scaffolding` package root, not internal shared modules.

# Completion

Step 02 is complete when `workspace.recipe` behavior is unchanged, the bounded context imports only the shared package-root API, and deleted recipe-local scaffold code is larger than any new adapter code added for integration.

## Result

Step 02 completed with `workspace.recipe` importing only the
`enclosure.shared.scaffolding` package root. `FileRecipeRepository`,
`FileRecipeRenderer`, `FileRecipeMaterializer`, `_RecipeManifest`,
recipe-local `_load_yaml_mapping`, `_included_recipes_for`,
`_input_specs_for`, path normalization, target defaults, variable context, and
local rendered-file/input/file DTOs were removed.

Verification completed:

- `uv run pytest tests/features/workspace/recipe`
- `uv run pytest tests/shared/scaffolding tests/features/workspace/recipe`
- `uv run ruff check src/enclosure/features/workspace/recipe tests/features/workspace/recipe`
- forbidden dependency and duplicate-symbol `rg` scans
- `uv run enclosure health` after an escalated retry; recipe checks were clean,
  while unrelated baseline workspace rules, recipe drift, and architecture
  findings remained.
