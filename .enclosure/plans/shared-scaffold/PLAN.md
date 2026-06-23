# File Tree

```text
.enclosure/plans/shared-scaffold/
  PLAN.md
  PLAN_STEP_05.md
  UML.md
src/enclosure/shared/scaffolding/
  see UML.md File Layout
src/enclosure/shared/config/
src/enclosure/features/workspace/recipe/
src/enclosure/features/pattern/catalog/
src/enclosure/features/pattern/fit/
tests/shared/scaffolding/
tests/features/workspace/recipe/
tests/features/pattern/
tests/features/shared-scaffold/
```

# Goal

Extract manifest-backed scaffolding behavior into one shared package with a narrow facade seam, then make recipe and pattern features consume that seam instead of carrying separate manifest, path, include composition, render, and write implementations.

The target owner is `enclosure.shared.scaffolding`. It owns generic scaffolding mechanics only: manifest loading, relative path validation, input/file/ladder models, include traversal and cycle detection, composed input resolution, context building, rendering, and selective materialization. Feature modules keep their product language, reports, CLI behavior, catalog policy, drift checks, bench reports, preview planning, and templates.

The implementation target is code and complexity reduction. The shared API should be smaller than the duplicated behavior it replaces, and each integration should remove local code rather than introduce adapters that preserve the same complexity under new names.

# Current Status

- Phase 1 is complete and `enclosure.shared.scaffolding` is stable for
  integration.
- Phase 2 is complete. `workspace.recipe` now loads, composes, renders, parses
  variables, and writes through the package-root shared scaffolding facade.
  Recipe-owned report, drift, bench, preview, skip, and roles-map behavior
  remains local.
- Phase 3 is complete. `pattern.catalog` and `pattern.fit` now use the
  package-root shared scaffolding facade for scaffold mechanics; duplicate
  pattern manifest, repository, render, context, and write code is removed.
- Phase 4 is complete. The final integration audit removed unused recipe
  compatibility aliases, added focused boundary guard tests, confirmed template
  stubs do not regenerate old scaffold mechanics, and verified recipe, pattern,
  shared scaffolding, and lint checks.
- Phase 5 is proposed. A follow-up architecture scan found stale generated
  pattern-module templates, config seam leaks, duplicated config query/metadata
  fixtures, and a few exported helpers that should be removed or explicitly
  justified before the shared seams are considered closed.

# Phases

## Phase 1: Fresh Shared Scaffolding Package

- Status: Complete; stable.
- Objective: create the new SSOT package for generic scaffold behavior.
- Owner: `src/enclosure/shared/scaffolding/`.
- Inputs: behavioral requirements observed in current recipe, pattern fit, and pattern catalog code; no imports from those modules.
- Outputs: a complete package-root `scaffolding` facade instance backed by `ScaffoldFacade`; merged scaffold and manifest ownership files; private classes and methods for YAML parsing, conversion, include composition, rendering, and writing.
- Acceptance: shared tests prove manifest loading, schema validation, path normalization, include composition, context defaults, rendering, and materialization without importing or modifying feature internals.
- Stability evidence: standalone shared scaffolding tests, full test suite, full
  lint, export checks, class-only shape checks, forbidden dependency scans, and
  real `.enclosure/recipes` smoke rendering all pass.

## Phase 2: Workspace Recipe Proof

- Status: Complete.
- Objective: integrate one bounded context as proof that the shared package reduces code without changing behavior.
- Owner: `src/enclosure/features/workspace/recipe/`.
- Inputs: shared scaffolding package and existing recipe application/report behavior.
- Outputs: recipe code delegates manifest discovery, include composition, rendering, variable parsing, and file writing to `from enclosure.shared.scaffolding import scaffolding`; recipe-specific roles-map composition, drift, bench, preview planning, and report logic stays local.
- Acceptance: existing workspace recipe CLI functional tests pass unchanged, and duplicated recipe manifest/render/write helpers are removed.
- Verification evidence: `uv run pytest tests/features/workspace/recipe`,
  `uv run pytest tests/shared/scaffolding tests/features/workspace/recipe`,
  and `uv run ruff check src/enclosure/features/workspace/recipe
  tests/features/workspace/recipe` pass. `enclosure health` runs and reports
  recipe check clean while unrelated baseline findings remain.

## Phase 3: Remaining Modules and Cleanups

- Status: Complete.
- Objective: move remaining pattern modules to the proven shared seam and delete obsolete duplicate code.
- Owner: `src/enclosure/features/pattern/catalog/`, `src/enclosure/features/pattern/fit/`, and cleanup in affected recipe files.
- Inputs: proven shared scaffolding package and completed recipe integration pattern.
- Outputs: pattern catalog and pattern fit delegate scaffold mechanics, including include traversal and input aggregation, to shared code; feature-local wrappers, aliases, and dead helper code are removed.
- Acceptance: focused pattern tests are added under `tests/features/pattern/`;
  `uv run pytest tests/shared/scaffolding tests/features/workspace/recipe
  tests/features/pattern` and `uv run ruff check src tests` pass; follow with
  `enclosure health` if available in the active environment.

## Phase 4: Final Integration Audit

- Status: Complete.
- Objective: gather and close the remaining integration questions after recipe
  and pattern migration, without expanding the shared scaffolding API.
- Owner: `src/enclosure/features/workspace/recipe/`, `.enclosure/recipes/`,
  `tests/shared/scaffolding/`, `tests/features/workspace/recipe/`,
  `tests/features/pattern/`, and focused scan/guard tests.
- Inputs: completed Step 03 migration and the post-migration full-pass audit.
- Outputs: every manifest-backed scaffold consumer is either using
  `from enclosure.shared.scaffolding import ...` through the package root or is
  explicitly documented as a non-scaffold feature; remaining compatibility
  aliases are either justified by current callers or removed; guard tests/scans
  prevent reintroducing local scaffold mechanics.
- Acceptance: Step 04 proves there are no remaining live integrations beyond
  shared scaffolding consumers, no feature imports shared internals, recipe
  template stubs do not regenerate removed scaffold mechanics, and existing
  recipe/pattern/shared tests plus lint pass.
- Verification: `uv run pytest tests/shared/scaffolding
  tests/features/workspace/recipe tests/features/pattern
  tests/features/shared-scaffold` and `uv run ruff check src tests` pass.
  `enclosure health` reports recipe checks clean with unrelated baseline
  findings in workspace rules, recipe drift, architecture shape, pressure,
  coherence, and clusters.

## Phase 5: Config And Scaffolding Leak Remediation

- Status: Proposed; see [PLAN_STEP_05.md](PLAN_STEP_05.md).
- Objective: close the SSOT forks and abstraction leaks found after Step 04 in
  `shared.config`, `shared.scaffolding` consumers, generated templates, and
  guard tests.
- Owner: `.enclosure/recipes/pattern-module/`,
  `tests/features/shared-scaffold/`, `src/enclosure/shared/config/`, and narrow
  config-consuming feature/test seams.
- Inputs: two independent architecture scans plus local source verification.
- Outputs: stale generated manifest/repository/config/render mechanics removed,
  shared config public seam decided, fake config fixtures replaced, config path
  semantics centralized, and guard tests expanded to catch templated regressions.
- Acceptance: Step 05 proves generators cannot recreate removed scaffold
  mechanics; callers reach shared config/scaffolding through explicit seams; and
  focused tests plus lint pass.

# Acceptance

- `enclosure.shared.scaffolding.__init__` is the only public shared scaffolding seam.
- `__init__.py` is export-only and contains no behavior implementation.
- No feature imports `enclosure.shared.scaffolding` internals.
- No feature mirrors private shared scaffolding abstractions through local
  wrapper repositories, renderers, materializers, manifest readers, path
  normalizers, input resolvers, or context builders.
- Recipe and pattern features no longer define independent copies of scaffold manifest parsing, include traversal, input aggregation, file rendering, path normalization, or selective materialization.
- Shared scaffolding does not import settings, resolve recipe/project roots, or bind caller roots into internal class constructors or state.
- Shared `Scaffold.source_root` names the individual scaffold/template folder; caller-provided `scaffold_root` names the collection folder.
- Private shared DTOs and helper classes remain private; callers may use only
  package-root `scaffolding`, `Scaffold`, `RenderedScaffoldFile`, and
  `ScaffoldError`.
- Existing CLI commands keep their current output and exit behavior unless a test exposes an existing bug that is approved as a contract change.
- The shared package does not import from `enclosure.features`.
- Step 02 and Step 03 treat `shared.scaffolding` as complete; missing shared behavior requires updating UML and Step 01 before integration continues.

# Open Questions

- `pattern.fit` remains a visible feature for this extraction. Any merge into
  `pattern.catalog` is a separate follow-up.
- Role and slot-state values remain validated strings in shared scaffolding.
  Enums can be introduced later only if they reduce consumer code.
- Nested scaffold DTO types remain reachable only through exported `Scaffold`;
  they are not promoted to package-root exports for Step 03.
- `workspace.plan` and `workspace.sync` use plan/sync write behavior, not
  manifest-backed scaffolding. They are excluded from shared scaffolding
  integration unless they later load, compose, render, or materialize
  recipe-style scaffold manifests.
