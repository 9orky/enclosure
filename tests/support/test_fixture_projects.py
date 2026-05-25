from __future__ import annotations

from pathlib import Path
import shutil

import pytest
from code_map import extract_code, supported_languages

from tests.support.projects import fixture_project_names


def test_minimal_fixture_project_exists_for_every_supported_language() -> None:
    fixture_names = set(fixture_project_names())

    assert {
        f"minimal-{language}"
        for language in supported_languages()
    }.issubset(fixture_names)


@pytest.mark.parametrize("language", supported_languages())
def test_minimal_fixture_project_exercises_code_map_elements(
    fixture_project,
    language: str,
) -> None:
    runtime = {"typescript": "node", "php": "php"}.get(language)
    if runtime is not None and shutil.which(runtime) is None:
        pytest.skip(f"{runtime} runtime is not available")

    project = fixture_project(f"minimal-{language}")
    result = extract_code(language, project.root, ("ignored/**",))
    source_files = result.extraction_result.files
    elements = _code_map_elements(source_files)

    assert result.extraction_result.summary.files_found == _source_file_count(
        project.root,
        language,
    )
    assert result.extraction_result.summary.files_excluded == _source_file_count(
        project.root / "ignored",
        language,
    )
    assert result.extraction_result.summary.files_checked == len(source_files)
    assert all(not source_id.startswith("ignored/") for source_id in source_files)
    assert all(source.line_count > 0 for source in source_files.values())
    assert all(source.code_line_count > 0 for source in source_files.values())
    assert elements["imports"]
    assert elements["classes"]
    assert elements["functions"]
    assert elements["methods"]
    assert elements["properties"]
    assert any("Activation" in name for name in elements["classes"])


def _code_map_elements(source_files) -> dict[str, set[str]]:
    elements: dict[str, set[str]] = {
        "imports": set(),
        "classes": set(),
        "functions": set(),
        "methods": set(),
        "properties": set(),
    }

    for source in source_files.values():
        elements["imports"].update(source_import.path for source_import in source.imports)
        elements["classes"].update(source_class.name for source_class in source.classes)
        elements["functions"].update(source_function.name for source_function in source.functions)
        for source_class in source.classes:
            elements["methods"].update(method.name for method in source_class.methods)
            elements["properties"].update(
                property_item.name for property_item in source_class.properties
            )
        for abstract_class in getattr(source, "abstract_classes", ()):
            elements["classes"].add(abstract_class.name)
            elements["methods"].update(
                method.name
                for method in (
                    *abstract_class.abstract_methods,
                    *abstract_class.concrete_methods,
                )
            )
            elements["properties"].update(
                property_item.name for property_item in abstract_class.properties
            )

    return elements


def _source_file_count(root: Path, language: str) -> int:
    suffixes = {
        "python": (".py",),
        "typescript": (".js", ".jsx", ".ts", ".tsx"),
        "php": (".php",),
    }[language]
    if not root.is_dir():
        return 0
    return sum(1 for path in root.rglob("*") if path.suffix in suffixes)
