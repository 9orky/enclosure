<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Workspace Recipe Docs

Use `enclosure workspace recipe` to inspect, validate, preview, and render local recipes.

## When To Use It

- Before hand-writing a module shape that may already have a recipe.
- After changing recipe manifests or templates.
- Before writing generated scaffolding into the project.
- When checking existing feature modules against their mapped recipe role.

## How To Respond

- List available recipes before choosing one.
- Show a recipe before rendering it.
- Use dry runs to review target files before writing.
- Run recipe checks after editing recipe metadata or templates.
- Keep module-to-role ownership in `workspace.recipe.roles_map`.
- Use `--drifts` to compare mapped module trees with their configured role recipes.

## Related Commands

- `enclosure workspace recipe --help`
- `enclosure workspace rules --docs`
- `enclosure workspace sync --docs`
