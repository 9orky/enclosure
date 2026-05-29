from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from posixpath import normpath

from pydantic import BaseModel, ConfigDict

_MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")


class RuleReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_path: Path
    raw_path: str


def all_references_from(
    document_path: Path,
    metadata: object,
    content: str,
) -> tuple[RuleReference, ...]:
    return references_from(
        document_path,
        (
            tuple(getattr(metadata, "child_paths", ()))
            + tuple(getattr(metadata, "tightens_paths", ()))
            + tuple(getattr(metadata, "escalation_paths", ()))
            + markdown_rule_reference_paths(content)
        ),
    )


def child_references_from(
    document_path: Path,
    metadata: object,
) -> tuple[RuleReference, ...]:
    return references_from(document_path, tuple(getattr(metadata, "child_paths", ())))


def tightens_references_from(
    document_path: Path,
    metadata: object,
) -> tuple[RuleReference, ...]:
    return references_from(
        document_path,
        tuple(getattr(metadata, "tightens_paths", ())),
    )


def escalation_references_from(
    document_path: Path,
    metadata: object,
) -> tuple[RuleReference, ...]:
    return references_from(
        document_path,
        tuple(getattr(metadata, "escalation_paths", ())),
    )


def markdown_references_from(
    document_path: Path,
    content: str,
) -> tuple[RuleReference, ...]:
    return references_from(document_path, markdown_rule_reference_paths(content))


def references_from(
    document_path: Path,
    raw_paths: tuple[str, ...],
) -> tuple[RuleReference, ...]:
    return tuple(
        RuleReference(
            source_path=document_path,
            raw_path=normalize_reference_path(raw_path),
        )
        for raw_path in unique_reference_paths(raw_paths)
    )


def normalize_reference_path(raw_path: str) -> str:
    cleaned = raw_path.strip().split("#", 1)[0].split("?", 1)[0]
    normalized = normpath(cleaned)
    return "." if normalized == "" else normalized


def resolve_reference_path(reference: RuleReference) -> Path | None:
    base_path = PurePosixPath(reference.source_path.as_posix()).parent
    normalized_reference = normpath(str(base_path.joinpath(reference.raw_path)))
    resolved_path = PurePosixPath(normalized_reference)

    if str(resolved_path) == ".":
        return None
    if resolved_path.is_absolute():
        return None
    if resolved_path.suffix != ".md":
        return None
    if any(part == ".." for part in resolved_path.parts):
        return None

    return Path(str(resolved_path))


def markdown_rule_reference_paths(content: str) -> tuple[str, ...]:
    references: list[str] = []
    for match in _MARKDOWN_LINK_PATTERN.finditer(content):
        target = match.group("target").strip()
        if is_external_or_anchor_reference(target):
            continue
        references.append(target)
    return tuple(references)


def has_markdown_link(content: str) -> bool:
    return _MARKDOWN_LINK_PATTERN.search(content) is not None


def is_external_or_anchor_reference(raw_path: str) -> bool:
    return (
        raw_path.startswith("#")
        or raw_path.startswith("mailto:")
        or "://" in raw_path
    )


def unique_reference_paths(raw_paths: tuple[str, ...]) -> tuple[str, ...]:
    unique_paths: list[str] = []
    seen: set[str] = set()
    for raw_path in raw_paths:
        normalized_path = normalize_reference_path(raw_path)
        if normalized_path in seen:
            continue
        seen.add(normalized_path)
        unique_paths.append(raw_path)
    return tuple(unique_paths)


__all__ = [
    "RuleReference",
    "all_references_from",
    "child_references_from",
    "escalation_references_from",
    "has_markdown_link",
    "markdown_references_from",
    "references_from",
    "resolve_reference_path",
    "tightens_references_from",
]
