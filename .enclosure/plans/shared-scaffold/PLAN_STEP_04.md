# Implementation Tree

```text
src/enclosure/features/workspace/recipe/
  domain.py
    public compatibility ladder/slot exports audited; remove only if no current
    caller and no public compatibility reason remains
  application.py
    synthetic role and composed ladder logic audited for package-root shared
    scaffolding use only
  __init__.py
    exported recipe compatibility aliases audited and either justified or
    removed
src/enclosure/features/pattern/catalog/
  package-root shared scaffolding imports remain; no local scaffold mechanics
src/enclosure/features/pattern/fit/
  package-root shared scaffolding imports remain; no local scaffold mechanics
.enclosure/recipes/
  generated module templates audited so they do not recreate removed pattern or
  recipe scaffold mechanics
tests/shared/scaffolding/
  public seam and forbidden export tests remain
tests/features/workspace/recipe/
  recipe facade integration and compatibility behavior covered
tests/features/pattern/
  pattern facade integration remains covered
tests/features/shared-scaffold/
  optional guard tests for repo-wide forbidden imports and duplicate scaffold
  mechanics
```

Status: Complete.

Implementation evidence:

- Removed unused `workspace.recipe` public ladder/slot compatibility aliases:
  `RecipeLadder`, `RecipeSlot`, `RecipeSlotName`, `RecipeSlotState`, and
  `RecipeRole`.
- Kept synthetic composed-role handling private to `workspace.recipe.application`
  while still delegating include composition and rendering to package-root
  `enclosure.shared.scaffolding`.
- Added focused guard tests under `tests/features/shared-scaffold/` for feature
  deep imports, shared-to-feature imports, and duplicate scaffold mechanics in
  feature code and `.enclosure/recipes/` templates.
- Confirmed `workspace.plan`, `workspace.sync`, and `workspace.rules` remain
  non-integrations because they do not consume recipe-style scaffold manifests.
- Verification passed:
  `uv run pytest tests/shared/scaffolding tests/features/workspace/recipe tests/features/pattern tests/features/shared-scaffold`
  and `uv run ruff check src tests`.
- `enclosure health` ran; recipe checks were clean and unrelated baseline
  findings remained in workspace rules, recipe drift, architecture shape,
  pressure, coherence, and clusters.

# Goal

Gather and close the remaining shared-scaffold integration questions after Step
03. This step is a final audit and cleanup pass, not a new feature extraction.

The intended end state is explicit: every live manifest-backed scaffold consumer
uses the package-root `enclosure.shared.scaffolding` seam, no feature imports
shared internals, no feature carries local manifest/include/render/write/path
mechanics, and non-scaffold modules that use words like "plan scaffold" or
"write plan" are documented as out of scope.

# Step Contract

- Inputs: completed Step 03 pattern migration and the post-migration full-pass
  audit.
- Outputs: remaining integration questions are resolved or explicitly
  documented; guard tests/scans cover the integration boundary.
- Scope: `workspace.recipe` compatibility aliases and synthetic role helpers,
  pattern package import scans, `.enclosure/recipes/` template scans, focused
  tests, and plan status updates.
- Out of scope: adding shared scaffolding API, changing manifest schema,
  rewriting `workspace.plan` or `workspace.sync`, merging pattern fit/catalog,
  changing command names or CLI output.
- Owner: `shared.scaffolding` owns scaffold mechanics; feature modules own
  reports, statuses, role/catalog policy, drift/bench behavior, CLI language,
  config access, and non-scaffold document/sync writes.
- Dependency direction: features may import only package-root
  `enclosure.shared.scaffolding` exports. Shared scaffolding must not import
  features, settings, or recipe/pattern vocabulary.

## Current Integration Inventory

- `workspace.recipe` is a shared scaffolding consumer. It loads, composes,
  renders, parses variables, and writes through the package-root facade.
- `pattern.catalog` is a shared scaffolding consumer. It loads manifests and
  composes roles through the package-root facade while retaining catalog
  validation/report language.
- `pattern.fit` is a shared scaffolding consumer. It renders and materializes
  through the package-root facade while retaining fit preview statuses/results.
- `.enclosure/recipes/pattern-module` currently contains generic module stubs,
  not the removed pattern manifest/repository/render/write mechanics.
- `workspace.plan` renders a markdown plan document and writes one plan file.
  It is not manifest-backed scaffolding.
- `workspace.sync` writes workspace sync changes and migrates config YAML. It is
  not manifest-backed scaffolding.
- `workspace.rules` parses rule metadata YAML. It is not scaffold manifest
  parsing.

## SSOT Guardrails

- Do not reintroduce feature-local manifest readers, repositories, renderers,
  materializers, include walkers, input aggregators, target normalizers,
  variable context builders, or rendered scaffold DTOs.
- Do not move feature-owned report/status/config behavior into
  `shared.scaffolding`.
- Do not promote private shared DTOs such as `_ScaffoldInput`,
  `_ScaffoldFile`, `_ScaffoldLadder`, or `_ScaffoldSlot` to package-root exports
  just to simplify compatibility cleanup.
- Do not deep-import shared modules from features. Imports matching
  `enclosure.shared.scaffolding.` are violations outside shared tests for the
  package itself.
- Keep `workspace.recipe` compatibility aliases only when they have current
  callers or a documented public compatibility reason. Otherwise remove them in
  the same step that proves tests and CLI output remain stable.

# Execution

1. Run a repo-wide import scan for `enclosure.shared.scaffolding.` deep imports.
2. Run a repo-wide duplicate mechanics scan for old recipe/pattern repository,
   manifest, render, write, include, input, target, and context names.
3. Inspect `workspace.recipe.domain` and `workspace.recipe.__init__` exports:
   `RecipeLadder`, `RecipeSlot`, `RecipeSlotName`, `RecipeSlotState`, and
   `RecipeRole`.
4. If those compatibility types have no current caller and are not required by
   public seam tests, remove them and adjust synthetic composed-role handling to
   use feature-local private report helpers only. Do not add shared exports.
5. If compatibility types remain, add a short test or comment documenting why
   they are public feature vocabulary rather than duplicated scaffold mechanics.
6. Inspect `workspace.recipe.application` synthetic role helpers. They may
   instantiate public `Scaffold`, call `scaffolding.compose()`, and convert
   ladder data into recipe-owned drift/bench reports. They must not walk
   includes or aggregate inputs by hand.
7. Inspect `.enclosure/recipes/` templates and confirm they do not generate
   removed pattern/recipe scaffold mechanics. Update templates only if they
   would regenerate old local manifest/repository/render/write code.
8. Record explicit non-integrations for `workspace.plan`, `workspace.sync`, and
   `workspace.rules`: they are out of scope unless they start consuming
   recipe-style scaffold manifests.
9. Add optional guard tests under `tests/features/shared-scaffold/` if shell
   scans alone are too easy to skip. Keep them focused on forbidden imports and
   duplicate mechanics names.
10. Re-run recipe, pattern, and shared scaffolding tests.
11. Re-run lint.
12. Run `enclosure health` if available and report unrelated baseline findings
    separately from shared-scaffold integration results.

# Verification

- `uv run pytest tests/shared/scaffolding tests/features/workspace/recipe tests/features/pattern`.
- `uv run ruff check src tests`.
- `enclosure health` if available.
- `rg "enclosure\.shared\.scaffolding\." src/enclosure/features` returns no
  feature deep imports.
- `rg "_PatternManifest|_RecipeManifest|FilePatternRepository|FilePatternRenderer|FilePatternMaterializer|FileRecipe|_load_yaml_mapping|included_patterns_for|included_recipes_for|_patterns_for_rendering|_recipes_for_rendering|_input_specs_for|target_defaults|target_context|variable_context|normalize_target|normalize_relative|resolve_input|PatternInputSpec|PatternFile|RenderedPatternFile|RelativePath" src/enclosure/features .enclosure/recipes`
  returns no live duplicate scaffold mechanics except explicitly documented
  non-scaffold config/rules parsing.
- `rg "enclosure\.features" src/enclosure/shared/scaffolding` returns no shared
  dependency on features.
- Current shared consumers are visible through package-root imports only:
  `workspace.recipe`, `pattern.catalog`, and `pattern.fit`.

# Completion

Step 04 is complete when the final audit proves there are no remaining
manifest-backed scaffold integrations outside `shared.scaffolding`, all
remaining compatibility aliases are either removed or justified, templates will
not regenerate removed mechanics, and tests/lint pass.

Step 04 must not begin until this plan is accepted.
