# Shell Preview Method

The shell preview method is preview-first. It uses non-writing commands to make
contract effects visible before code or generated files change.

## Recipe Preview

Use `--shell` when a recipe should act as the shape oracle:

```sh
enclosure workspace recipe <recipe-name> <target-path> --shell
```

Use tree-only dry runs for file-shape review:

```sh
enclosure workspace recipe <recipe-name> <target-path> --dry-run --tree
```

Use content dry runs for template review:

```sh
enclosure workspace recipe <recipe-name> <target-path> --dry-run --content
```

Generate only after the preview matches the intended owner and target:

```sh
enclosure workspace recipe <recipe-name> <target-path>
```

## Focused Checks

Use these commands as non-writing evidence:

```sh
enclosure workspace recipe --check
enclosure workspace recipe --drifts
enclosure workspace rules
enclosure workspace rules route --tag structure
enclosure health
```

Use project tests and linting when behavior or source hygiene is affected:

```sh
uv run pytest
uv run ruff check .
```

## Method Discipline

- Run commands from the project root.
- Prefer preview commands before write commands.
- Treat skipped files as review signals.
- Treat shell output as evidence, not decoration.
- Record reusable findings in method or rule documents, not only in chat.

## Failure Modes

The shell method has failed when:

- generated files are written before preview,
- existing files are overwritten without inspecting skipped paths,
- recipe drift is ignored after changing a manifest,
- route output is skipped before changing rule-sensitive code,
- tests are used as a substitute for architecture checks.
