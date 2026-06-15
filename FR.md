# Modwire Feature Requests From Enclosure Integration

## Context

Enclosure uses `modwire>=1.1.0` as its architecture analysis engine. The library is on the critical path for:

- source extraction through `modwire.extract_code`
- dependency graph construction through `CodeMap.graph` and `build_dependency_graph`
- boundary validation through `ArchitecturePolicyEvaluator`
- architecture tag matching through `match_node`
- language discovery through `supported_languages`
- report rendering through `modwire.architecture.render`

The integration is substantial enough that Enclosure now carries its own adapter layer around Modwire in `src/enclosure/shared/architecture_code.py` and `src/enclosure/shared/architecture_code_cache.py`, plus higher-level report logic in the architecture feature modules.

This report focuses on library changes that would make Modwire easier to consume from Enclosure and likely from other architecture tooling.

## Current Enclosure Usage

### Extraction And Code Maps

Enclosure calls `extract_code(language, project_root, exclusions)` and then reads:

- `CodeMap.extraction_result.files`
- `ExtractionSummary.files_found`
- `ExtractionSummary.files_checked`
- `ExtractionSummary.files_excluded`
- `CodeMap.graph.edges`
- `CodeMap.runtime_command`

Relevant files:

- `src/enclosure/shared/architecture_code.py`
- `src/enclosure/shared/architecture_code_cache.py`
- `src/enclosure/features/architecture/shape/domain.py`
- `src/enclosure/features/architecture/clusters/domain.py`

### Architecture Policy Evaluation

Enclosure validates dependency boundaries through:

- `ArchitecturePolicyEvaluator().evaluate(graph, config)`
- `EdgeRuleViolation`
- `FlowViolation`
- `supported_analyzers()`

Relevant files:

- `src/enclosure/features/architecture/boundaries/application.py`
- `src/enclosure/features/architecture/boundaries/domain.py`
- `src/enclosure/features/architecture/health/application.py`

### Matching And Tags

Enclosure calls `match_node` directly to map files into modules, layers, API seams, and coherence streams.

Relevant files:

- `src/enclosure/features/architecture/map/domain.py`
- `src/enclosure/features/architecture/coherence/domain/tree.py`

### Rendering

Enclosure reuses `modwire.architecture.render.violations` as a Jinja filter.

Relevant file:

- `src/enclosure/shared/ui.py`

## Priority Requests

### 1. First-Class Cached Extraction

Enclosure currently implements its own Modwire cache with:

- cache key hashing
- source manifests
- source file stat tracking
- extractor implementation file stamps
- runtime executable stamps
- JSON persistence
- atomic writes
- cache pruning
- graph rebuild on cache hit
- source-change-during-extraction protection

This is useful outside Enclosure and would be better owned by Modwire.

Requested API shape:

```python
code_map = modwire.extract_code(
    language="python",
    sources_root=source_root,
    exclusions=("ignored/**",),
    cache=modwire.ExtractionCache(
        root=workspace_root / ".modwire-cache",
        max_entries=3,
    ),
)
```

Useful details:

- expose cache hit/miss status
- invalidate on source changes, extractor script changes, Modwire version changes, and runtime executable changes
- keep cache schema versioned
- write cache entries atomically
- support disabling cache per call
- support cache pruning policy

Evidence: `src/enclosure/shared/architecture_code_cache.py` is mostly Modwire cache integration code.

### 2. Workspace Root And Architecture Root Support

Enclosure often has a workspace root and a narrower architecture root. Today it must extract from the architecture root, cache under the workspace root, normalize exclusions, and sometimes rebase source IDs itself.

Requested API shape:

```python
code_map = modwire.extract_code(
    language="python",
    workspace_root=project_root,
    sources_root=project_root / "src/enclosure/features",
    source_id_root="src/enclosure/features",
    exclusions=(".venv/**", "src/enclosure/features/generated/**"),
)
```

Expected behavior:

- cache lives under `workspace_root`
- source IDs can be returned relative to `sources_root` or `workspace_root`, by option
- exclusions can be declared relative to either root with deterministic normalization
- matching/policy evaluation uses the same logical source IDs as extraction

Evidence: `architecture_code._architecture_root`, `_extraction_exclusions`, `_source_prefix`, `_rebase_source_id`, `_rebase_import`, `_scoped_code_map`, and `_ArchitectureMatchingConfig`.

### 3. Public Source Discovery And Manifest API

Enclosure recreates Modwire's source discovery so it can decide whether cached extraction is valid. This duplicates exclusion semantics and file counting.

Requested API shape:

```python
manifest = modwire.discover_sources(
    language="python",
    sources_root=source_root,
    exclusions=("ignored/**",),
)
```

The manifest should include:

- source IDs
- filesystem paths
- file size and mtime
- files found
- files excluded
- files checked
- extractor metadata used for discovery

Important: this must use the exact same traversal and exclusion semantics as `extract_code`.

Evidence: `architecture_code_cache._collect_source_targets`, `_matches_exclusion`, `_matches_pruneable_directory`, and related tests.

### 4. Stable CodeMap Serialization

`SourceFile` is a Pydantic model, but `CodeMap`, `ExtractionResult`, `ExtractionSummary`, and `DependencyGraph` are dataclasses. Enclosure serializes only the files and summary, then rebuilds the graph manually.

Requested API shape:

```python
payload = modwire.serialize_code_map(code_map)
code_map = modwire.deserialize_code_map(payload)
```

or:

```python
payload = code_map.to_json()
code_map = CodeMap.from_json(payload)
```

Requirements:

- versioned schema
- full graph round-trip or deterministic graph rebuild
- compatibility story across Modwire versions
- validation errors instead of raw model/dataclass failures

Evidence: `architecture_code_cache.ArchitectureCodeCacheEntry` and `_code_map_from_entry`.

### 5. CodeMap Transform Helpers

Enclosure needs common graph/code-map transforms that Modwire could provide directly:

- filter to tracked files only
- remove external/unresolved import nodes
- rebase source IDs under a prefix
- rewrite imports consistently after rebasing
- build subgraphs
- iterate tracked edges

Requested API examples:

```python
tracked = code_map.tracked_only()
scoped = code_map.rebase("src/enclosure/features")
subgraph = code_map.subgraph(nodes=tracked_ids)
```

Evidence:

- `architecture_code.tracked_dependency_graph`
- `architecture_code._scoped_code_map`
- `clusters._incoming_counts`
- `map.describe_architecture_map`

### 6. Richer DependencyGraph API

`DependencyGraph` currently exposes `add_node`, `add_edge`, `outgoing`, and `node_ids`. Enclosure repeatedly computes higher-level graph views.

Requested additions:

- `incoming(node_id)`
- `edges_between(source, target)`
- `has_node(node_id)`
- `subgraph(node_ids)`
- `without_external_nodes(tracked_ids)`
- stable sorted iterators
- immutable/frozen graph option for report code

Evidence: cluster, map, health, and coherence reports all iterate raw `graph.edges` and maintain their own counters.

### 7. External Import Policy Controls

`build_dependency_graph` creates graph nodes for every normalized import path, even when the import target is outside extracted files. That is useful sometimes, but Enclosure frequently wants only tracked source files for architecture rules.

Requested options:

```python
graph = modwire.build_dependency_graph(files, include_external=False)
```

or:

```python
code_map.graph.tracked_edges()
code_map.graph.external_edges()
```

Expected behavior:

- make tracked vs external nodes explicit
- expose unresolved imports distinctly
- let policy evaluators choose whether external nodes participate

Evidence: `architecture_code.tracked_dependency_graph` exists only to protect boundary evaluation from external nodes.

### 8. Compiled Tag Matcher / Tag Map API

Enclosure calls `match_node` repeatedly and reimplements tag mapping for modules, layers, API seams, and streams.

Requested API shape:

```python
matcher = modwire.architecture.TagMatcher(config)
match = matcher.match(node_id, "module")
tags = matcher.tags_for(node_id)
tag_map = matcher.map_code_map(code_map)
```

Useful behavior:

- compile patterns once
- expose matched tag name, matched path, captured path, and wildcard status
- apply exclusions consistently
- expose display path helpers for architecture roots
- avoid requiring callers to pass a plain `exclusions` dict into `match_node`

Evidence: `architecture/map/domain.py` and `architecture/coherence/domain/tree.py` both build their own tag mapping on top of `match_node`.

### 9. Typed Architecture Config Contracts

Modwire's architecture APIs are currently duck-typed around attributes like `config.language`, `config.architecture_root`, `config.rules.tags`, `config.rules.boundaries`, and `config.rules.flow.analyzers`.

Requested API:

- public Protocols or Pydantic models for architecture config
- validation helpers for tags, edge rules, flow rules, and analyzers
- clear exceptions for invalid config instead of attribute errors/assertions
- analyzer metadata beyond just names

Evidence: Enclosure defines its own config models around Modwire expectations in `features/architecture/boundaries/domain.py` and `features/architecture/config/domain.py`.

### 10. Shape Policy Evaluator

Modwire already extracts the data needed for file and symbol shape rules:

- classes, interfaces, types, abstract classes
- functions and methods
- line counts
- optional args and optional properties
- import aliasing
- crossing type
- joined import metadata

Enclosure implements its own shape evaluator using those fields.

Requested API shape:

```python
violations = modwire.shape.ShapePolicyEvaluator().evaluate(code_map, shape_config)
```

Useful built-in rules:

- max classes/functions/types per file
- max methods per class
- max line counts per symbol
- optional argument/property restrictions
- import alias restrictions
- allowed import crossing types
- joined-import enforcement

Evidence: `src/enclosure/features/architecture/shape/domain.py`.

### 11. Higher-Level Architecture Summaries

Enclosure builds reports that could be reusable Modwire primitives:

- module map
- layer map
- cross-module dependencies
- unknown/unmapped files
- dependency hotspots
- pressure clusters
- coherence-style stream analysis

Requested modules:

```python
modwire.architecture.map_code(code_map, config)
modwire.architecture.cluster_code(code_map, group_depth=5)
modwire.architecture.find_hotspots(code_map, config)
```

This should not replace Enclosure's report language, but it would remove repeated low-level graph/tag plumbing.

Evidence:

- `features/architecture/map/domain.py`
- `features/architecture/clusters/domain.py`
- `features/architecture/coherence/domain/*`

### 12. Better Runtime Diagnostics

Enclosure surfaces Modwire failures through CLI error boundaries. More structured runtime diagnostics would make errors clearer.

Requested behavior:

- no `assert` for user-facing validation
- explicit `UnsupportedLanguageError`
- explicit `MissingRuntimeError`
- include command path, command version if available, exit code, stderr, and extractor script path
- expose runtime availability check before extraction

Requested API:

```python
diagnostics = modwire.runtime_diagnostics("typescript")
```

Evidence: `extract_code` asserts that the root exists, and `load_extractor` asserts language support. Extractor execution currently depends on subprocess failure behavior.

### 13. Public Language Metadata

`supported_languages()` is useful, but Enclosure also needs language extensions and runtime requirements for fixtures, config validation, cache keys, and help text.

Requested API:

```python
for language in modwire.languages():
    print(language.name, language.file_extensions, language.command)
```

Expected fields:

- language name
- file extensions
- runtime command
- extractor implementation/version stamp
- whether runtime is currently available

Evidence: Enclosure reaches into `load_extractor(language)` in cache code to obtain `file_extensions`, `command`, and `extractor_file`.

### 14. Public Implementation Stamp

For cache invalidation, Enclosure needs to know when Modwire extraction behavior changed. It currently inspects private implementation files with `inspect.getfile` and paths under `modwire.extractors.base`.

Requested API:

```python
stamp = modwire.extraction_implementation_stamp("python")
```

The stamp should change when any relevant extractor code, schema, or runtime contract changes.

Evidence: `architecture_code_cache._implementation_file_stamps`.

### 15. Report Rendering Hooks

Enclosure reuses `modwire.architecture.render.violations`, but it also needs JSON-ish data and project-specific display labels.

Requested improvements:

- public `violation_to_dict(violation)` with stable `type`
- renderer accepts path display callback
- grouped violation rendering can return structured groups as well as text
- renderers do not require callers to have a full Modwire-shaped report object

Evidence: `src/enclosure/shared/ui.py` and Modwire's `architecture.render`.

### 16. Test Builders / Fixtures

Enclosure tests manually construct `CodeMap`, `DependencyGraph`, `SourceFile`, `SourceImport`, `ExtractionResult`, and `ExtractionSummary`. This is verbose and fragile when Modwire models evolve.

Requested API:

```python
code_map = modwire.testing.code_map(
    files=("sales/orders/domain", "sales/orders/application"),
    edges=(("sales/orders/application", "sales/orders/domain"),),
)
```

Useful helpers:

- minimal `SourceFile`
- minimal `SourceImport`
- code map from file names and edges
- graph from edges
- fixture projects per supported language

Evidence:

- `tests/shared/test_architecture_code_cache.py`
- `tests/features/architecture/coherence/test_domain.py`
- `tests/features/architecture/shape/test_domain.py`

### 17. Version Metadata And API Stability

The installed package does not expose `modwire.__version__`. Enclosure depends on `modwire>=1.1.0`, but cache/debug output and compatibility checks would benefit from runtime version metadata.

Requested additions:

- `modwire.__version__`
- public schema version for serialized extraction output
- documented stability level for modules such as `modwire.definitions`, `modwire.extraction`, `modwire.graph`, and `modwire.architecture.matching`

## Proposed Roadmap

### Near Term

1. Add `modwire.__version__`.
2. Add public language metadata.
3. Add `CodeMap` serialization/deserialization.
4. Add graph helpers: incoming, subgraph, tracked-only edges.
5. Replace user-facing asserts with explicit exceptions.

### Medium Term

1. Add source discovery manifests.
2. Add cached extraction.
3. Add workspace/source-root aware extraction.
4. Add compiled tag matcher.
5. Add implementation stamps for cache invalidation.

### Longer Term

1. Add shape policy evaluation.
2. Add architecture map/cluster/hotspot helpers.
3. Add richer rendering hooks.
4. Add testing factories.

## Highest-Impact Request

If only one area can be addressed first, make it cached extraction with public source discovery and stable `CodeMap` serialization.

That would remove the most integration code from Enclosure, reduce duplicated exclusion semantics, make large repositories faster, and create a reusable foundation for the other requests.
