<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Workspace Rules Docs

Use `enclosure workspace rules` to validate shared and local rule markdown documents in the current workspace.
Use `enclosure workspace rules route --tag TAG` to print a deterministic reading route and short read receipt template for agents.

## When To Use It

- After editing local rule documents.
- After refreshing packaged shared rules.
- After adding, removing, or renaming rule references.
- Before agent work that needs a confirmable rule-reading path.

## How To Respond

- Fix parse errors before interpreting other findings.
- Keep local rules project-specific and narrow.
- Keep shared guidance reusable.
- Update navigation links when rule files or headings change.
- Ask agents to confirm the route receipt before editing code.

## Related Commands

- `enclosure workspace rules route --tag structure`
- `enclosure workspace sync --docs`
- `enclosure architecture health --docs`
