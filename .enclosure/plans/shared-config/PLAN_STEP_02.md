# Step 02: Migrate Architecture Bounded Context

Status: Ready for implementation after Step 01 verification

## Implementation Tree

- `src/enclosure/shared/architecture_code.py`
  - `extract_architecture_code() -> ArchitectureCodeMap`
  - `_architecture_root(project_root: Path, architecture_config: object) -> Path`
  - `_extraction_exclusions(architecture_config: object) -> tuple[str, ...]`
  - `_matching_config(architecture_config: object) -> object`
- `src/enclosure/features/architecture/config/` (delete)
  - `__init__.py` (delete)
  - `domain.py` (delete)
  - `infrastructure.py` (delete)
- `src/enclosure/features/architecture/boundaries/domain.py`
  - remove `BoundaryRule`, `ConfigTagRule`, `FlowRealmRule`, `FlowRuleSet`, and
    `BoundariesConfig` config ownership after callers move to shared config
  - keep `BoundariesReport`
- `src/enclosure/features/architecture/clusters/domain.py`
  - remove `ClustersConfig` config ownership after callers move to shared config
  - keep report and cluster domain types
- `src/enclosure/features/architecture/health/domain.py`
  - remove `HealthConfig` config ownership after callers move to shared config
  - keep report and finding domain types
- `src/enclosure/features/architecture/map/domain.py`
  - remove `MapConfig` config ownership after callers move to shared config
  - keep report, dependency, and map domain types
- `src/enclosure/features/architecture/pressure/domain.py`
  - remove `PressureConfig` config ownership after callers move to shared config
  - keep report and pressure domain types
- `src/enclosure/features/architecture/shape/domain.py`
  - remove `ImportCrossingType`, `ShapeConfigError`, and `ShapeConfig` config
    ownership after callers move to shared config
  - keep `ShapeViolation`, `ShapeReport`, and shape evaluation functions
- `src/enclosure/features/architecture/*/__init__.py`
  - remove exports that expose deleted architecture-owned config classes
- `tests/features/architecture/`
  - update tests to construct or patch architecture inputs through
    `enclosure.shared.config.settings`, `settings.metadata`, and
    `settings.query("architecture...")`

## Goal

Integrate the completed `shared.config` package from Step 01 into the
architecture bounded context and its current extraction helper.

This step is the pilot migration. It proves that architecture callers can use
`settings`, `settings.query("architecture...")`, and `settings.metadata` without
changing any other bounded context.

This step must treat `shared.config` as finished. Do not add new package
capabilities here unless Step 01 is first updated and completed again.

## Step Contract

Inputs:

- A completed and verified Step 01 `src/enclosure/shared/config/` package.
- [UML.md](UML.md), which is the source of truth for integration boundaries.
- Existing architecture production code and tests under the roots below.

Outputs:

- Architecture runtime config access goes through
  `from enclosure.shared.config import settings`.
- Architecture config data is read with `settings.query("architecture")` or
  narrower `settings.query("architecture...")` calls.
- Architecture project-root and standard path access comes from
  `settings.metadata`.
- Old architecture-owned config loaders and pydantic config classes are removed
  from the declared Step 02 roots instead of wrapped.

Scope:

- Replace config loading and project-root ownership for the architecture bounded
  context only.
- Update architecture tests only where they cover this migration.
- Keep architecture reports, analyzers, templates, and command semantics
  otherwise unchanged.

Out of scope:

- Adding or changing `shared.config` capabilities.
- Migrating workspace, pattern, health, other shared-helper, CLI, or
  packaged-resource callers outside the declared Step 02 roots.
- Removing `enclosure.shared.layout`; that is a Step 03 shared-helper cleanup
  unit after remaining callers move.
- Adding backwards-compatible imports, bridge modules, or compatibility aliases.

Owner:

- `src/enclosure/features/architecture/`
- `tests/features/architecture/`
- The shared helper file `src/enclosure/shared/architecture_code.py` is the only
  allowed non-architecture source edit because it is the current architecture
  extraction entry point and imports architecture config directly.

Dependency direction:

- Architecture callers may depend on `enclosure.shared.config`.
- `enclosure.shared.config` must not depend on architecture callers.
- Downstream architecture functions receive the already-loaded architecture
  config object and metadata-derived paths; they must not load raw YAML,
  validate manifest sections, or rediscover project root.

Stop conditions:

- If architecture integration needs missing `shared.config` behavior, stop,
  update Step 01 and [UML.md](UML.md), complete Step 01 independently, then
  resume Step 02.
- If work requires edits outside the roots declared here, stop and move that
  work to Step 03 or to the owning step.

## Execution

1. Verify the Step 01 prerequisite before editing architecture.
   - Run `uv run pytest tests/shared/config`.
   - Confirm `settings.query("architecture")`,
     `settings.metadata.project_root`, and
     `settings.metadata.canonical_config_path` exist.
2. Replace the architecture extraction entry point.
   - In `src/enclosure/shared/architecture_code.py`, import `settings` from
     `enclosure.shared.config`.
   - Replace `config.load_project_mapping()` and
     `ArchitectureConfig.validate_mapping(...)` with
     `settings.metadata.project_root`,
     `settings.metadata.canonical_config_path`, and
     `settings.query("architecture")`.
   - Keep `ArchitectureCodeMap.report_fields()` output shape stable; derive
     `config_format` from `settings.metadata.canonical_config_path`.
   - Replace the cache root with `settings.metadata.cache_dir / "modwire"`.
3. Remove architecture-owned config classes.
   - Delete `src/enclosure/features/architecture/config/`.
   - Remove config classes from architecture domain modules after all local
     callers/tests import the equivalent shared-config classes or use simple
     non-pydantic test doubles.
   - Remove config class exports from architecture package `__init__.py` files.
4. Update architecture tests.
   - Replace imports from `enclosure.features.architecture.config.*` with
     `enclosure.shared.config` or shared config class imports where direct class
     construction is still useful.
   - Replace `current_project_root` and raw config loader patches with
     patches/fixtures around `settings.metadata` and
     `settings.query("architecture...")`.
   - Move invalid architecture config-section validation expectations to
     `tests/shared/config` if Step 01 does not already cover them.
5. Scan for forbidden remnants inside architecture.
   - No imports from `enclosure.features.architecture.config`.
   - No `load_project_mapping()`, section-level `validate_mapping(...)`, raw
     YAML parsing, or `current_project_root` use in architecture code.
   - No architecture-owned pydantic config classes remain in architecture
     production modules.
6. Run architecture-focused verification.

## Verification

- [ ] Compare Step 02 architecture integration against [UML.md](UML.md).
- [ ] Run `uv run pytest tests/shared/config`.
- [ ] Run architecture tests affected by config migration.
- [ ] Run `uv run pytest tests/features/architecture`.
- [ ] Run `enclosure architecture boundaries`.
- [ ] Run `enclosure architecture shape`.
- [ ] Run `enclosure architecture health`.
- [ ] Run `rg -n "features\\.architecture\\.config|load_project_mapping|validate_mapping\\(|current_project_root|yaml\\.safe_load|from enclosure\\.shared import config" src/enclosure/features/architecture tests/features/architecture src/enclosure/shared/architecture_code.py` and confirm no forbidden production remnants.

## Completion

Step 02 is complete when:

- Architecture production callers use `from enclosure.shared.config import settings`
  where runtime config is needed.
- Architecture integration strictly follows [UML.md](UML.md).
- Architecture edits stay inside the declared Step 02 root boundary.
- Architecture callers use `settings.query("architecture...")` for architecture config data.
- Architecture callers use `settings.metadata.project_root` as the runtime source of project-root truth.
- Architecture callers use `settings.metadata.canonical_config_path` when the canonical manifest output path is needed.
- Architecture callers do not rediscover, infer, or resolve the project root independently.
- Architecture feature modules do not load raw YAML.
- Architecture feature modules do not validate raw manifest sections directly.
- `src/enclosure/features/architecture/config/` is deleted, not wrapped.
- Architecture-owned pydantic config classes are removed from architecture
  production modules after equivalent Step 01 classes exist.
- No backwards-compatibility bridges are introduced.
- `shared.config` remains independent of architecture and other feature modules.
- Step 02 adds no new `shared.config` capabilities.
- Verification checklist passes or any remaining failures are documented as
  unrelated pre-existing failures.
