# Alignings

Status: Pending Acceptance

## Problem Or Goal

Remove local dumpster coupling to `.dev` and stop reusable rules, docs, and
helpers from leaking Enclosure's own architecture layout as if it were generic
project guidance.

## Architect Audit Inputs

- Architect 1 audited `.dev` references. Source/tooling references existed in
  runtime config, architecture extraction defaults, workspace sync detection,
  package metadata, and local tool caches. Generated Modwire cache files also
  embedded `.dev/**`.
- Architect 2 audited architecture leakage. The main findings were hard-coded
  product commands in shared rules, local rules naming `architecture/boundaries`
  and `architecture/clusters` as model modules, concrete `src/enclosure/features`
  paths in generic docs/tests, product vocabulary in shared ownership rules, and
  recipe templates coupled to `enclosure.shared`.

## Accepted Clarification

- A freshly installed Enclosure workspace starts with an empty recipes folder.
- Recipes are local, user-and-agent authored scaffolds. They are dual-use:
  agents use them to generate valid code quickly, and users can use them to
  generate the boring parts when an agent is gone or unavailable.
- Generated code should be working, pluggable code. That makes patterns visible
  to agents, reduces drift, and keeps the same scaffold useful for humans.
- Therefore recipe alignment is not "product-local vs generic default." The
  target is local reusable recipes whose templates do not leak Enclosure's own
  runtime architecture unless the local recipe intentionally generates Enclosure
  product code.

## Completed Alignments

- Removed the `ConfigMetadata.dev_dir` affordance.
- Removed `.dev/**` from default architecture extraction exclusions.
- Removed `.dev` from workspace sync source-detection exclusions.
- Moved uv, pytest, ruff, and Makefile report caches to `.enclosure/.cache`.
- Removed `prune .dev` from package manifest rules.
- Deleted generated Modwire cache files that embedded `.dev/**`.
- Rewrote local rules to reference the configured contract and recipes instead
  of naming `architecture/boundaries` or `architecture/clusters` as models.
- Rewrote shared rule language to use configured health, recipe preview, and
  workspace-contract terms instead of product command names.
- Replaced shared "owning enclosure" vocabulary with "owning boundary".
- Removed concrete `src/enclosure/features/...` examples from generic docs and
  neutralized recipe-generation test fixture paths.
- Replaced the benchmark's hard-coded Enclosure source root rewrite with a
  generic architecture-root rewrite.

## Remaining Intentional Local Contract

- `.enclosure/enclosure.yaml` still names `src/enclosure/features` and mapped
  modules such as `architecture/boundaries`, `architecture/clusters`, and
  `workspace/sync`. This is the executable local contract, not a reusable rule
  or documentation leak.

## Remaining Alignment Work

- Define recipe guidance around local dual-use scaffolds: user-operable,
  agent-friendly, working, and pluggable.
- Classify existing recipes that import `enclosure.shared`,
  `enclosure.shared.config.settings`, or `enclosure.shared.scaffolding` as
  Enclosure-product recipes unless they are rewritten to use local extension
  points or recipe variables.
- For reusable local recipes, parameterize product/runtime imports and keep the
  rendered code functional without depending on Enclosure internals.
- Regenerate checked-in module docs after template changes when a generation
  command is available and approved.
- Keep `.enclosure/.cache` as generated local-only output; do not promote cache
  reports into packaged docs or shared rules.

## Verification Checklist

- [x] `rg` finds no `.dev` folder references except unrelated version/domain
      strings such as `.dev0` or `szpak.dev`.
- [x] Targeted `rg` finds `architecture/boundaries`, `architecture/clusters`,
      and `workspace/sync` only in the local contract and this plan.
- [x] `enclosure workspace rules` passes after rule edits.
- [x] `uv run pytest tests/features/workspace/recipe/test_generation.py` passes
      after fixture path changes.
- [x] `enclosure health` was run; workspace checks pass, but existing
      architecture findings remain: recipe drift, shape violations, pressure,
      coherence, and cluster findings.

## Notes For The Implementing Agent

- Treat `.enclosure/enclosure.yaml` as the local contract unless the user
  explicitly asks to change the project architecture itself.
- Do not reintroduce `.dev` as a cache or output location. Use
  `.enclosure/.cache` or a caller-provided temporary path.
- Keep shared rules generic. Concrete Enclosure CLI examples belong in product
  docs or local supplements, not in packaged shared policy.
- Wait for human acceptance before editing recipe templates or recipe metadata.
