<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Workspace Rules Docs

Use `enclosure workspace rules` to validate rule markdown.
Use route options to print a reading route and receipt.

## When To Use It

- During first-run setup before editing code.
- After editing local rule documents.
- After shared rule refresh.
- After changing rule references.
- Before agent work needing a route.
- As the first check in CI, PR review, or agent handoff.
- When path or task context should choose tags.

## How To Respond

- Fix parse errors first.
- Keep local rules narrow.
- Keep shared guidance reusable.
- Update links when files or headings change.
- Ask agents to confirm the route before edits.
- Prefer `--path` or `--task` over judgment.
- Use first-run route as the baseline, then narrow for changed files.
- Pair this with `enclosure workspace recipe --check` and `enclosure health`.

## Related Commands

- `enclosure workspace rules`
- `enclosure workspace rules route --task calibration`
- `enclosure workspace rules route --path src/enclosure/features/workspace/rules/domain/graph.py`
