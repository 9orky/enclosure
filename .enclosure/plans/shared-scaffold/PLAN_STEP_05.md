# Step 05: Config And Scaffolding Leak Remediation

Status: Proposed; do not implement until accepted.

This step is based on two independent architecture scans plus a local
cross-check. It closes SSOT forks and abstraction leaks around
`enclosure.shared.config` and `enclosure.shared.scaffolding` that remained
after Step 04.

## Goal

Make the shared package seams explicit and enforceable:

- `enclosure.shared.scaffolding` owns manifest-backed scaffold mechanics.
- `enclosure.shared.config` owns project config loading, validated settings,
  config metadata, query traversal, and config-derived path semantics.
- Feature modules own feature reports, statuses, CLI language, migration policy,
  document rendering policy, and feature-specific result DTOs.

The expected end state is fewer local wrappers, fewer test-only fake settings,
and guard tests that catch templated regressions as well as concrete source
regressions.

## Step Contract

- Inputs: completed Step 04 integration audit, Architect A config scan, and
  Architect B scaffolding scan.
- Outputs: stale templates fixed, config/scaffolding public seams clarified,
  duplicated config/scaffold mechanics removed or explicitly justified, and
  guard tests expanded.
- Scope: `.enclosure/recipes/pattern-module/`,
  `tests/features/shared-scaffold/`, `src/enclosure/shared/config/`,
  config-consuming feature code and test fixtures, and narrow pattern/recipe
  public helper cleanup.
- Out of scope: changing CLI output, changing recipe/scaffold manifest schema,
  merging pattern fit/catalog, rewriting workspace sync migration behavior, or
  widening shared scaffolding exports.

## Public Seam Decisions

Decide these before editing broad code paths:

1. `shared.scaffolding` remains fixed at package-root exports only:
   `scaffolding`, `Scaffold`, `RenderedScaffoldFile`, and `ScaffoldError`.
2. `shared.config` should expose `settings`, `ConfigError`, and one explicit
   alternate-root factory if tests and commands need settings for a non-current
   project root.
3. Treat `SettingsFacade`, `Manifest`, `ManifestQuery`, and `ConfigMetadata` as
   internal unless Step 05 deliberately promotes one of them through the package
   root.
4. Decide whether config schema classes under `shared.config.architecture` and
   `shared.config.workspace` are a supported schema seam. If they remain public,
   document that as a schema seam separate from the runtime `settings` seam.
5. Do not add root helpers such as `load_project_mapping()`, `section()`, or
   `load_yaml_mapping()` only to satisfy stale templates.

## Violation Inventory

### 1. Pattern-module templates regenerate scaffold mechanics

Evidence:

- `.enclosure/recipes/pattern-module/recipe.yaml:55` through `:70` generates
  `domain/manifest.py`, `infrastructure/manifests.py`, and
  `infrastructure/repository.py`.
- `.enclosure/recipes/pattern-module/templates/domain/manifest.py.tmpl:10`
  defines a generated manifest DTO with `schema_version`, `role`,
  `description`, and `includes`.
- `.enclosure/recipes/pattern-module/templates/infrastructure/manifests.py.tmpl:12`
  loads and validates a scaffold-style manifest.
- `.enclosure/recipes/pattern-module/templates/infrastructure/repository.py.tmpl:9`
  generates `File{{ target.class }}Repository`; `:27` through `:44`
  rediscover manifests and hard-code `recipe.yaml`.

Why this violates SSOT:

Step 04 says templates do not regenerate removed pattern/recipe scaffold
mechanics. These templates still regenerate manifest DTOs, YAML manifest
loading, repository discovery, and manifest filename ownership.

Fixing details:

- Remove `domain/manifest.py`, `infrastructure/manifests.py`, and
  `infrastructure/repository.py` outputs from `pattern-module/recipe.yaml`.
- Delete those templates or replace them with pattern-owned reference/report
  stubs that do not parse recipe manifests.
- If generated pattern modules need scaffold manifests, generate code that
  consumes `from enclosure.shared.scaffolding import scaffolding, Scaffold,
  ScaffoldError` through the package root.
- Add a focused smoke generation test for `pattern-module` proving it does not
  emit local manifest/repository/render/write mechanics.

### 2. Pattern-module templates call stale shared config APIs

Evidence:

- `.enclosure/recipes/pattern-module/templates/infrastructure/config.py.tmpl:9`
  calls `enclosure.shared.config.load_project_mapping()`.
- `.enclosure/recipes/pattern-module/templates/infrastructure/config.py.tmpl:10`
  calls `enclosure.shared.config.section(...)`.
- `.enclosure/recipes/pattern-module/templates/infrastructure/manifests.py.tmpl:13`
  calls `config.load_yaml_mapping(...)`.

Why this violates SSOT:

Those APIs are not in the current package-root `shared.config` seam. Keeping
the template either generates broken code or pressures shared config to expose
raw mapping helpers that bypass validated settings.

Fixing details:

- Replace generated config loading with `from enclosure.shared.config import
  settings` and `settings.query(...)` if the generated module reads project
  settings.
- Do not generate raw YAML mapping loaders for scaffold manifests; use
  `shared.scaffolding`.
- If a generated module needs feature-local config DTOs, convert from the
  validated query result at the feature boundary without calling raw config
  parser helpers.

### 3. Generated feature DTOs subclass shared config internals

Evidence:

- `.enclosure/recipes/pattern-module/templates/domain/config.py.tmpl:5`
  imports `from enclosure.shared import config` and subclasses
  `config.StrictConfigModel`.
- `.enclosure/recipes/pattern-module/templates/domain/manifest.py.tmpl:7`
  does the same for a generated manifest DTO.

Why this violates SSOT:

It makes generated feature/domain code depend on a shared config implementation
base instead of validated shared settings or feature-owned DTOs.

Fixing details:

- Prefer feature-owned dataclasses for generated result/config DTOs.
- If Pydantic is necessary, import Pydantic directly in the generated feature
  module and keep the DTO feature-owned.
- Remove the manifest DTO entirely if violation 1 is fixed by deleting generated
  scaffold manifest files.

### 4. Pattern-module template creates a local render wrapper

Evidence:

- `.enclosure/recipes/pattern-module/templates/infrastructure/templates.py.tmpl:6`
  defines `render_{{ target.snake }}_text()`.
- The wrapper delegates to `templates.render_recipe_template(...)` at `:7`.

Why this violates SSOT:

For manifest-backed scaffolding, shared scaffolding owns render context and file
rendering. A generated feature-local render wrapper is another render seam.

Fixing details:

- Delete the generated render wrapper if it is only for scaffold rendering.
- If generated modules need non-scaffold document rendering, rename it to the
  document/report concern and keep it out of manifest-backed flows.

### 5. Guard tests miss templated duplicate mechanics

Evidence:

- `tests/features/shared-scaffold/test_integration_boundaries.py:13` through
  `:36` searches concrete names such as `FilePatternRepository` and
  `_PatternManifest`.
- The stale templates use templated names such as `File{{ target.class }}Repository`
  and `load_{{ target.snake }}_manifest`, so the guard at `:59` through `:71`
  does not fail.

Why this violates SSOT:

The guard test claims to protect templates from regenerating removed mechanics,
but it is blind to template placeholders.

Fixing details:

- Replace the string-only guard with regex checks over source and templates.
- Add forbidden template patterns for:
  `File{{ target.class }}Repository`, `load_{{ target.snake }}_manifest`,
  `Manifest(config.StrictConfigModel)`, `schema_version`, `recipe.yaml`,
  `render_{{ target.snake }}_text`, and `render_recipe_template`.
- Keep exceptions narrow and documented for non-scaffold YAML/config behavior.

### 6. Tests deep-import config internals

Evidence:

- `tests/features/architecture/support.py:8` and `:9` import
  `SettingsFacade` and `Manifest` from internal modules.
- `tests/features/architecture/test_multi_realm_functional.py:9` and `:10`
  repeat those imports.
- `tests/features/health/report/conftest.py:14` and `:15` repeat those imports.

Why this violates SSOT:

Tests construct settings through private config internals instead of the
package seam. This makes private constructor shape part of the effective public
contract.

Fixing details:

- Add an explicit package-root factory, for example
  `settings_for(project_root: Path)`, if alternate project roots are valid test
  and command behavior.
- Migrate tests to `from enclosure.shared.config import settings_for`.
- If no factory is accepted, centralize the internal construction in one shared
  test helper and document that it is test-only, then avoid duplicating it.

### 7. Tests reimplement settings query and metadata

Evidence:

- `tests/features/workspace/recipe/conftest.py:17` through `:44` defines
  `ProjectSettings`, `ConfigNode`, YAML loading, dot-path traversal, and object
  wrapping.
- `tests/features/workspace/health/conftest.py:15` through `:69` repeats the
  same pattern plus metadata paths and alias handling.
- `tests/features/workspace/rules/conftest.py:13` through `:60` repeats it.
- `tests/features/health/report/conftest.py:19` through `:73` repeats it.

Why this violates SSOT:

These fixtures fork `Manifest`, `ManifestQuery`, `ConfigMetadata`, alias
handling, and tuple/list conversion. They can pass while production settings
would fail.

Fixing details:

- Replace the fake settings objects with real shared config settings built for
  the fixture project.
- Monkeypatch the same feature module `settings` references, but point them at
  the real shared settings facade/factory.
- Keep tests that inspect generated YAML with `yaml.safe_load`; those are output
  assertions, not settings seam replacements.

### 8. Feature-local config wrappers duplicate shared config normalization

Evidence:

- `src/enclosure/shared/config/workspace/recipe.py:19` through `:42`
  normalizes `skip`, `roles_map`, and skip matching.
- `src/enclosure/features/workspace/recipe/domain.py:19` through `:59`
  repeats skip and roles-map normalization in `RecipeGenerationConfig`.
- `src/enclosure/features/workspace/recipe/application.py:836` converts
  `settings.query("workspace.recipe")` into that duplicate feature config.
- `src/enclosure/features/pattern/fit/domain.py:9` through `:25` repeats skip
  normalization in `PatternFitConfig`.

Why this violates SSOT:

Config normalization has two owners. Shared config already validates and
normalizes the workspace recipe config.

Fixing details:

- Consume the validated `settings.query("workspace.recipe")` object directly
  where only shared config fields are needed.
- Keep feature dataclasses only for feature-owned runtime decisions and reports.
- If a feature wrapper remains, remove normalization logic and make the wrapper
  hold a validated shared config object.

### 9. `shared.config.pattern` is feature-specific and unused by root settings

Evidence:

- `src/enclosure/shared/config/pattern/fit.py:8` defines `PatternFitConfig`.
- `src/enclosure/shared/config/root.py:10` through `:12` includes only
  `architecture` and `workspace`.
- Live pattern fit reads `workspace.recipe`, not a top-level `pattern` config.

Why this violates SSOT:

Shared config should model the actual project config schema. An unused
feature-specific schema package is a second possible owner for pattern fit
configuration.

Fixing details:

- Delete `src/enclosure/shared/config/pattern/` unless Step 05 deliberately adds
  a real `.enclosure/enclosure.yaml` `pattern:` section.
- If a `pattern:` section is added, wire it into `EnclosureSettings` and migrate
  pattern code to that single schema.

### 10. Architecture engine details leak into shared config

Evidence:

- `src/enclosure/shared/config/architecture/root.py:3` imports
  `modwire.supported_languages`.
- `src/enclosure/shared/config/architecture/shape.py:5` imports
  `modwire.ShapeConfig`.
- `src/enclosure/shared/config/architecture/shape.py:35` exposes
  `to_modwire_config()`.

Why this violates boundaries:

Shared config parses and validates project configuration. Engine adapter
behavior belongs closer to architecture application/domain code.

Fixing details:

- Move `to_modwire_config()` to an architecture-owned adapter.
- Move `supported_languages()` validation to the architecture command path, or
  wrap it in an architecture-owned validator invoked after config loading.
- Keep shared config fields as plain validated project config values.

### 11. `architecture.root` path semantics are split

Evidence:

- `src/enclosure/shared/architecture_code.py:66` through `:74` expands `~`,
  handles absolute roots, joins relative roots, and resolves the result.
- `src/enclosure/features/workspace/recipe/application.py:1143` through `:1148`
  only joins `project_root / root`.
- `src/enclosure/features/workspace/rules/application.py:287` through `:292`
  compares paths to raw `Path(architecture_root)`.

Why this violates SSOT:

Config-derived path semantics have multiple owners and can disagree for
absolute paths, `~`, or empty roots.

Fixing details:

- Add a single shared config/path helper for resolving `architecture.root`
  against `settings.metadata.project_root`.
- Use that helper in architecture, recipe drift/bench, workspace rules, and
  health code.
- Add tests for relative root, absolute root, `~`, and empty/missing root.

### 12. Workspace sync mirrors config metadata and YAML mapping loading

Evidence:

- `src/enclosure/features/workspace/sync/domain.py:9` through `:18` defines
  `WorkspacePaths` with fields already owned by `ConfigMetadata`.
- `src/enclosure/features/workspace/sync/infrastructure.py:24` through `:34`
  copies metadata field-by-field.
- `src/enclosure/features/workspace/sync/infrastructure.py:174` through `:203`
  parses existing and packaged config mappings.
- `src/enclosure/features/workspace/sync/infrastructure.py:294` through `:310`
  implements another YAML mapping loader.

Why this violates SSOT:

Workspace sync should own migration and merge policy, not duplicate config path
layout or generic config mapping parse semantics.

Fixing details:

- Pass `ConfigMetadata` or a package-root metadata projection directly instead
  of copying into `WorkspacePaths`.
- Extract one shared config raw-mapping loader only if sync migration truly
  requires raw YAML before validated settings are available.
- Keep sync-owned merge/dump formatting local; do not move migration policy into
  shared config.

### 13. Pattern catalog exports helpers that traffic in `Scaffold`

Evidence:

- `src/enclosure/features/pattern/catalog/application/preview.py:10` exports
  `composed_ladder_for(pattern: Scaffold, ...)`.
- `src/enclosure/features/pattern/catalog/application/preview.py:30` exports
  `pattern_for_role(...) -> Scaffold | None`.
- `src/enclosure/features/pattern/catalog/application/preview.py:73` through
  `:76` includes both helpers in `__all__`.
- `src/enclosure/features/pattern/catalog/application/apply.py:11` exposes
  `apply_roles_map(... patterns_by_name: Mapping[str, Scaffold])`.

Why this leaks abstraction:

Pattern public APIs should expose pattern-owned reports, summaries, previews,
or violations. Exported helpers that exchange `Scaffold` widen the feature seam
around shared scaffolding DTO shape.

Fixing details:

- Make these helpers private unless there is a current production caller.
- Prefer one feature-owned validation/report API that hides `Scaffold` behind
  pattern catalog result models.
- Move direct `Scaffold` traffic to private application helpers.

### 14. Recipe package re-exports shared variable parsing

Evidence:

- `src/enclosure/features/workspace/recipe/domain.py:365` aliases
  `parse_variables = scaffolding.parse_variables`.
- `src/enclosure/features/workspace/recipe/__init__.py:25` re-exports the alias.
- `src/enclosure/features/workspace/recipe/__init__.py:141` includes it in
  `__all__`.

Why this leaks abstraction:

This is not duplicated parsing, but it creates a second public route to a shared
scaffolding operation.

Fixing details:

- Remove the feature-level alias if no compatibility caller requires it.
- Have application/UI code call `scaffolding.parse_variables()` directly.
- If compatibility requires keeping it, document it as a compatibility alias and
  add a guard that new shared operations are not re-exported this way.

## Likely Non-Violations Checked

- Live feature imports of `from enclosure.shared.config import settings` are
  valid package-root seam usage.
- No production feature code deep-imports `enclosure.shared.scaffolding.*`.
- `src/enclosure/shared/scaffolding/` imports no `enclosure.features` modules.
- `workspace.sync` YAML merge/dump formatting is sync-owned migration policy;
  only generic mapping load and path metadata duplication need cleanup.
- `workspace.rules` YAML frontmatter parsing is rule metadata behavior, not
  scaffold manifest parsing.
- Pattern and recipe preview DTOs are feature-owned where they add status/report
  behavior around shared rendered files.

## Execution Order

1. Define and document the `shared.config` public seam.
2. Add the package-root alternate-root settings factory if accepted.
3. Migrate test deep imports and fake settings fixtures to the real shared
   config seam.
4. Fix `pattern-module` templates so they stop generating scaffold manifest,
   repository, raw config, and render-wrapper mechanics.
5. Expand shared-scaffold guard tests to catch templated duplicate mechanics.
6. Remove feature config normalization wrappers or reduce them to feature-owned
   behavior only.
7. Delete or justify `shared.config.pattern`.
8. Move modwire adapter behavior out of shared config.
9. Centralize `architecture.root` resolution and migrate callers.
10. Reduce workspace sync metadata/YAML mapping duplication without moving sync
    migration policy.
11. Privatize pattern catalog helpers that expose `Scaffold`.
12. Remove or justify recipe `parse_variables` re-export.

## Verification

- `uv run pytest tests/shared/scaffolding tests/features/shared-scaffold`
- `uv run pytest tests/features/workspace/recipe tests/features/pattern`
- `uv run pytest tests/features/workspace/health tests/features/workspace/rules tests/features/health/report tests/features/architecture`
- `uv run ruff check src tests`
- `rg "enclosure\\.shared\\.scaffolding\\." src/enclosure/features`
- `rg "File\\{\\{ target\\.class \\}\\}Repository|load_\\{\\{ target\\.snake \\}\\}_manifest|Manifest\\(config\\.StrictConfigModel\\)|render_\\{\\{ target\\.snake \\}\\}_text|render_recipe_template" .enclosure/recipes`
- `rg "load_project_mapping|\\.section\\(|load_yaml_mapping" .enclosure/recipes src tests`
- `rg "from enclosure\\.shared\\.config\\.(facade|manifest|query|metadata|root|base)" tests src`
- `rg "parse_variables = scaffolding\\.parse_variables|Mapping\\[[^\\n]*Scaffold|-> Scaffold" src/enclosure/features`

## Completion

Step 05 is complete when stale generators cannot recreate removed mechanics,
shared config and shared scaffolding have explicit package seams, feature/test
code reaches those seams instead of private internals or local fakes, and all
focused tests plus lint pass.
