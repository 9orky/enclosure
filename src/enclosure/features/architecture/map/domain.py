from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from modwire.architecture import TagMatcher
from pydantic import field_validator

from enclosure.shared import architecture, config, limits


class MapConfig(config.StrictConfigModel):
    top: int

    @field_validator("top")
    @classmethod
    def top_is_limit(cls, value: int) -> int:
        return limits.validate_report_limit(value)


@dataclass(frozen=True)
class MappedLayer:
    name: str
    files: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "file_count": len(self.files),
            "files": list(self.files),
        }


@dataclass(frozen=True)
class MappedModule:
    name: str
    files: tuple[str, ...]
    layers: tuple[MappedLayer, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "file_count": len(self.files),
            "files": list(self.files),
            "layers": [layer.to_json_dict() for layer in self.layers],
        }


@dataclass(frozen=True)
class MappedDependency:
    source: str
    target: str
    count: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "target": self.target,
            "count": self.count,
        }


@dataclass(frozen=True)
class ArchitectureHotspot:
    kind: str
    name: str
    detail: str
    score: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "name": self.name,
            "detail": self.detail,
            "score": self.score,
        }


@dataclass(frozen=True)
class ArchitectureMapReport:
    project_root: Path
    config_path: Path
    config_format: str
    language: str
    runtime_command: str = ""
    files_found: int = 0
    files_excluded: int = 0
    files_checked: int = 0
    modules: tuple[MappedModule, ...] = ()
    dependencies: tuple[MappedDependency, ...] = ()
    unknown_files: tuple[str, ...] = ()
    hotspots: tuple[ArchitectureHotspot, ...] = ()
    top: int = 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            **architecture.metadata_json(self),
            "top": self.top,
            "modules": [module.to_json_dict() for module in self.modules],
            "dependencies": [
                dependency.to_json_dict() for dependency in self.dependencies
            ],
            "unknown_files": list(self.unknown_files),
            "hotspots": [hotspot.to_json_dict() for hotspot in self.hotspots],
        }


class ArchitectureMapConfigError(RuntimeError):
    pass


def describe_architecture_map(
    graph,
    config,
    *,
    tracked_files: tuple[str, ...] | None,
    top: int,
) -> "MappedArchitecture":
    tag_names = {rule.name for rule in config.rules.tags}
    module_tag = (
        config.rules.flow.module_tag
        if config.rules.flow.module_tag in tag_names
        else ""
    )
    layer_names = tuple(
        layer_name
        for layer_name in config.rules.flow.layers
        if layer_name in tag_names
    )

    tracked_node_ids = tuple(tracked_files or graph.node_ids())
    matcher = TagMatcher(config)
    file_maps = {
        node_id: _map_file(node_id, matcher, module_tag, layer_names)
        for node_id in tracked_node_ids
    }
    builders: dict[str, _ModuleBuilder] = defaultdict(_ModuleBuilder)
    unknown_files: list[str] = []

    for node_id, file_map in file_maps.items():
        display_path = matcher.display_path(node_id)
        if not file_map.module_name:
            unknown_files.append(display_path)
            continue
        builders[file_map.module_name].add_file(display_path, file_map.layer_name)

    dependency_counts: Counter[tuple[str, str]] = Counter()
    incoming_counts: Counter[str] = Counter()
    outgoing_counts: Counter[str] = Counter()

    for edge in graph.edges:
        source = file_maps.get(edge.from_id)
        target = file_maps.get(edge.to_id)
        if source is None or target is None:
            continue
        if not source.module_name or not target.module_name:
            continue
        if source.module_name == target.module_name:
            continue
        dependency_counts[(source.module_name, target.module_name)] += 1
        outgoing_counts[source.module_name] += 1
        incoming_counts[target.module_name] += 1

    dependencies = tuple(
        MappedDependency(source, target, count)
        for (source, target), count in sorted(
            dependency_counts.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1]),
        )
    )
    modules = tuple(
        sorted(
            (builder.build(name) for name, builder in builders.items()),
            key=lambda module: (module.name),
        )
    )

    return MappedArchitecture(
        modules=modules,
        dependencies=dependencies,
        unknown_files=tuple(sorted(unknown_files)),
        hotspots=_hotspots(
            modules,
            incoming_counts,
            outgoing_counts,
            dependencies,
            unknown_files,
            top=top,
        ),
    )


@dataclass(frozen=True)
class MappedArchitecture:
    modules: tuple[MappedModule, ...]
    dependencies: tuple[MappedDependency, ...]
    unknown_files: tuple[str, ...]
    hotspots: tuple[ArchitectureHotspot, ...]


@dataclass(frozen=True)
class _FileMap:
    module_name: str = ""
    layer_name: str = ""


@dataclass
class _ModuleBuilder:
    files: list[str] = field(default_factory=list)
    files_by_layer: dict[str, list[str]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def add_file(self, file_path: str, layer_name: str) -> None:
        self.files.append(file_path)
        if layer_name:
            self.files_by_layer[layer_name].append(file_path)

    def build(self, name: str) -> MappedModule:
        return MappedModule(
            name=name,
            files=tuple(sorted(self.files)),
            layers=tuple(
                MappedLayer(layer_name, tuple(sorted(files)))
                for layer_name, files in sorted(self.files_by_layer.items())
            ),
        )


def _map_file(
    node_id: str,
    matcher: TagMatcher,
    module_tag: str,
    layer_names: tuple[str, ...],
) -> _FileMap:
    module_name = ""
    if module_tag:
        match = matcher.match(node_id, module_tag)
        if match is not None:
            module_name = matcher.display_path(match.captured_path)

    layer_name = ""
    if layer_match := matcher.first_match(node_id, layer_names):
        layer_name = layer_match.name

    return _FileMap(module_name=module_name, layer_name=layer_name)


def _hotspots(
    modules: tuple[MappedModule, ...],
    incoming_counts: Counter[str],
    outgoing_counts: Counter[str],
    dependencies: tuple[MappedDependency, ...],
    unknown_files: list[str],
    *,
    top: int,
) -> tuple[ArchitectureHotspot, ...]:
    hotspots: list[ArchitectureHotspot] = []
    sorted_modules = sorted(modules, key=lambda item: (-len(item.files), item.name))
    for module in limits.apply_limit(sorted_modules, top):
        if len(module.files) > 1:
            hotspots.append(
                ArchitectureHotspot(
                    kind="module-size",
                    name=module.name,
                    detail=f"{len(module.files)} tracked file(s)",
                    score=len(module.files),
                )
            )
    for name, count in limits.apply_limit(outgoing_counts.most_common(), top):
        hotspots.append(
            ArchitectureHotspot(
                kind="outgoing-dependencies",
                name=name,
                detail=f"{count} outgoing cross-module import(s)",
                score=count,
            )
        )
    for name, count in limits.apply_limit(incoming_counts.most_common(), top):
        hotspots.append(
            ArchitectureHotspot(
                kind="incoming-dependencies",
                name=name,
                detail=f"{count} incoming cross-module import(s)",
                score=count,
            )
        )
    for dependency in limits.apply_limit(dependencies, top):
        hotspots.append(
            ArchitectureHotspot(
                kind="cross-module-edge",
                name=f"{dependency.source} -> {dependency.target}",
                detail=f"{dependency.count} import(s)",
                score=dependency.count,
            )
        )
    if unknown_files:
        hotspots.append(
            ArchitectureHotspot(
                kind="unknown-files",
                name="unmapped",
                detail=f"{len(unknown_files)} file(s) outside module tags",
                score=len(unknown_files),
            )
        )
    return limits.apply_limit(hotspots, top)


__all__ = [
    "ArchitectureHotspot",
    "ArchitectureMapConfigError",
    "ArchitectureMapReport",
    "MapConfig",
    "MappedArchitecture",
    "MappedDependency",
    "MappedLayer",
    "MappedModule",
    "describe_architecture_map",
]
