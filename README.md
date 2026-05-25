# enclosure

[![PyPI version](https://img.shields.io/pypi/v/enclosure.svg)](https://pypi.org/project/enclosure/)
[![Python versions](https://img.shields.io/pypi/pyversions/enclosure.svg)](https://pypi.org/project/enclosure/)
[![CI](https://img.shields.io/github/actions/workflow/status/9orky/enclosure/ci.yml?branch=main&label=ci)](https://github.com/9orky/enclosure/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/9orky/enclosure/blob/main/LICENSE)

Coding agents are brilliant.

They are also very enthusiastic strangers in your house.

`enclosure` is a tiny CLI that gives them a room, a map, a few house rules, and a polite reminder that the production database is not a toy chest.

It creates a project-local operating contract for humans and agents: readable rules, architecture boundaries, local recipes, and checks that turn "please understand this repo" into something visible, reviewable, and repeatable.

Small tool. Big reduction in "wait, why did it touch that?"

The ambition is simple: be the smallest powerful thing in the category.

## The Problem

Most AI coding failures do not start with bad syntax.

They start with missing context.

The agent does not know which module owns the behavior. It does not know that this folder is legacy, that this layer must stay inward-facing, that a public package seam exists for a reason, or that the team has a very specific way of adding new features.

Humans know these things. Usually in meetings, memory, code review scars, and that one message in Slack nobody can find anymore.

`enclosure` makes that knowledge sit inside the repository.

Not as a manifesto. As files.

## What Enclosure Gives You

`enclosure` gives your repo an enclosure for agents: a small, explicit place where cooperation starts.

- `.enclosure/enclosure.yaml` describes architecture tags, layer flow, exclusions, and dependency rules.
- `.enclosure/rules/` mirrors shared guidance that agents can read before improvising.
- `.enclosure/rules/local/` keeps repository-specific decisions where humans can review and tune them.
- `.enclosure/recipes/` holds local recipes for project-shaped scaffolding.
- `AGENTS.md` and `.github/copilot-instructions.md` point coding assistants toward the contract.

The point is not to make agents obedient little robots. That would be boring, and also fiction.

The point is to make cooperation cheaper. The agent can still reason, explore, and help, but it starts from boundaries the team can see.

## Why It Feels Different

Many tools in this space try to become the new center of gravity.

`enclosure` does the opposite.

It stays small, local, and boring in the best possible way. No platform migration. No ceremony tax. No giant dashboard asking if you are having a productive transformation journey today.

You run it in a repo. It writes a contract. You and your agents use that contract. When the shared baseline changes, you update it. When the local rules need nuance, you edit normal files.

That is the trick: `enclosure` is powerful because it does not try to own your workflow. It gives the workflow a skeleton, then gets out of the way.

## Capabilities

- Bootstrap or refresh a local collaboration contract.
- Validate architecture boundaries, dependency flow, and file shape.
- Map modules, layers, hotspots, unknown files, and dependency pressure.
- Validate local rule documents.
- Inspect, preview, and render project-shaped recipes.

Command syntax lives in `--help`. Human-facing command guidance lives beside the command implementation and is available with `--docs`.

## Install

```bash
pipx install enclosure
```

Try it without committing to the relationship:

```bash
pipx run enclosure --help
```

`enclosure` supports Python 3.11+.

## Quick Start

```bash
cd your-repo
enclosure workspace sync init
$EDITOR .enclosure/enclosure.yaml
enclosure architecture health
enclosure architecture boundaries
```

Then tell your coding agent to start in `.enclosure/`.

That one instruction changes the conversation. Instead of "look around and guess," the agent gets a doorway into the repo's actual operating model.

For command-level documentation:

```bash
enclosure --docs
enclosure architecture --docs
enclosure workspace recipe --docs
```

## Configuration Sketch

```yaml
architecture:
  language: python
  root: src/enclosure/features
  exclusions: [.venv/**, .enclosure/**, tests/**, libraries/**]
  shape:
    max_classes_per_file: -1
    max_interfaces_per_file: -1
    max_types_per_file: -1
    max_abstract_classes_per_file: -1
    max_functions_per_file: -1
    max_methods_per_class: -1
    max_declared_args_per_function: -1
    max_declared_args_per_method: -1
    max_lines_count_per_function: -1
    max_lines_count_per_method: -1
    max_lines_count_per_class: -1
    allow_optional_function_args: true
    allow_optional_method_args: true
    allow_optional_class_properties: true
    allow_imports_aliases: true
    enforce_joined_imports: false
    allowed_imports_crossing_types: [module, symbol]
  boundaries:
    tags:
      - { name: feature, match: &feature "*", except: [], exclude: [] }
      - { name: module, match: &module "*/*", except: ["*/__init__"], exclude: [] }
      - { name: module_api, match: &module_api "*/*/__init__", except: [], exclude: [] }
      - { name: domain, match: &domain "*/*/domain", except: [], exclude: [] }
      - { name: application, match: &application "*/*/application", except: [], exclude: [] }
      - { name: infrastructure, match: &infrastructure "*/*/infrastructure", except: [], exclude: [] }
      - { name: ui, match: &ui "*/*/ui", except: [], exclude: [] }
    rules:
      - { source: *feature, disallow: [*feature], allow: [*module_api], allow_same_match: true }
      - { source: *module, disallow: [*module], allow: [*module_api], allow_same_match: true }
      - { source: "*/config/domain", disallow: [*module], allow: [*domain], allow_same_match: true }
      - { source: *domain, disallow: [*application, *infrastructure, *ui], allow: [], allow_same_match: false }
      - { source: *infrastructure, disallow: [*application, *ui], allow: [], allow_same_match: false }
      - { source: *application, disallow: [*ui], allow: [], allow_same_match: false }
      - { source: *ui, disallow: [*infrastructure], allow: [], allow_same_match: false }
    flow:
      layers: [ui, application, infrastructure, domain]
      module_tag: feature
      analyzers: [backward-flow, no-cycles]
  map:
    top: 20
  clusters:
    group_depth: 5
    top: 20
    files_top: 5
  health:
    top: 5

workspace:
  recipe:
    skip: []
  rules:
    local:
      max_content_chars: 2400
  sync: {}
```

For report-size limits such as `top` and `files_top`, `-1` means unlimited,
`0` means show none, and any positive value caps the result.

The syntax is intentionally small. It describes seams, not the meaning of life.

## Who It Is For

Use `enclosure` if:

- you work with coding agents and want them to understand repo boundaries before editing;
- your team has architecture rules that live mostly in people's heads;
- you want generated files to follow local recipes instead of generic templates;
- you like tools that are small enough to understand and useful enough to keep.

Skip it if you want an all-seeing platform that manages every decision for you. `enclosure` is not trying to become your boss. It already has plans this weekend.

## The Human Part

Good agent collaboration is not about replacing human judgment.

It is about reducing the amount of judgment wasted on preventable mess.

Humans decide the architecture. Humans review the contract. Humans tune the local rules. Agents get a better starting point, a smaller blast radius, and a way to explain their work in the language of the repository.

That is why `enclosure` is small but powerful: it does not make the agent smarter by magic. It makes the room clearer.

And clear rooms produce better work.

## Release Notes

See [CHANGELOG.md](https://github.com/9orky/enclosure/blob/main/docs/repo/CHANGELOG.md).

## Contributing

Ideas, issues, and pull requests are welcome.

Start with [CONTRIBUTING.md](https://github.com/9orky/enclosure/blob/main/docs/repo/CONTRIBUTING.md).
