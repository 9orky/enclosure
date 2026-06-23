# Step 02: Integrate Shared Config

Status: Draft

## Goal

Integrate the completed `shared.config` package from Step 01 into existing enclosure callers.

This step must treat `shared.config` as finished. Do not add new package capabilities here unless Step 01 is first updated and completed again.

## Source Of Truth

[UML.md](UML.md) is the source of truth for Step 02 integration boundaries. Integration must strictly follow the caller direction, deleted old ownership, no-bridge rule, and independence boundary shown in the UML.

If integration needs behavior not represented in the UML, stop and update Step 01 and the UML before coding.

## Integration Boundary

Step 02 may edit existing feature modules, shared helpers, tests, and CLI flows.

Step 02 must not weaken the Step 01 independence contract. Existing callers may depend on `shared.config`, but `shared.config` must not begin depending on existing callers.

No backwards-compatibility bridges are allowed.

If integration reveals a missing `shared.config` capability, stop Step 02, update and complete Step 01 independently, then resume integration.

## File Tree

- src/enclosure/features/architecture/config/
- src/enclosure/features/workspace/config/
- src/enclosure/features/workspace/rules/domain/config.py
- src/enclosure/features/workspace/recipe/domain.py
- src/enclosure/features/workspace/sync/domain.py
- src/enclosure/features/pattern/catalog/domain/config.py
- src/enclosure/features/pattern/fit/domain.py
- src/enclosure/shared/architecture_code.py
- tests/shared/
- tests/features/

## Work Items

- Replace existing config imports with `from enclosure.shared.config import settings`.
- Replace section-level config loading with `settings.manifest` queries.
- Delete `src/enclosure/features/architecture/config/` after all callers move.
- Delete `src/enclosure/features/workspace/config/` after all callers move.
- Delete nested bounded-context config class definitions after confirming their replacements already exist in the completed Step 01 package.
- Remove duplicate `load_config()` functions and repeated config error aliases.
- Remove `config.section(...)` only if no internal shared-config implementation still needs it.
- Update tests that previously validated independent sections to validate the shared root graph and focused nested validators.
- Update CLI and report code to use metadata exposed by `settings` if needed.
- Run full relevant verification.

## Acceptance

- Existing callers use `from enclosure.shared.config import settings`.
- Integration strictly follows [UML.md](UML.md).
- No existing feature module loads raw YAML.
- No existing feature module validates raw manifest sections directly.
- Old bounded-context config packages and loaders are deleted, not wrapped.
- No backwards-compatibility bridges are introduced.
- `shared.config` remains independent of existing feature modules, bounded-context config modules, and other shared modules/packages.
- Step 02 adds no new `shared.config` capabilities.
- Code reduction opportunities from removed duplicate config paths are applied.

## Verification

- [ ] Run tests for features migrated from bounded-context config imports.
- [ ] Compare Step 02 integration against [UML.md](UML.md).
- [ ] Run tests that cover invalid manifests and fail-fast behavior.
- [ ] Run `uv run pytest tests/shared/test_config.py`.
- [ ] Run `enclosure health`.
- [ ] Run `enclosure workspace health` if workspace files changed.
- [ ] Run `enclosure architecture boundaries`.
- [ ] Run `enclosure architecture shape`.
- [ ] Run `enclosure architecture health` if architecture-sensitive code changed.
