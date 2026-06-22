# Verification Method

Verification has two jobs:

1. prove behavior,
2. prove conformance to the architecture contract.

Tests usually prove behavior. Enclosure checks prove conformance. Serious work
requires the right evidence for the risk introduced.

## Behavioral Evidence

Prefer tests at the highest valid public seam:

1. CLI or public feature seam for user-visible behavior.
2. Module seam when the module owns the behavior.
3. Lower-level direct tests only when the lower unit owns the behavior or the
   public seam cannot isolate it.

Do not test private helpers only because they are easy to import. That freezes
internals and weakens the seam.

## Architecture Evidence

Use architecture checks when a change touches:

- boundaries,
- layer direction,
- recipe manifests,
- rule documents,
- workspace configuration,
- module file shape.

Useful commands:

```sh
enclosure workspace recipe --check
enclosure workspace recipe --drifts
enclosure workspace rules
enclosure health
uv run pytest
uv run ruff check .
```

## Failure Classification

When verification fails, classify it:

- behavior wrong: fix implementation or test expectations,
- contract wrong: fix rule, config, or recipe after proving the old contract is
  invalid,
- shape drift: update the module or recipe role,
- boundary violation: change ownership, seam, or dependency direction,
- missing evidence: add the smallest check that proves the claim.

Weakening checks to make a failure disappear is not verification.
