from __future__ import annotations

from dataclasses import dataclass, field

from .definitions import SourceFile


@dataclass(frozen=True)
class Node:
    id: str
    kind: str = "file"


@dataclass(frozen=True)
class Edge:
    from_id: str
    to_id: str
    kind: str = "import"


@dataclass
class DependencyGraph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    _outgoing_by_node: dict[str, list[Edge]] = field(default_factory=dict)

    def add_node(self, node_id: str, *, kind: str = "file") -> None:
        self.nodes.setdefault(node_id, Node(id=node_id, kind=kind))
        self._outgoing_by_node.setdefault(node_id, [])

    def add_edge(self, from_id: str, to_id: str, *, kind: str = "import") -> None:
        self.add_node(from_id)
        self.add_node(to_id)
        edge = Edge(from_id=from_id, to_id=to_id, kind=kind)
        self.edges.append(edge)
        self._outgoing_by_node[from_id].append(edge)

    def outgoing(self, node_id: str) -> tuple[Edge, ...]:
        return tuple(self._outgoing_by_node.get(node_id, ()))

    def node_ids(self) -> tuple[str, ...]:
        return tuple(self.nodes.keys())


def build_dependency_graph(extracted_files: dict[str, SourceFile]) -> DependencyGraph:
    graph = DependencyGraph()

    for file_path, extracted_file in extracted_files.items():
        graph.add_node(file_path)
        for imported_reference in extracted_file.imports:
            graph.add_edge(file_path, imported_reference.normalized_path)

    return graph


__all__ = ["DependencyGraph", "build_dependency_graph"]
