<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Architecture Coherence Docs

Use `enclosure architecture coherence` to inspect how consistently feature-module streams follow the configured abstract tree: naming, tagged tree shape, sibling patterns, layer flow, public seams, and dependency pressure.

## When To Use It

- Before streamlining or refactoring feature modules.
- When deciding whether similar modules still follow one recognizable pattern.
- After adding a new feature module and before turning its shape into a recipe.

## How To Respond

- Treat scores as stage-loop signals, not pass/fail checks.
- Treat sibling-pattern findings as candidates for streamlining or intentional exceptions.
- Inspect findings before moving files or renaming modules.
- Fix boundary and shape errors with focused commands before optimizing coherence.
- Use `--top -1` when preparing a broader architecture review.

## Related Commands

- `enclosure architecture health --docs`
- `enclosure architecture map --docs`
- `enclosure architecture clusters --docs`
- `enclosure architecture boundaries --docs`
