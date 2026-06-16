<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Workspace Recipe Docs

Use `enclosure workspace recipe` to inspect, validate, preview, and render recipes.

## When To Use It

- During first-run setup before creating project-shaped files.
- Before hand-writing a module shape that may already have a recipe.
- After changing recipe manifests or templates.
- Before writing generated scaffolding.
- When checking modules against their mapped recipe role.

## How To Respond

- List available recipes before choosing one.
- Show a recipe before rendering it.
- Use `enclosure workspace recipe <name> <path> --shell` as the first-run convention oracle.
- Use dry runs before writing.
- Run recipe checks after editing recipe metadata or templates.
- Compose reusable `fragment` recipes with `includes`.
- Keep module-to-role ownership in `workspace.recipe.roles_map`.
- Use `--drifts` to compare mapped module trees to recipes.

## Related Commands

- `enclosure workspace recipe --help`
- `enclosure workspace recipe --list`
- `enclosure workspace rules --docs`
