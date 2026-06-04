<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Architecture GUI Docs

`enclosure gui` opens the current project as an interactive architecture canvas in a browser.

## Usage

```bash
enclosure gui
```

## Controls

- Arrow down expands all visible folders one level and fits the tree.
- Arrow up folds all visible folders one level and fits the tree.
- The tree chooses the best-fitting layout for the visible nodes, growing horizontally when that uses the canvas better.
- Drag pans the canvas.
- Mouse wheel zooms around the pointer.
- The fit button recenters the current tree.

## Modes

- Boundaries shows architecture tags, exclusions, dependency edges, and rule findings.
- Symbols shows files and extracted symbols with dependency heat.
- Shape lets you adjust numeric limits locally in the browser and highlights affected files.

## Options

- `--host` changes the local server host.
- `--port` changes the local server port.
- `--no-open` prints the URL without opening a browser tab.
