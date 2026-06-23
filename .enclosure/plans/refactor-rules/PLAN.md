# Workspace Recipe Refactor Plan

Status: Draft

Refactor `workspace/recipe` toward the target schema described by [UML.md](UML.md). This document is the big-picture execution plan; [UML.md](UML.md) contains only the target file tree and UML schema.

## Execution Frame

- Target module: `src/enclosure/features/workspace/recipe`
- Current owner: `workspace/recipe`
- Target design: split the oversized application file into explicit domain, infrastructure, application, and UI responsibilities.
- Migration choice: in-place refactor with temporary compatibility only where needed to preserve the package facade during movement.
- Verification seam: package facade imports plus `enclosure workspace recipe` CLI behavior.

## Portability Contract

- Do not hard-code the repository language, source root, feature root, architecture root, layer names, module depth, path separators, or Enclosure's own module layout into recipe logic.
- Treat project structure as data supplied by workspace settings, recipe manifests, role mappings, ladder metadata, and discovered filesystem facts.
- Keep any relation to this repository's current layout inside adapters, fixtures, command defaults, or documentation examples; application and domain code must consume explicit configuration or discovery results.
- Do not infer behavior from path strings such as `src/enclosure/features`, `architecture/*`, `workspace/*`, `domain.py`, `application.py`, `infrastructure.py`, or `ui/cli.py` unless those strings came from the active workspace contract.
- Model paths as configured workspace locations, not as Python package assumptions. A recipe target may currently render Python files, but recipe analysis must not assume Python is the only language or that Enclosure's feature architecture is the only shape.
- Treat UML names such as `Location`, `WorkspaceRelations`, `RecipePolicy`, and `subject_root` as portability boundaries. Implementations may map them to existing project types, but must not replace them with hard-coded Enclosure source-tree or architecture constants.

## Testing Contract

- Implement only functional tests that exercise public seams, CLI behavior, or real filesystem-backed workspace fixtures.
- Do not use mocks, monkey patching, or patched globals to fake settings, filesystem behavior, recipe loading, or scaffolding behavior.
- Test portability by constructing fixture workspaces with real config, recipes, role mappings, and files instead of replacing collaborators at runtime.

## Contract References

- Target file tree: [UML.md#target-file-tree](UML.md#target-file-tree)
- UML schema: [UML.md#uml-schema](UML.md#uml-schema)

## Phases

### Phase 1: Characterization

Objective: freeze current behavior before movement.

Owner: test suite.

Inputs: current CLI behavior, package facade exports, current report dataclasses, `.enclosure/recipes`, `workspace.recipe.roles_map`.

Outputs: focused functional characterization tests under `tests/features/workspace/recipe/`.

Acceptance: functional tests cover list/show/check/drifts/dry-run/generate/bench/bench-all and package facade imports without mocks or monkey patching.

### Phase 2: Infrastructure Extraction

Objective: isolate settings, scaffolding, filesystem, and configured workspace-relation access behind `infrastructure.py`.

Owner: infrastructure layer.

Inputs: direct calls to `settings`, architecture-root helpers, `scaffolding`, filesystem APIs, and `scaffolding.write`.

Outputs: a concrete workspace adapter with no UI imports, no application policy, and no hard-coded relation to Enclosure's current language or architecture layout.

Acceptance: application code can be tested with adapter-level seams; CLI behavior is unchanged.

Portability check: application tests can exercise drift and bench behavior using fixture workspace relations that do not match Enclosure's own source tree.

### Phase 3: Catalog And Generation Services

Objective: split catalog validation/composition from preview/generate/check orchestration.

Owner: application layer.

Inputs: `_RecipeGenerationService` list/show/check/describe/generate paths, catalog validation helpers, sample-variable helpers.

Outputs: `application/catalog.py`, `application/generation.py`, and public read/write facade functions in `queries.py` and `commands.py`.

Acceptance: public `list_recipes`, `show_recipe`, `check_recipes`, `describe_recipe_generation`, and `generate_recipe` return the same domain objects and dict shapes as before.

### Phase 4: Drift And Bench Services

Objective: split mapped-target drift and bench analysis into cohesive services.

Owner: application layer.

Inputs: current `drifts`, `bench`, `bench_all`, recurrence, classification, content-weight, and actual-file helpers.

Outputs: `application/drift.py` and `application/bench.py`.

Acceptance: public `check_recipe_drifts`, `bench_preview`, and `bench_all_preview` preserve current report values for the same workspace without assuming Enclosure's own source tree, feature depth, or language.

### Phase 5: UI Presentation Extraction

Objective: move bench HTML rendering out of application into `ui/bench_html.py`.

Owner: UI layer.

Inputs: `_render_bench_html`, `_render_bench_all_html`, CSS, HTML escaping, table/summary helpers.

Outputs: UI-owned HTML presenter called by `ui/cli.py`; application no longer imports `html` for presentation rendering.

Acceptance: `--bench --html` and `--bench-all --html` still write equivalent reports and still fail on report violations.

### Phase 6: Public Seam Cleanup

Objective: keep external imports stable while removing temporary compatibility code.

Owner: package seam.

Inputs: `recipe/__init__.py`, `application/__init__.py`, old `application.py` imports.

Outputs: lazy package facade, stable `__all__`, no old monolithic `application.py` once call sites are migrated.

Acceptance: repository call sites import through the facade or the new application package without boundary violations.

## Acceptance

- `src/enclosure/features/workspace/recipe/application.py` is removed or reduced to a temporary shim that is deleted before handoff.
- `workspace/recipe` remains mapped to `module-workspace-cli` unless implementation proves the recipe role itself is stale.
- No UI code imports infrastructure directly.
- Domain has no imports from application, infrastructure, or UI.
- No application or domain code contains hard-coded Enclosure source roots, architecture paths, layer filenames, language assumptions, or module-depth assumptions.
- Workspace relations used by drift, bench, and generation are sourced from configuration, recipe manifests, role mappings, ladder metadata, or filesystem discovery.
- `enclosure workspace recipe --check` and `enclosure workspace recipe --drifts` preserve current semantics.
- `enclosure workspace recipe --bench workspace/recipe --html <path>` and `--bench-all --html <path>` still write HTML reports.
- Existing package facade exports remain import-compatible.

## Verification

Run these after each material phase:

```text
uv run pytest tests/features/workspace/recipe tests/shared/scaffolding/test_scaffolding.py
uv run ruff check src/enclosure/features/workspace/recipe tests/features/workspace/recipe
uv run enclosure workspace recipe --check
uv run enclosure workspace recipe --drifts
uv run enclosure architecture boundaries
uv run enclosure architecture shape
uv run enclosure health
```

Run these before final handoff:

```text
uv run enclosure workspace recipe --bench workspace/recipe --html .enclosure/.cache/reports/workspace-recipe-bench.html
uv run enclosure workspace recipe --bench-all --html .enclosure/.cache/reports/workspace-recipe-bench-all.html
```

## Open Questions

- Should bench HTML rendering remain an application-returned string for the package API, or should only the CLI expose HTML rendering?
- Should `RecipeGenerationReport` and `GenerateRecipeResult` remain `TypedDict`, or should they become frozen dataclasses during the refactor?
- Should repeated bench vocabulary such as `warp`, `residue`, and `slot growth` become domain enums before moving classification logic?
