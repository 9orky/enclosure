# Implementation Tree

```text
src/enclosure/features/workspace/recipe/
  domain.py
    recipe-specific report and bench dataclasses remain
    recipe-local duplicates of scaffold models removed or aliased only where public compatibility requires it
  infrastructure.py
    recipe manifest repository/render/materializer duplicate code removed
    thin calls to the imported `scaffolding` facade retained only if application imports need a local seam
  application.py
    RecipeService uses shared load/render/write/parse behavior
    recipe drift, bench, show, list, check, and CLI-facing result behavior preserved
  __init__.py
    public recipe API remains stable
tests/features/workspace/recipe/
  test_functional.py
```

# Goal

Integrate one bounded context as proof. Use `workspace.recipe` because it has the strongest current behavior surface and tests.

The goal is not just to call the shared package. The goal is measurable code and complexity reduction: delete recipe-local manifest parsing, repository discovery, rendering, materializer, relative path normalization, target context, defaults, and variable parsing where the shared package now owns them.

# Step Contract

- Inputs: completed Step 01 shared scaffolding package.
- Outputs: `workspace.recipe` delegates scaffold mechanics to `from enclosure.shared.scaffolding import scaffolding`.
- Scope: `src/enclosure/features/workspace/recipe/` and its tests only.
- Out of scope: pattern catalog, pattern fit, recipe CLI redesign, recipe manifest schema redesign, drift/bench algorithm changes.
- Owner: `workspace.recipe` remains owner of recipe language, reports, drift checks, bench checks, and CLI-facing functions.
- Dependency direction: `workspace.recipe` may import only `scaffolding` and required DTOs/errors from `enclosure.shared.scaffolding`, not `facade.py`, `domain.py`, `manifest.py`, `context.py`, `render.py`, `write.py`, or `errors.py`.
- Step 02 must treat `shared.scaffolding` as complete. If recipe integration needs new shared behavior, stop and update `UML.md` and Step 01 before continuing.

# Execution

1. Replace `FileRecipeRepository` usage with `scaffolding.load_all()` and `scaffolding.load()`.
2. Replace `FileRecipeRenderer.render_files()` usage with `scaffolding.render()`.
3. Replace `FileRecipeMaterializer.write_files()` usage with `scaffolding.write()`.
4. Replace recipe-local `parse_variables()` with `scaffolding.parse_variables()`.
5. Replace recipe-local `normalize_target_path()`, `normalize_rendered_target()`, target defaults, and variable context helpers with shared render behavior.
6. Keep recipe-specific result names such as `RecipeGenerationReport`, `GenerateRecipeResult`, `RecipePreviewFile`, `RecipeDriftReport`, and bench reports.
7. Convert shared `RenderedScaffoldFile` to recipe preview/result structures only at the feature boundary where statuses are applied.
8. Keep recipe include composition, drift, and bench logic local if it depends on recipe role semantics or architecture module mapping.
9. Delete recipe-local duplicate pydantic manifest DTO and YAML loader after all call sites move.
10. Remove any compatibility aliases that are not imported by tests, CLI, or another production module.
11. Do not add back-calls from `shared.scaffolding` into recipe code.

# Verification

- Run `uv run pytest tests/features/workspace/recipe`.
- Run `uv run pytest tests/shared/scaffolding tests/features/workspace/recipe`.
- Confirm the existing functional test still covers list, show, check, dry-run, shell preview, generate, bench, and bench-all behavior.
- Use `rg` to confirm `FileRecipeRepository`, `FileRecipeRenderer`, `FileRecipeMaterializer`, `_RecipeManifest`, and recipe-local `_load_yaml_mapping` are gone unless a compatibility alias is explicitly justified.
- Confirm `src/enclosure/shared/scaffolding/` still has no imports from `src/enclosure/features/`.

# Completion

Step 02 is complete when `workspace.recipe` behavior is unchanged, the bounded context imports only the shared package-root API, and deleted recipe-local scaffold code is larger than any new adapter code added for integration.
