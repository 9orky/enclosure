# Shared Config

Status: Draft

## File Tree

- src/enclosure/shared/config/
- src/enclosure/shared/config/__init__.py
- src/enclosure/shared/config/facade.py
- src/enclosure/shared/config/query.py
- src/enclosure/shared/config/base.py
- src/enclosure/shared/config/errors.py
- src/enclosure/shared/config/metadata.py
- src/enclosure/shared/config/loader.py
- src/enclosure/shared/config/loaded_manifest.py
- src/enclosure/shared/config/root.py
- src/enclosure/shared/config/architecture/
- src/enclosure/shared/config/architecture/root.py
- src/enclosure/shared/config/architecture/boundaries.py
- src/enclosure/shared/config/architecture/tag.py
- src/enclosure/shared/config/architecture/boundary_rule.py
- src/enclosure/shared/config/architecture/flow.py
- src/enclosure/shared/config/architecture/clusters.py
- src/enclosure/shared/config/architecture/health.py
- src/enclosure/shared/config/architecture/map.py
- src/enclosure/shared/config/architecture/pressure.py
- src/enclosure/shared/config/architecture/shape.py
- src/enclosure/shared/config/workspace/
- src/enclosure/shared/config/workspace/root.py
- src/enclosure/shared/config/workspace/guidance.py
- src/enclosure/shared/config/workspace/recipe.py
- src/enclosure/shared/config/workspace/rules.py
- src/enclosure/shared/config/workspace/sync.py
- src/enclosure/shared/config/pattern/
- src/enclosure/shared/config/pattern/fit.py
- src/enclosure/shared/config/health/
- tests/shared/config/

## Problem Or Goal

Create `enclosure.shared.config` as an independent package with a thin public API. It becomes the sole owner of config pydantic classes, manifest loading, whole-graph validation, and dot-notation manifest querying.

The public API is:

```python
from enclosure.shared.config import settings
```

`settings` is a facade class instance. Callers query config data through `settings.manifest` using dot notation. The value behind a selected attribute can be a scalar, pydantic object, list, tuple, or nested query object depending on what the key points to.

The design fails fast and fails loud. Manifest loading, graph assembly, and pydantic validation happen before consumers get useful config data. Invalid manifest input fails immediately with a clear error instead of letting downstream modules recover from partial config.

## Source Of Truth

[UML.md](UML.md) is the source of truth for implementation. Implementers must strictly follow the package layout, class names, relationships, public seam, step boundary, and independence rules shown there.

If the text plan and UML conflict, stop and update the documents before coding. Do not silently choose one interpretation during implementation.

## Independence Rule

`shared.config` is completed before integration starts.

Step 01 must build a ready standalone package. During that step, `src/enclosure/shared/config/` must not import existing enclosure feature modules, existing bounded-context config modules, or other shared modules/packages. It may use the Python standard library plus direct third-party dependencies required for this package, such as `pydantic` and `yaml`.

No module inside `shared.config` may know anything about existing features and modules as part of Step 01. Existing feature integration happens only in Step 02.

Step 02 must not add missing `shared.config` capabilities. If integration discovers that the package is incomplete, return to Step 01, complete the package independently, then resume Step 02.

## Target Users Or Callers

Step 01 target is the standalone `shared.config` package and its tests.

Step 02 target callers are existing enclosure modules that need runtime configuration:

- `architecture.*` features that consume architecture config.
- `workspace.*` features that consume workspace config.
- pattern and health callers that read config data.
- shared helpers such as `architecture_code`.
- tests and CLI commands that need validated config data.

Callers should not import config models from bounded contexts after Step 02. They should import `settings` from `enclosure.shared.config` and query the validated graph through the manifest facade.

## Proposed Module Ownership

`src/enclosure/shared/config/` owns:

- all config pydantic classes needed for the manifest graph;
- topic subpackages for config classes, including `architecture`, `workspace`, `pattern`, and `health`;
- concise module names inside those subpackages without a redundant `config` suffix;
- manifest discovery and YAML loading implemented independently of existing enclosure modules;
- whole-graph pydantic validation;
- the `settings` facade instance;
- dot-notation manifest traversal;
- config errors.

Bounded contexts such as `architecture.config`, `workspace.config`, `workspace.rules.domain.config`, and `pattern.catalog.domain.config` no longer own config classes or config loading after Step 02. Their config code should be deleted after equivalent replacements already exist in the completed Step 01 package.

## Public Seam

The public seam is intentionally thin:

```python
from enclosure.shared.config import settings
```

Required behavior:

- `settings` is a singleton facade class instance.
- `settings.manifest` exposes the validated config graph through dot notation.
- Attribute traversal may return scalars, pydantic objects, lists, tuples, or nested query objects.
- Missing attributes raise `AttributeError`.
- Config loading and validation failures raise loud config errors before useful settings access succeeds.

The public seam should not expose:

- dict-style manifest access;
- generic `.get(...)` fallback access;
- bounded-context config loaders;
- backwards-compatible config bridges;
- raw YAML parsing helpers as caller-facing API.

## Private Internals

Private implementation details should include:

- independent manifest path discovery and YAML loading;
- top-level mapping validation;
- whole-manifest pydantic validation into a root settings model;
- dot-notation object wrapping for validated graph traversal;
- manual declaration of every config class inside `shared.config`;
- error wrapping that reports unreadable manifests, invalid YAML, wrong top-level shape, and pydantic validation failures clearly.

Do not add backwards-compatibility bridges. The migration removes old config ownership rather than wrapping it.

## Expected Layers

- Domain: config error types, strict model base, topic subpackages for pydantic config classes, root settings model, dot-notation query object, facade class.
- Infrastructure: independent manifest discovery and YAML file loading.
- Application: the exported `settings` instance that coordinates load, validation, and manifest access.
- UI: absent.

## Inputs, Outputs, And Data

Inputs:

- `.enclosure/enclosure.yaml` or `.enclosure/enclosure.yml`.
- Manually declared config pydantic classes inside `shared.config`.

Outputs:

- A validated root pydantic config object for the whole config graph.
- `settings.manifest`, a dot-notation query surface over the validated graph.
- Stable project root and config path metadata if callers need them after integration.

Data behavior:

- Existing manifest schema should remain valid unless whole-graph validation reveals a real validation defect.
- Existing nested config defaults should remain effective.
- No partial or best-effort config should be exposed after load or validation failure.
- Missing dot-notation attributes raise `AttributeError`.

## Dependencies

Allowed in Step 01:

- Python standard library.
- `pydantic` for whole-graph validation.
- `yaml` through the existing PyYAML dependency.

Avoid in Step 01:

- Imports from existing enclosure feature modules.
- Imports from existing bounded-context config modules.
- Imports from other `enclosure.shared.*` modules.
- Dynamic plugin registration or discovery.

Avoid in all steps:

- Feature modules loading raw YAML directly.
- Feature modules calling section-level validators after migration.
- Manifest access through dictionaries, key strings, or fallback-heavy generic getters.

## Recipe Or Scaffold

Use the existing compact config-support shape only as a loose reference. The implementation itself should be independent and package-shaped rather than a feature module:

- no command UI;
- thin `__init__.py`;
- internal support modules;
- topic subpackages for config classes.

Because `src/enclosure/shared` is outside `architecture.root`, follow shared package style while keeping Step 01 independent from existing enclosure feature and shared modules.

## Design Artifacts

- [Shared config UML](UML.md)
- [Step 01](PLAN_STEP_01.md)
- [Step 02](PLAN_STEP_02.md)

## Phases

Phase 1: Complete standalone `shared.config`.

Owner: `src/enclosure/shared/config/`.
Inputs: manifest schema requirements and standalone tests.
Outputs: a ready `shared.config` package with config classes, independent manifest loading, whole-graph validation, `settings`, and dot-notation manifest querying.
Acceptance: `shared.config` is complete after this phase and imports no existing enclosure feature modules, bounded-context config modules, or other shared modules/packages.

Phase 2: Integrate the completed package.

Owner: existing feature modules, shared helpers, tests, and CLI callers.
Inputs: completed Step 01 package.
Outputs: all existing config callers use `from enclosure.shared.config import settings`; bounded-context config ownership is removed; duplicate loader and section-validation code is deleted.
Acceptance: no compatibility bridges are introduced, integration does not change the standalone ownership rules established in Step 01, and Step 02 does not add new `shared.config` capabilities.

## Code Reduction Opportunities

- Delete `src/enclosure/features/architecture/config/` after moving `ArchitectureConfig` into `shared.config.architecture`.
- Delete `src/enclosure/features/workspace/config/` after moving `WorkspaceConfig` and nested workspace config ownership into `shared.config.workspace`.
- Delete nested config modules such as `workspace.rules.domain.config` and `pattern.catalog.domain.config` after their classes exist in the completed Step 01 package.
- Replace duplicate `load_config()` functions with the single `settings` facade.
- Remove `config.section(...)` if no internal shared-config implementation still needs section-level validation.
- Collapse repeated `ConfigError` aliases into one shared error type.
- Simplify tests that separately validate architecture and workspace config sections by validating the full root graph once and adding focused tests for nested validators.
- Reduce import forwarding in bounded-context `__init__.py` files that only re-export config classes.

## Acceptance

- `shared.config` is a package, not a single module.
- Implementation strictly follows [UML.md](UML.md).
- Step 01 completes `shared.config` as an independent ready solution.
- During Step 01, `shared.config` imports no existing enclosure feature modules, bounded-context config modules, or other shared modules/packages.
- `shared.config` owns all config pydantic classes needed for the manifest graph.
- Config classes are grouped under topic subpackages such as `architecture`, `workspace`, `pattern`, and `health`.
- Module names inside those subpackages omit redundant `config` suffixes.
- `shared.config` loads the whole manifest and validates the full config graph through pydantic.
- `from enclosure.shared.config import settings` is the public API.
- `settings` is a facade class instance.
- `settings.manifest` is queryable by dot notation.
- Dot-notation queries can return scalar values, config objects, lists, tuples, or nested query objects.
- Missing dot-notation attributes raise `AttributeError`.
- Loading or validation failures fail fast and fail loud.
- Step 02 integrates the completed package without backwards-compatibility bridges.
- Step 02 does not add new `shared.config` capabilities; missing package capability sends the work back to Step 01.
- Bounded-context config classes and loaders are removed during integration.
- Code reduction opportunities are applied where directly unlocked by the migration.

## Verification Checklist

- [ ] Run Step 01 standalone shared config tests.
- [ ] Compare implementation against [UML.md](UML.md).
- [ ] Confirm `src/enclosure/shared/config/` imports no existing enclosure feature modules, bounded-context config modules, or other shared modules/packages.
- [ ] Run shared config tests covering root graph validation and manifest dot-notation queries.
- [ ] Run tests for features migrated from bounded-context config imports.
- [ ] Run tests that cover invalid manifests and fail-fast behavior.
- [ ] Run `uv run pytest tests/shared/test_config.py`.
- [ ] Run `enclosure health`.
- [ ] Run `enclosure workspace health` if workspace files changed.
- [ ] Run `enclosure architecture boundaries`.
- [ ] Run `enclosure architecture shape`.
- [ ] Run `enclosure architecture health` if architecture-sensitive code changed.

## Open Questions

- Should `settings.manifest` wrap pydantic models directly, or should it expose a separate query wrapper over `model_dump()` output while preserving object and list returns?
- Which project root and config path metadata should remain accessible through `settings`, if any?
- Should validators preserve current error message wording exactly, or is clearer root-graph pydantic output acceptable?

## Notes For The Implementing Agent

Treat Step 01 as a standalone package build. Do not import existing feature modules, old config modules, or other shared helpers to make the package work.

Only after Step 01 is complete should Step 02 touch existing callers. This keeps implementation risk low: first prove `shared.config`, then wire the product into it.

Do the integration as a deliberate break from bounded-context config ownership. There are no backwards-compatibility bridges in this plan.
