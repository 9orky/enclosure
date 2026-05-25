#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


def line_span(node: ast.AST) -> int:
    return node.end_lineno - node.lineno + 1


def normalize_module_path(value: str) -> str:
    return value.replace(".", "/").strip("/")


def import_path(node: ast.ImportFrom) -> str:
    return f"{'.' * node.level}{node.module or ''}"


def normalized_import_path(
    import_value: str,
    is_relative: bool,
    file_path: Path,
    sources_root: Path,
) -> str:
    if not is_relative:
        return normalize_module_path(import_value)

    level = len(import_value) - len(import_value.lstrip("."))
    module = import_value[level:]
    package_dir = file_path.parent
    for _ in range(max(level - 1, 0)):
        package_dir = package_dir.parent

    package_path = package_dir.relative_to(sources_root).as_posix()
    module_path = normalize_module_path(module)
    return "/".join(part for part in (package_path, module_path) if part)


def argument_counts(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    exclude_receiver: bool,
) -> tuple[int, int]:
    positional_args = [*node.args.posonlyargs, *node.args.args]
    positional_required_count = len(positional_args) - len(node.args.defaults)
    parameters = [
        (arg.arg, index >= positional_required_count)
        for index, arg in enumerate(positional_args)
    ]
    parameters.extend(
        (arg.arg, default is not None)
        for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
    )
    if node.args.vararg is not None:
        parameters.append((node.args.vararg.arg, True))
    if node.args.kwarg is not None:
        parameters.append((node.args.kwarg.arg, True))

    if exclude_receiver and parameters and parameters[0][0] in {"self", "cls"}:
        parameters = parameters[1:]

    return len(parameters), sum(1 for _, is_optional in parameters if is_optional)


def has_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == name:
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == name:
            return True
    return False


def node_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent_name = node_name(node.value)
        return f"{parent_name}.{node.attr}" if parent_name else node.attr
    return ""


def method_is_abstract(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return has_decorator(node, "abstractmethod")


def class_is_abstract(node: ast.ClassDef) -> bool:
    return any(node_name(base) in {"ABC", "abc.ABC"} for base in node.bases) or any(
        isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        and method_is_abstract(child)
        for child in node.body
    )


def visibility_intent(name: str) -> str:
    if name.startswith("__") and not (name.startswith("__") and name.endswith("__")):
        return "private"
    if name.startswith("_") and not (name.startswith("__") and name.endswith("__")):
        return "protected"
    return "public"


def annotation_is_optional(node: ast.AST | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Constant) and node.value is None:
        return True
    if isinstance(node, ast.Name):
        return node.id in {"None", "Optional"}
    if isinstance(node, ast.Attribute):
        return node.attr == "Optional"
    if isinstance(node, ast.Subscript):
        return annotation_is_optional(node.value) or annotation_is_optional(node.slice)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return annotation_is_optional(node.left) or annotation_is_optional(node.right)
    if isinstance(node, ast.Tuple):
        return any(annotation_is_optional(element) for element in node.elts)
    return False


def value_is_none(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def optional_constructor_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    positional_args = [*node.args.posonlyargs, *node.args.args]
    defaults_by_name = {}
    if node.args.defaults:
        defaults_by_name = {
            arg.arg: default
            for arg, default in zip(
                positional_args[-len(node.args.defaults) :],
                node.args.defaults,
                strict=True,
            )
        }
    optional_names = {
        arg.arg
        for arg in [*positional_args, *node.args.kwonlyargs]
        if annotation_is_optional(arg.annotation)
    }
    optional_names.update(
        name for name, default in defaults_by_name.items() if value_is_none(default)
    )
    optional_names.update(
        arg.arg
        for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
        if value_is_none(default)
    )
    return optional_names


def class_properties(node: ast.ClassDef) -> list[dict[str, object]]:
    properties: dict[str, bool] = {}

    def add_property(name: str, is_optional: bool) -> None:
        properties[name] = properties.get(name, False) or is_optional

    for child in node.body:
        if isinstance(child, ast.AnnAssign):
            target = child.target
            if isinstance(target, ast.Name):
                add_property(
                    target.id,
                    annotation_is_optional(child.annotation)
                    or value_is_none(child.value),
                )
            continue
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    add_property(target.id, value_is_none(child.value))
            continue
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        optional_parameter_names = optional_constructor_parameters(child)
        for descendant in ast.walk(child):
            if isinstance(descendant, ast.AnnAssign):
                target = descendant.target
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in {"self", "cls"}
                ):
                    add_property(
                        target.attr,
                        annotation_is_optional(descendant.annotation)
                        or value_is_none(descendant.value),
                    )
                continue
            if not isinstance(descendant, ast.Assign):
                continue
            is_optional = value_is_none(descendant.value) or (
                isinstance(descendant.value, ast.Name)
                and descendant.value.id in optional_parameter_names
            )
            for target in descendant.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in {"self", "cls"}
                ):
                    add_property(target.attr, is_optional)

    return [
        {"name": name, "is_optional": is_optional}
        for name, is_optional in properties.items()
    ]


def method_definition(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, object]:
    declared_args, optional_args = argument_counts(
        node,
        exclude_receiver=not has_decorator(node, "staticmethod"),
    )
    return {
        "name": node.name,
        "visibility": "public",
        "visibility_intent": visibility_intent(node.name),
        "line_count": line_span(node),
        "declared_args": declared_args,
        "optional_args": optional_args,
    }


def class_definition(node: ast.ClassDef) -> dict[str, object]:
    return {
        "name": node.name,
        "visibility": "public",
        "visibility_intent": visibility_intent(node.name),
        "methods": [
            method_definition(child)
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        ],
        "properties": class_properties(node),
        "line_count": line_span(node),
    }


def abstract_class_definition(node: ast.ClassDef) -> dict[str, object]:
    methods = [
        method_definition(child)
        for child in node.body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    abstract_method_names = {
        child.name
        for child in node.body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        and method_is_abstract(child)
    }
    return {
        "name": node.name,
        "visibility": "public",
        "visibility_intent": visibility_intent(node.name),
        "abstract_methods": [
            method for method in methods if method["name"] in abstract_method_names
        ],
        "concrete_methods": [
            method for method in methods if method["name"] not in abstract_method_names
        ],
        "properties": class_properties(node),
        "line_count": line_span(node),
    }


def function_definition(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, object]:
    declared_args, optional_args = argument_counts(node, exclude_receiver=False)
    return {
        "name": node.name,
        "visibility": "public",
        "visibility_intent": visibility_intent(node.name),
        "line_count": line_span(node),
        "declared_args": declared_args,
        "optional_args": optional_args,
    }


def code_line_count(content: str) -> int:
    return sum(
        1
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def import_join_key(import_path_value: str) -> str:
    return normalize_module_path(import_path_value).rsplit("/", 1)[0]


def collect_imports(
    tree: ast.Module,
    path: Path,
    sources_root: Path,
) -> list[dict[str, object]]:
    imports = []
    for statement_id, node in enumerate(ast.walk(tree), start=1):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    {
                        "path": alias.name,
                        "is_relative": False,
                        "normalized_path": normalized_import_path(
                            alias.name,
                            False,
                            path,
                            sources_root,
                        ),
                        "imported_name": "",
                        "is_aliased": alias.asname is not None,
                        "crossing_type": "module",
                        "file_barrier_crossed": True,
                        "statement_id": statement_id,
                        "join_key": import_join_key(alias.name),
                        "uses_joined_import": False,
                    }
                )
            continue
        if isinstance(node, ast.ImportFrom):
            node_path = import_path(node)
            for alias in node.names:
                imports.append(
                    {
                        "path": node_path,
                        "is_relative": node.level > 0,
                        "normalized_path": normalized_import_path(
                            node_path,
                            node.level > 0,
                            path,
                            sources_root,
                        ),
                        "imported_name": alias.name,
                        "is_aliased": alias.asname is not None,
                        "crossing_type": "symbol",
                        "file_barrier_crossed": True,
                        "statement_id": statement_id,
                        "join_key": node_path,
                        "uses_joined_import": True,
                    }
                )
    return imports


def extract_file(path: Path, sources_root: Path) -> dict[str, object]:
    content = path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(path))
    class_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    classes = [
        class_definition(node)
        for node in class_nodes
        if not class_is_abstract(node)
    ]
    abstract_classes = [
        abstract_class_definition(node)
        for node in class_nodes
        if class_is_abstract(node)
    ]
    functions = [
        function_definition(node)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    return {
        "imports": collect_imports(tree, path, sources_root),
        "classes": classes,
        "interfaces": [],
        "types": [],
        "abstract_classes": abstract_classes,
        "functions": functions,
        "line_count": len(content.splitlines()),
        "code_line_count": code_line_count(content),
        "public_symbol_count": sum(
            1
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        ),
    }


def main() -> int:
    file_path = Path(sys.argv[1]).resolve()
    sources_root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd()
    print(json.dumps(extract_file(file_path, sources_root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
