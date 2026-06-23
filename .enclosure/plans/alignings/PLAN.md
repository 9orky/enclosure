# Alignings

Status: In Progress - Partially Complete

## File Tree

```text
.enclosure/
  enclosure.yaml
  .cache/
    modwire/
  plans/
    alignings/
      PLAN.md
      PLAN_STEP_01.md
      PLAN_STEP_02.md
      PLAN_STEP_03.md
      PLAN_STEP_04.md
      PLAN_STEP_05.md
  rules/
    local/
    shared/
  recipes/
    module/
    module-config-support/
    module-domain-package-cli/
    module-report-cli/
    module-workspace-cli/
    pattern-module/
    slot-infrastructure-file/
docs/
  modules/
    workspace-recipe.md
pyproject.toml
src/
  enclosure/
    shared/
      config/
        metadata.py
      architecture_code.py
    features/
      workspace/
        recipe/
          ui/
            templates/
              docs.tmpl
              llm.tmpl
tests/
  shared/
    test_architecture_code.py
  features/
    workspace/
      recipe/
        test_generation.py
```

## Goal

Separate Enclosure-managed workspace state from project implementation
environment state, and stop reusable rules, docs, helpers, and local dual-use
recipes from leaking Enclosure's own runtime architecture as generic project
guidance.

The reusable-rule language cleanup and managed-cache correction are complete.
The remaining work is recipe alignment: local recipes should keep generating
working, pluggable code for humans and agents, but reusable recipes should not
render code that imports Enclosure product internals unless the recipe is
explicitly classified as Enclosure-product-only.

## Phases

### 1. Managed Cache And Configured Exclusions

Status: Done

Step Artifact: `PLAN_STEP_01.md`

Objective: Remove Enclosure runtime/config dependency on `.dev` and remove
hard-coded architecture exclusion assumptions.

Owner: runtime config and Modwire cache setup.

Inputs: `ConfigMetadata`, architecture extraction, workspace sync source
detection, package metadata, and generated Modwire caches.

Outputs: `.enclosure/.cache/modwire` for Enclosure-owned code extraction cache;
project environment/tool cache configuration stays outside `.enclosure/.cache`;
architecture exclusions come only from `.enclosure/enclosure.yaml`.

Acceptance: Enclosure runtime/config code never treats `.dev` as managed
workspace state, and architecture extraction has no hard-coded default
exclusions.

### 2. Reusable Rule And Documentation Language

Status: Done

Step Artifact: `PLAN_STEP_02.md`

Objective: Keep packaged shared rules generic while preserving this repository's
local architecture contract.

Owner: `.enclosure/rules/**`, packaged `src/enclosure/resources/rules/**`, and
generic docs/tests.

Inputs: architect audit findings for hard-coded product commands, local rule
model names, concrete `src/enclosure/features` examples, and product ownership
vocabulary.

Outputs: shared rule language uses configured health, recipe preview,
workspace-contract, and owning-boundary terms; local rules point to the
configured contract instead of treating Enclosure modules as generic models.

Acceptance: targeted `rg` finds `architecture/boundaries`,
`architecture/clusters`, and `workspace/sync` only in the executable local
contract or in alignment planning material.

### 3. Recipe Classification And Guidance

Status: Ready

Step Artifact: `PLAN_STEP_03.md`

Objective: Decide which checked-in recipes are reusable local scaffolds and which
are Enclosure-product recipes.

Owner: `.enclosure/recipes/*/recipe.yaml` and recipe guidance.

Inputs: existing manifests, template imports, accepted clarification that a new
workspace starts with an empty recipe folder, and the dual-use recipe contract.

Outputs: each recipe either avoids Enclosure product internals or clearly states
that it intentionally generates Enclosure product code.

Acceptance: every recipe that renders `enclosure.shared`, `enclosure.shared.config`,
or `enclosure.shared.scaffolding` has an explicit product-only reason, or the
template is scheduled for generic rewriting.

### 4. Reusable Recipe Template Alignment

Status: Ready

Step Artifact: `PLAN_STEP_04.md`

Objective: Rewrite reusable templates so generated code remains working without
depending on Enclosure internals.

Owner: recipe manifests and templates under `.enclosure/recipes/**`.

Inputs: existing scaffold variable support, `target.*` template context, recipe
manifest inputs, and current Typer-based CLI shape.

Outputs: infrastructure templates use target-local or standard-library workspace
discovery; UI templates render docs/results without `enclosure.shared.ui`; pattern
templates use local defaults or declared variables instead of `settings.query`.

Acceptance: `rg -n "enclosure\\.shared" .enclosure/recipes` returns no hits for
recipes classified as reusable.

### 5. Regeneration And Verification

Status: Ready

Step Artifact: `PLAN_STEP_05.md`

Objective: Refresh checked-in generated docs after template changes and prove the
remaining alignment did not regress recipe behavior.

Owner: generated module docs, recipe tests, workspace validation commands.

Inputs: updated recipes, generation commands, and existing workspace health
findings.

Outputs: regenerated docs/templates where applicable and focused tests for the
new generic rendered-code shape.

Acceptance: `enclosure workspace recipe --check`, `enclosure workspace rules`,
and focused recipe tests pass. `enclosure health` may still report existing
architecture findings unrelated to this alignment: recipe drift, shape,
pressure, coherence, and cluster findings.

## Acceptance

- `.dev` is not Enclosure-managed workspace state and is not referenced by
  Enclosure runtime/config, reusable rules, reusable docs, or recipes.
- `.enclosure/.cache` is scoped to Enclosure-managed cache data such as Modwire.
- Architecture extraction exclusions come only from the project contract; no
  implicit fallback exclusions are assumed.
- `.enclosure/enclosure.yaml` remains the executable local contract and may name
  `src/enclosure/features`, `architecture/boundaries`,
  `architecture/clusters`, and `workspace/sync`.
- Shared rules and packaged reusable docs do not present Enclosure product
  modules, commands, or source roots as generic architecture guidance.
- Local reusable recipes are user-operable, agent-friendly, working, and
  pluggable without Enclosure product imports in rendered code.
- Product-only recipes, if any remain, are explicitly classified before their
  Enclosure imports are accepted.

## Open Questions

- Should all currently checked-in `.enclosure/recipes` be treated as reusable
  local recipes? Default answer for implementation: yes, unless a product-only
  recipe is named before Phase 4 starts.
- Should reusable CLI templates keep Typer as the generated command framework?
  Default answer for implementation: yes, because current recipes already render
  Typer commands and the dependency is explicit in generated code.
- Which regeneration command should be used for checked-in module docs after
  recipe template changes? Default answer for implementation: use the existing
  Enclosure workspace recipe/docs commands when available and approved.
