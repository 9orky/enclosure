# enclosure

[![PyPI version](https://img.shields.io/pypi/v/enclosure.svg)](https://pypi.org/project/enclosure/)
[![Python versions](https://img.shields.io/pypi/pyversions/enclosure.svg)](https://pypi.org/project/enclosure/)
[![CI](https://img.shields.io/github/actions/workflow/status/9orky/enclosure/ci.yml?branch=main&label=ci)](https://github.com/9orky/enclosure/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/9orky/enclosure/blob/main/LICENSE)

`enclosure` is a small CLI for making coding agents architecture-aware inside a real repository.

It creates a project-local contract in `.enclosure/`: rules, architecture boundaries, dependency flow, file-shape constraints, and scaffolding recipes that agents can read before they edit and checks can validate after they edit.

You do not have to hand-author the whole contract. The intended workflow is to ask an agent to inspect the repository, initialize `enclosure`, draft the rules and config from the code that already works, and then refine the result with you.

The name is literal. Every agent coding task starts inside the enclosure. If the agent jumps the fence by crossing a boundary, importing through the wrong layer, inventing a module shape, or ignoring local guidance, the loop makes that visible quickly: read the contract, change the code, run the checks, steer back.

## Why Architects Should Care

Agentic coding fails less from syntax mistakes than from architectural amnesia.

An agent can search files, but it does not automatically know:

- which module owns a responsibility;
- where the public seam is;
- which layers may depend on which other layers;
- what local rules matter before touching this repo;
- what shape new files and modules should take;
- how to tell when it has crossed the fence.

`enclosure` moves that knowledge out of memory, review comments, and scattered docs and puts it in a repo-native operating surface.

## What It Supports

- **Context architecture with rules**: `.enclosure/rules/` gives agents progressive, task-specific reading paths for ownership, boundaries, dependency direction, execution, testing, and refactoring.
- **Local architectural contract**: `.enclosure/enclosure.yaml` declares roots, exclusions, tags, layer flow, dependency rules, file-shape rules, and report limits.
- **Boundary validation**: `enclosure architecture boundaries` checks imports against configured ownership and layer rules.
- **Shape validation**: `enclosure architecture shape` checks configured limits for files, symbols, imports, arguments, and line counts.
- **Architecture mapping**: `enclosure architecture map` shows modules, layers, unknown files, dependencies, and hotspots.
- **Dependency pressure views**: `enclosure architecture clusters` highlights coupled areas before broad refactors.
- **Fast preflight**: `enclosure health` gives an architect-friendly workspace and architecture overview before or after a task.
- **Project-shaped generation**: `.enclosure/recipes/` captures working module scaffolds found by the agent, then lets future tasks generate known-good files instead of hand-creating structure from scratch.
- **Assistant routing**: generated `AGENTS.md` and `.github/copilot-instructions.md` tell coding assistants to begin in `.enclosure/`.
- **Human-reviewable governance**: the contract is plain YAML and Markdown, so teams can review it like code.

## The Core Loop

```text
1. Agent starts in .enclosure/
2. Agent reads the relevant rule path and architecture contract
3. Agent edits inside the declared ownership, seam, and layer flow
4. Agent runs the relevant enclosure checks
5. Violations reveal where the task jumped the fence
6. Agent steers back before review
```

That loop is the product. The CLI is intentionally small so the contract stays close to the repository and easy to change.

## Install

```bash
pipx install enclosure
```

Try it without installing:

```bash
pipx run enclosure --help
```

`enclosure` supports Python 3.11+.

## Quick Start

The simplest setup is to let a coding agent do the first pass.

### Kickstarting Prompt

Copy this into your coding agent from the repository root:

```text
Install or run enclosure if needed, then set up this repository for agentic coding.

Start by inspecting the existing project structure and identifying the main architectural roots, modules, layers, public seams, dependency direction, tests, and one or two working examples of a well-shaped module.

Run `enclosure workspace sync init`, then draft `.enclosure/enclosure.yaml` and local rules so future agents know where to start, what boundaries to respect, and how to verify their work.

If you find a repeatable module scaffold, turn it into an `.enclosure/recipes/` recipe so future agents generate that known-good structure instead of creating files manually.

Finish by running the relevant enclosure checks, report what the contract now covers, and call out anything that still needs human architectural judgment.
```

Or run the first commands yourself:

```bash
cd your-repo
enclosure workspace sync init
$EDITOR .enclosure/enclosure.yaml
enclosure health
enclosure architecture health
enclosure architecture boundaries
```

After setup, tell every coding agent:

```text
Start in the .enclosure/ folder and stay anchored there while discovering project-specific operating guidance.
```

## Contract Shape

The generated contract has four important surfaces:

```text
.enclosure/
  ./enclosure.yaml      # architecture roots, tags, flow, rules, limits
  rules/                # shared and local guidance for agents
  recipes/              # known-good scaffolds generated from working examples
AGENTS.md               # assistant entry instruction
.github/
  copilot-instructions.md
```

A typical architecture contract describes:

```yaml
architecture:
  root: src/enclosure/features
  exclusions: [.venv/**, .enclosure/**, tests/**]
  boundaries:
    tags:
      - { name: feature, match: "*" }
      - { name: domain, match: "*/*/domain" }
      - { name: application, match: "*/*/application" }
      - { name: infrastructure, match: "*/*/infrastructure" }
      - { name: ui, match: "*/*/ui" }
    flow:
      layers: [ui, application, infrastructure, domain]
      analyzers: [backward-flow, no-cycles]
```

The full syntax is available in the generated `.enclosure/enclosure.yaml` and command docs.

Recipes are deliberately modest: they are not a framework. They are the reusable shape of code the repository already accepts. An agent can find a good module, convert that scaffold into a recipe, preview it with `--dry-run`, and then generate files that start inside the enclosure.

## Useful Commands

```bash
enclosure --docs
enclosure --llm

enclosure health
enclosure workspace health

enclosure architecture health
enclosure architecture map
enclosure architecture boundaries
enclosure architecture shape
enclosure architecture clusters

enclosure workspace rules
enclosure workspace recipe --check
enclosure workspace recipe --list
enclosure workspace recipe <name> --show
enclosure workspace recipe <name> --dry-run
```

## When To Use It

Use `enclosure` when:

- coding agents contribute to a repository with meaningful architectural boundaries;
- the team wants local rules to shape agent behavior before code review;
- module ownership, public seams, and dependency direction matter;
- generated code should follow project recipes;
- architects want a lightweight feedback loop instead of a new platform.

Skip it if the repository has no stable architecture yet or if you want a hosted workflow manager. `enclosure` is a repo-local contract and checker, not a platform.

## Release Notes

See [CHANGELOG.md](https://github.com/9orky/enclosure/blob/main/docs/repo/CHANGELOG.md).

## Contributing

Ideas, issues, and pull requests are welcome.

Start with [CONTRIBUTING.md](https://github.com/9orky/enclosure/blob/main/docs/repo/CONTRIBUTING.md).
