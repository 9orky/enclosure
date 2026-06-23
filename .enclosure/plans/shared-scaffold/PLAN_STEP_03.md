# Implementation Tree

```text
src/enclosure/features/pattern/catalog/
  domain/
    pattern-specific report/result language remains
    duplicate manifest model removed unless a public compatibility alias has a current caller
  infrastructure/
    repository and manifest parser duplicates removed
    shared scaffolding facade used at the package root seam
  application/
    describe/validate/preview use shared `Scaffold` objects or thin pattern summaries
src/enclosure/features/pattern/fit/
  domain.py
    fit-specific preview/result dataclasses remain
    duplicate scaffold models/context helpers removed
  infrastructure.py
    repository/render/materializer/manifest duplicates removed or file deleted if empty
  application.py
    preview/materialize use shared scaffolding load/compose/render/write behavior
tests/features/pattern/
  catalog/test_application.py
    list/show/validate and composed-role/catalog preview proof
  fit/test_application.py
    missing pattern, empty scaffold, create preview, skip-existing, skip-config,
    materialize, and include rendering proof
```

Status: Ready for acceptance; do not implement until accepted.

# Goal

Move remaining modules to the proven shared scaffolding facade seam and clean up the temporary complexity left by the extraction.

This step should finish the reduction: the same manifest/include/render/write behavior should exist in one shared package, and pattern modules should only retain feature-specific orchestration and result language.

# Step Contract

- Inputs: completed Step 02 recipe proof.
- Outputs: pattern catalog and pattern fit consume `from enclosure.shared.scaffolding import scaffolding`; duplicate local scaffold behavior is removed.
- Scope: `src/enclosure/features/pattern/catalog/`, `src/enclosure/features/pattern/fit/`, focused pattern tests, and only directly relevant recipe cleanup if a current caller no longer needs it.
- Out of scope: changing command names, changing manifest schema, merging pattern fit into pattern catalog, adding new scaffold features.
- Owner: pattern modules own pattern vocabulary and user-facing behavior; `shared.scaffolding` owns scaffold mechanics.
- Dependency direction: pattern modules may import only `scaffolding` and required DTOs/errors from the `enclosure.shared.scaffolding` package root, not internal shared modules; `shared.scaffolding` remains feature-independent.
- SSOT rule: there is exactly one owner for manifest parsing, scaffold DTOs,
  include traversal, input resolution, target normalization, render context,
  rendering, and selective writes: `enclosure.shared.scaffolding`.
- Abstraction boundary: pattern modules must not import, instantiate, subclass,
  type-check against, or mirror private shared classes such as
  `_ScaffoldManifestRepository`, `_ScaffoldComposer`, `_ScaffoldRenderer`,
  `_ScaffoldContextFactory`, `_ScaffoldRelativePathNormalizer`, or nested
  private DTO classes. Reach them only through `scaffolding`, `Scaffold`,
  `RenderedScaffoldFile`, and `ScaffoldError` from the package root.
- Step 03 must treat `shared.scaffolding` as complete. If remaining modules need
  new shared behavior, stop and update `UML.md` and Step 01 before continuing.

## SSOT Guardrails

- Do not create feature-local wrappers that re-express shared behavior under
  pattern names, such as `PatternRepository`, `PatternRenderer`,
  `PatternMaterializer`, `PatternManifestReader`, `PatternRelativePath`,
  `PatternInputSpec`, or `RenderedPatternFile`, unless the type is a
  user-facing result model with feature-owned fields and a current caller.
- Do not copy validation constants, regular expressions, path normalization
  rules, target default maps, variable context maps, include cycle detection,
  or input resolution from shared scaffolding into pattern modules.
- Do not expose shared private nested DTO types through pattern public APIs.
  Pattern public seams should expose pattern reports/summaries/previews, not
  `_ScaffoldInput`, `_ScaffoldFile`, `_ScaffoldLadder`, or `_ScaffoldSlot`.
- Do not add convenience exports to `enclosure.shared.scaffolding.__init__` to
  make pattern migration easier. New exports are a Step 01/UML contract change.
- Do not add shared-to-feature callbacks, settings reads, fixture knowledge, or
  pattern vocabulary to `shared.scaffolding`.
- Thin adapters are allowed only at a feature boundary where they convert
  `Scaffold` or `RenderedScaffoldFile` into pattern-owned reports, summaries,
  preview statuses, or violations. They must not preserve duplicated scaffold
  mechanics.

## Step 02 Dependency

Step 02 proved the shared seam in `workspace.recipe`.

The expected reusable integration pattern is:

- load manifests through `scaffolding.load_all()` and `scaffolding.load()`;
- compose includes through `scaffolding.compose()`;
- render files through `scaffolding.render()`;
- materialize selected paths through `scaffolding.write()`;
- parse CLI variables through `scaffolding.parse_variables()` if pattern UI gains
  or exposes variable parsing during this step;
- catch `ScaffoldError` at feature boundaries where current code catches
  manifest `ValueError`, preserving feature-specific report codes and messages
  where tests establish them;
- keep pattern vocabulary, summaries, catalog validation, preview statuses, and
  CLI output local to pattern modules.

Step 02 also showed two useful implementation details:

- Shared `Scaffold.role` and slot `state` are strings, not feature enums; pattern
  validation should compare string values such as `"container"` and
  `"archetype"`.
- Shared `RenderedScaffoldFile.relative_path` is a `Path`; convert it to
  pattern preview/result structures only at the feature boundary where statuses
  are applied.

# Execution

1. Resolve `scaffold_root` in pattern code from `settings.metadata.recipes_dir`; pass that path into shared calls and do not let shared code import settings.
2. Replace pattern catalog `FilePatternRepository` and
   `infrastructure.manifests` loading with `scaffolding.load_all()` and
   `scaffolding.load()`.
3. Map shared `Scaffold` objects into `PatternSummary` only at
   `pattern.catalog.application.describe`; use the `Scaffold.role` string
   directly and `Scaffold.ladder.summary()` instead of local manifest
   enums/ladder DTOs.
4. Replace pattern catalog include traversal and composed ladder metadata reads
   in `application.preview` with `scaffolding.compose()` where behavior is
   generic.
5. Keep pattern catalog role composition strings, catalog validation, violation
   codes, and report/result language local.
6. Delete `pattern.catalog.domain.manifest` duplicate scaffold types once all
   callers use shared `Scaffold`, or leave only compatibility aliases that have
   a current production caller.
7. Delete `pattern.catalog.infrastructure.manifests` and
   `pattern.catalog.infrastructure.repository` once all callers use the shared
   scaffolding facade.
8. Replace pattern fit repository with shared scaffolding facade loading.
9. Replace pattern fit include traversal, input aggregation, renderer, and
   materializer with `scaffolding.render()` and `scaffolding.write()`.
10. Remove pattern fit local target context, defaults, variable context, target
    normalization, `_PatternManifest`, YAML reader, local `PatternInputSpec`,
    local `PatternFile`, and local rendered-file DTOs where shared
    `Scaffold`/`RenderedScaffoldFile` now own them.
11. Keep pattern fit preview statuses local: `create`, `skip_exists`, and
    `skip_config`. Convert shared rendered files to `PatternPreviewFile` at the
    preview boundary.
12. Review `workspace.recipe` after pattern integration. Do not churn public
    compatibility aliases that are still exported for callers; remove only
    wrappers or aliases with no current caller.
13. Add real source tests under `tests/features/pattern/`; do not rely on stale
    `__pycache__` artifacts.
14. Run a search for duplicate scaffold symbols and remove remaining private
    copies unless they are feature-specific by behavior, not just by name.
15. Audit every new helper added during Step 03. If the helper parses manifests,
    walks includes, aggregates inputs, normalizes paths, builds render context,
    renders templates, or writes files, it is an SSOT violation and must be
    removed or moved only through a reopened Step 01 contract.
16. Do not add back-calls from `shared.scaffolding` into pattern or recipe code.
17. Do not add new shared scaffolding API unless Step 01 and [UML.md](UML.md)
    are reopened first.

# Verification

- Add focused pattern catalog tests for listing/loading current fixture
  manifests through the public feature seam, catalog validation, and composed
  role/catalog preview behavior.
- Add focused pattern fit tests for missing pattern, empty scaffold, create
  preview, skip-existing, skip-config, include rendering, and materialize.
- Run `uv run pytest tests/shared/scaffolding tests/features/workspace/recipe tests/features/pattern`.
- Run `uv run ruff check src tests`.
- Run `enclosure health` if the command is available from the local environment.
- Confirm with `rg` that `_PatternManifest`, `FilePatternRepository`,
  `FilePatternRenderer`, `FilePatternMaterializer`, pattern-local
  `_load_yaml_mapping`, `included_patterns_for`, `_patterns_for_rendering`,
  `_input_specs_for`, local target/default/variable context helpers, and
  duplicate pattern `RelativePath`/`PatternInputSpec`/`PatternFile`/
  `RenderedPatternFile` definitions no longer remain outside intentional
  feature result models or explicitly justified public compatibility aliases.
- Confirm with `rg` that pattern modules do not mention shared private classes
  or modules: `_Scaffold`, `ScaffoldFacade`, `manifest.py`, `composition.py`,
  `context.py`, `render.py`, `write.py`, `relative_path.py`, or imports matching
  `enclosure.shared.scaffolding.`.
- Confirm with `rg` that no pattern module carries duplicated scaffold mechanics
  by searching for `yaml`, `BaseModel`, `ConfigDict`, `safe_load`,
  `render_recipe_template`, `target_defaults`, `target_context`,
  `variable_context`, `normalize_target`, `normalize_relative`, and
  `resolve_input`.
- Confirm `src/enclosure/shared/scaffolding/` still has no imports from `src/enclosure/features/`.
- Confirm `src/enclosure/features/pattern/` imports only from the
  `enclosure.shared.scaffolding` package root, not internal shared modules.
- Confirm `workspace.recipe` still passes and keeps only package-root shared
  scaffolding imports.

# Completion

Step 03 is complete when recipe, pattern catalog, and pattern fit all use one shared scaffolding facade implementation, duplicate behavior is deleted, tests pass, and no cleanup wrappers remain without a current caller.

Step 03 must not begin until this plan is accepted.
