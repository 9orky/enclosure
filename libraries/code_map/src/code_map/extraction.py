from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .definitions import SourceFile
from .extractors import load_extractor
from .graph import DependencyGraph, build_dependency_graph


@dataclass(frozen=True)
class ExtractionSummary:
    files_found: int
    files_checked: int
    files_excluded: int


@dataclass(frozen=True)
class ExtractionResult:
    files: dict[str, SourceFile]
    summary: ExtractionSummary


@dataclass(frozen=True)
class CodeMap:
    graph: DependencyGraph
    extraction_result: ExtractionResult
    runtime_command: str


def extract_code(
    language: str,
    sources_root: Path,
    exclusions: tuple[str, ...],
) -> CodeMap:
    """ Extracts the code from the given source root and builds a dependency graph.

    Args:
        language (str): programming language name, supprted are: "python", "javascript", "typescript"
        sources_root (Path): where to look for source files, usually src or lib folder in your project
        exclusions (tuple[str, ...]): glob patterns to exclude files from extraction, e.g. ("**/node_modules/**", "**/dist/**"), relative to sources_root (just like gitignore patterns)
    Returns:
        CodeMap: graph of the codebase and extraction result, including summary and runtime command used for extraction
    """
    assert sources_root.is_dir(), f"Project root {sources_root} is not a directory"

    extractor = load_extractor(language)
    extraction = extractor.extract_files(sources_root, exclusions)
    extracted_files = extraction.files
    dependency_graph = build_dependency_graph(extracted_files)
    
    extraction_result = ExtractionResult(
        files=extracted_files,
        summary=ExtractionSummary(
            files_found=extraction.files_found,
            files_checked=len(extracted_files),
            files_excluded=extraction.files_excluded,
        ),
    )

    return CodeMap(
        graph=dependency_graph,
        extraction_result=extraction_result,
        runtime_command=extractor.command,
    )


__all__ = [
    "CodeMap",
    "ExtractionResult",
    "ExtractionSummary",
    "extract_code",
]
