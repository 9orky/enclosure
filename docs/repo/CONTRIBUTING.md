# Contributing

Thanks for stopping by.

`enclosure` is a small CLI with a fairly opinionated goal: help humans and coding agents cooperate without turning the repository into folklore.

## Local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip build twine
python -m pip install -e .
```

## Useful commands

```bash
make test
enclosure --help
enclosure --docs
enclosure health
enclosure workspace health
enclosure architecture boundaries
enclosure architecture shape
enclosure workspace rules
python -m build
python -m twine check dist/*
```

## Ground rules

- Keep changes narrow and intentional.
- Prefer the repo's existing feature/module/layer patterns over inventing a new one.
- If you change the CLI, make `--help` better, not just longer.
- Run `enclosure health` before summarizing architecture-sensitive work.
- If you change the architecture feature, run `enclosure architecture boundaries` and `enclosure architecture shape`.
- If you touch packaged resources, remember they ship to users.

## Pull requests

Small PRs are easier to review, safer to release, and kinder to everyone's future self.
