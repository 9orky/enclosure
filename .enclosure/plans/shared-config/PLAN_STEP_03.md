# Step 03: Migrate Remaining Bounded Contexts

Status: Ready to split into migration units after Step 02 completion

## Goal

After Step 02 successfully migrates architecture, integrate the completed
`shared.config` package into the remaining bounded contexts and later allowed
integration surfaces.

This step removes the remaining duplicated config ownership only after the
architecture migration proves the approach.

This step must treat `shared.config` as finished. Do not add new package
capabilities here unless Step 01 is first updated and completed again.

## Current Post-Step-02 State

Architecture has already migrated to `shared.config` and
`src/enclosure/features/architecture/config/` has been deleted. Remaining
imports of `enclosure.features.architecture.config` are therefore broken on
execution and are intentional Step 03 cleanup targets, not Step 02 leftovers.

Known remaining production callers include:

- `src/enclosure/features/workspace/sync/infrastructure.py`
  - imports deleted `enclosure.features.architecture.config`
  - validates generated config with old section-level validators
  - reads `resources/enclosure.yaml`
  - parses YAML while migrating existing config content
- `src/enclosure/features/workspace/rules/application.py`
  - imports deleted `enclosure.features.architecture.config`
  - calls architecture and workspace `load_config()` helpers
- `src/enclosure/features/workspace/config/`
  - owns old `WorkspaceConfig` loading and validation
- `src/enclosure/features/workspace/rules/domain/config.py`
  - owns old rules config classes
- `src/enclosure/features/workspace/recipe/`
  - owns old recipe config classes and raw config loading
- `src/enclosure/features/pattern/`
  - owns old pattern config classes and raw config loading
- `src/enclosure/features/health/`
  - still reads project root through `enclosure.shared.layout`

Known remaining shared/test cleanup callers include:

- `src/enclosure/shared/layout.py`
- `src/enclosure/shared/ui.py`
- `tests/shared/test_architecture_code.py`
- `tests/ui/test_command_docs.py`

These shared and UI test roots are not part of a bounded-context migration unit.
Handle them only in a clearly named later Step 03 cleanup unit whose root
includes the files being edited.

## Source Of Truth

[UML.md](UML.md) is the source of truth for integration boundaries. Step 03 must
strictly follow the caller direction, deleted old ownership, no-bridge rule, and
independence boundary shown in the UML.

If remaining-context integration needs behavior not represented in the UML,
stop, update Step 01 and the UML, complete Step 01 independently, then resume
Step 03.

## Root Boundary

Step 03 is split by migration unit. Each migration unit may edit only its own
root and matching tests.

Allowed production roots:

- `src/enclosure/features/workspace/`
- `src/enclosure/features/pattern/`
- `src/enclosure/features/health/`

Allowed test roots:

- `tests/features/workspace/`
- `tests/features/pattern/`
- `tests/features/health/`

Later shared-helper or packaged-resource cleanup may happen only in a clearly
named Step 03 migration unit whose root is the exact shared or resource root
being cleaned.

Step 03 must not edit:

- `src/enclosure/shared/config/`
- `src/enclosure/features/architecture/`
- tests outside the active migration unit root

If a migration unit appears to require edits outside its root boundary, stop and
create or update the appropriate migration unit instead of mixing roots.

## Integration Boundary

Remaining callers may depend on `shared.config`, but `shared.config` must not
begin depending on remaining callers.

No backwards-compatibility bridges are allowed.

No migrated caller may call a project-root discovery helper, walk upward from
the current working directory, or infer the project root from config paths. Any
code that needs the project root or a common workspace path must read it from
`settings.metadata` and pass that value downward.

## File Tree

Primary bounded-context roots:

- `src/enclosure/features/workspace/`
- `src/enclosure/features/workspace/config/` (delete after workspace callers move)
- `src/enclosure/features/workspace/rules/domain/config.py` (delete after callers move)
- `src/enclosure/features/pattern/`
- `src/enclosure/features/pattern/catalog/domain/config.py` (delete after callers move)
- `src/enclosure/features/health/`

Matching test roots:

- `tests/features/workspace/`
- `tests/features/pattern/`
- `tests/features/health/`

Optional later cleanup units, only when their roots are explicitly active:

- `src/enclosure/shared/`
- `src/enclosure/resources/`
- `tests/shared/`
- `tests/ui/`

## Work Items

- Migrate workspace callers to `from enclosure.shared.config import settings`.
- Migrate pattern callers to `from enclosure.shared.config import settings`.
- Migrate health callers to `from enclosure.shared.config import settings`.
- Prefer the first migration unit to be `workspace/sync`, because it currently
  imports the deleted architecture config package and blocks `workspace sync`.
- Replace remaining section-level config loading with `settings.query("...")` calls inside the active migration root.
- Replace remaining project-root discovery with `settings.metadata.project_root` inside the active migration root.
- Replace standard workspace path construction with metadata paths such as `settings.metadata.plans_dir`, `settings.metadata.recipes_dir`, `settings.metadata.rules_dir`, `settings.metadata.local_rules_dir`, `settings.metadata.cache_dir`, and `settings.metadata.dev_dir`.
- Replace canonical config-path construction with `settings.metadata.canonical_config_path` when the active migration root needs the canonical manifest output path.
- Delete remaining bounded-context config packages and modules after all callers in their root move.
- Remove duplicate `load_config()` functions and repeated config error aliases inside the active migration root.
- Remove section-level config validation inside the active migration root after equivalent shared-config validation is covered by Step 01 tests.
- In the workspace sync migration unit, replace packaged default config template reads with `Manifest.dump_default()`.
- In workspace migration units, replace references to deleted architecture config
  loaders with `settings.query("architecture")` and `settings.metadata`.
- Pattern config data currently lives in `workspace.recipe`; pattern migration
  should query `settings.query("workspace.recipe")`. There is no top-level
  `pattern` section in the root settings graph.
- In the packaged-resource cleanup unit, remove `resources/enclosure.yaml` after workspace sync no longer reads it.
- In the shared-helper cleanup unit, remove `src/enclosure/shared/layout.py` only after all production callers have moved to `settings.metadata` or feature-owned path helpers.
- Update tests inside the active migration unit root.
- Run verification for each migrated root before starting the next root.

## Acceptance

- Remaining migrated callers use `from enclosure.shared.config import settings`.
- Each Step 03 migration unit edits only its declared root boundary.
- Remaining migrated callers use `settings.query("...")` for config data.
- Remaining migrated callers use `settings.metadata.project_root` as the runtime source of project-root truth.
- Remaining migrated callers use metadata path fields instead of recomputing target, plans, recipes, rules, local rules, cache, dev, bootstrap instruction, or agent instruction paths.
- Workspace sync initializes default config content through `Manifest.dump_default()`.
- `resources/enclosure.yaml` is deleted in the packaged-resource cleanup unit.
- No production code imports `enclosure.shared.layout` after the shared-helper cleanup unit.
- `src/enclosure/shared/layout.py` is deleted only in the shared-helper cleanup unit.
- Migrated feature modules do not load raw YAML.
- Migrated feature modules do not validate raw manifest sections directly.
- Old bounded-context config packages and loaders are deleted, not wrapped.
- No backwards-compatibility bridges are introduced.
- `shared.config` remains independent of existing feature modules, bounded-context config modules, and other shared modules/packages.
- Step 03 adds no new `shared.config` capabilities.

## Verification

- [ ] Compare each Step 03 migration unit against [UML.md](UML.md).
- [ ] Run `uv run pytest tests/shared/config`.
- [ ] Run tests for each migrated bounded-context root.
- [ ] Run `uv run pytest tests/features/workspace` after workspace migration.
- [ ] Run `uv run pytest tests/features/pattern` after pattern migration.
- [ ] Run `uv run pytest tests/features/health` after health migration.
- [ ] Run `enclosure workspace health` after workspace migration.
- [ ] Run `enclosure health` after health or shared-helper cleanup.
- [ ] Confirm no migrated production module loads raw YAML directly.
- [ ] Confirm no migrated production module imports deleted bounded-context config modules.
