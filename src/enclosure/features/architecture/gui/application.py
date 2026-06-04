from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from modwire.architecture import ArchitecturePolicyEvaluator

import enclosure.features.architecture.map
import enclosure.features.architecture.shape
from enclosure.shared import architecture_code

from . import domain


def build_gui_snapshot() -> domain.GuiSnapshot:
    code_analysis = architecture_code.extract_architecture_code()
    return _build_gui_snapshot(code_analysis)


def _build_gui_snapshot(code_analysis: architecture_code.ArchitectureCodeMap) -> domain.GuiSnapshot:
    code_map = code_analysis.code_map
    config = code_analysis.config
    matching_config = code_analysis.matching_config
    graph = architecture_code.tracked_dependency_graph(code_map)
    boundary_findings = tuple(
        ArchitecturePolicyEvaluator().evaluate(graph, matching_config)
    )
    shape_findings = enclosure.features.architecture.shape.evaluate_shape(
        code_map,
        config,
    )
    mapped = enclosure.features.architecture.map.describe_architecture_map(
        code_map.graph,
        matching_config,
        tracked_files=tuple(code_map.extraction_result.files),
        top=-1,
    )
    module_layers = _module_layers(mapped.modules)
    boundary_by_file = _boundary_findings_by_file(boundary_findings)
    shape_by_file = _shape_findings_by_file(shape_findings)

    return domain.GuiSnapshot(
        project_root=code_analysis.project_root,
        architecture_root=_architecture_root_label(code_analysis.project_root, config),
        config_path=code_analysis.config_path,
        files_checked=code_map.extraction_result.summary.files_checked,
        files_excluded=code_map.extraction_result.summary.files_excluded,
        files=tuple(
            _gui_file(
                source_id,
                source_file,
                module_layers,
                boundary_by_file,
                shape_by_file,
            )
            for source_id, source_file in sorted(code_map.extraction_result.files.items())
        ),
        tags=_tags(config.rules.tags),
        boundary_rules=_boundary_rules(config.rules.boundaries),
        flow_layers=tuple(config.rules.flow.layers),
        exclusions=tuple(config.exclusions),
        shape_config=_shape_config(config.shape),
        dependencies=tuple(
            dependency.to_json_dict() for dependency in mapped.dependencies
        ),
        hotspots=tuple(hotspot.to_json_dict() for hotspot in mapped.hotspots),
    )


def _gui_file(
    source_id: str,
    source_file: object,
    module_layers: dict[str, tuple[str, str]],
    boundary_by_file: dict[str, tuple[dict[str, object], ...]],
    shape_by_file: dict[str, tuple[dict[str, object], ...]],
) -> domain.GuiFile:
    module_name, layer_name = module_layers.get(source_id, ("", ""))
    return domain.GuiFile(
        source_id=source_id,
        module_name=module_name,
        layer_name=layer_name,
        symbols=_symbols(source_file),
        imports=_imports(source_file),
        boundary_findings=boundary_by_file.get(source_id, ()),
        shape_findings=shape_by_file.get(source_id, ()),
    )


def _module_layers(modules: tuple[object, ...]) -> dict[str, tuple[str, str]]:
    module_layers: dict[str, tuple[str, str]] = {}
    for module in modules:
        for file_path in module.files:
            module_layers[file_path] = (module.name, "")
        for layer in module.layers:
            for file_path in layer.files:
                module_layers[file_path] = (module.name, layer.name)
    return module_layers


def _symbols(source_file: object) -> tuple[domain.GuiSymbol, ...]:
    symbols: list[domain.GuiSymbol] = []
    for class_definition in source_file.classes:
        symbols.append(_symbol("class", class_definition.name, class_definition.line_count))
        symbols.extend(_member_symbols("method", class_definition.name, class_definition.methods))
        symbols.extend(_property_symbols(class_definition.name, class_definition.properties))
    for abstract_class in source_file.abstract_classes:
        symbols.append(
            _symbol("abstract_class", abstract_class.name, abstract_class.line_count)
        )
        symbols.extend(
            _member_symbols(
                "abstract_method",
                abstract_class.name,
                abstract_class.abstract_methods,
            )
        )
        symbols.extend(
            _member_symbols(
                "method",
                abstract_class.name,
                abstract_class.concrete_methods,
            )
        )
        symbols.extend(_property_symbols(abstract_class.name, abstract_class.properties))
    for interface in source_file.interfaces:
        symbols.append(_symbol("interface", interface.name, interface.line_count))
        symbols.extend(_member_symbols("signature", interface.name, interface.signatures))
        symbols.extend(_member_symbols("method", interface.name, interface.methods))
        symbols.extend(_property_symbols(interface.name, interface.properties))
    for source_type in source_file.types:
        symbols.append(_symbol("type", source_type.name, source_type.line_count))
        symbols.extend(_member_symbols("signature", source_type.name, source_type.signatures))
        symbols.extend(_property_symbols(source_type.name, source_type.properties))
    for function in source_file.functions:
        symbols.append(_symbol("function", function.name, function.line_count))
    return tuple(symbols)


def _member_symbols(
    kind: str,
    owner_name: str,
    members: list[object],
) -> tuple[domain.GuiSymbol, ...]:
    return tuple(
        _symbol(kind, f"{owner_name}.{member.name}", getattr(member, "line_count", 0))
        for member in members
    )


def _property_symbols(
    owner_name: str,
    properties: list[object],
) -> tuple[domain.GuiSymbol, ...]:
    return tuple(
        _symbol("property", f"{owner_name}.{source_property.name}", 0)
        for source_property in properties
    )


def _symbol(kind: str, name: str, line_count: int) -> domain.GuiSymbol:
    return domain.GuiSymbol(kind=kind, name=name, line_count=line_count)


def _imports(source_file: object) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                source_import.join_key
                for source_import in source_file.imports
                if source_import.file_barrier_crossed
            }
        )
    )


def _boundary_findings_by_file(
    findings: tuple[object, ...],
) -> dict[str, tuple[dict[str, object], ...]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for finding in findings:
        finding_data = asdict(finding)
        for source_id in _boundary_finding_source_ids(finding_data):
            grouped.setdefault(source_id, []).append(finding_data)
    return {
        source_id: tuple(items)
        for source_id, items in sorted(grouped.items())
    }


def _boundary_finding_source_ids(finding_data: dict[str, object]) -> tuple[str, ...]:
    source_ids: list[str] = []
    source_id = finding_data.get("source_id")
    target_id = finding_data.get("target_id")
    path = finding_data.get("path")
    if isinstance(source_id, str):
        source_ids.append(source_id)
    if isinstance(target_id, str):
        source_ids.append(target_id)
    if isinstance(path, tuple):
        source_ids.extend(item for item in path if isinstance(item, str))
    return tuple(dict.fromkeys(source_ids))


def _shape_findings_by_file(
    findings: tuple[object, ...],
) -> dict[str, tuple[dict[str, object], ...]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for finding in findings:
        grouped.setdefault(finding.source_id, []).append(finding.to_json_dict())
    return {
        source_id: tuple(items)
        for source_id, items in sorted(grouped.items())
    }


def _tags(tags: list[object]) -> tuple[domain.GuiTag, ...]:
    return tuple(
        domain.GuiTag(
            name=tag.name,
            match=tag.match,
            excluded_patterns=tuple(tag.excluded_patterns),
        )
        for tag in tags
    )


def _boundary_rules(rules: list[object]) -> tuple[domain.GuiBoundaryRule, ...]:
    return tuple(
        domain.GuiBoundaryRule(
            source=rule.source,
            disallow=tuple(rule.disallow),
            allow=tuple(rule.allow),
            allow_same_match=rule.allow_same_match,
        )
        for rule in rules
    )


def _shape_config(shape: object) -> domain.GuiShapeConfig:
    return domain.GuiShapeConfig(
        max_classes_per_file=shape.max_classes_per_file,
        max_interfaces_per_file=shape.max_interfaces_per_file,
        max_types_per_file=shape.max_types_per_file,
        max_abstract_classes_per_file=shape.max_abstract_classes_per_file,
        max_functions_per_file=shape.max_functions_per_file,
        max_methods_per_class=shape.max_methods_per_class,
        max_declared_args_per_function=shape.max_declared_args_per_function,
        max_declared_args_per_method=shape.max_declared_args_per_method,
        max_lines_count_per_function=shape.max_lines_count_per_function,
        max_lines_count_per_method=shape.max_lines_count_per_method,
        max_lines_count_per_class=shape.max_lines_count_per_class,
    )


def _architecture_root_label(project_root: Path, config: object) -> str:
    configured_root = str(getattr(config, "architecture_root", "")).strip("/")
    if configured_root:
        return configured_root
    return project_root.name


__all__ = ["build_gui_snapshot"]
