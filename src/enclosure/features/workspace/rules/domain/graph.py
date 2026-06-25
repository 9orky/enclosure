from __future__ import annotations

from collections import deque
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from . import documents, inference, references

_SUPPORTED_READ_STRATEGIES = {"progressive"}


class RuleGraphFinding(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    violation: documents.RuleSchemaViolation


class RuleReadStep(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    reason: str
    document_class: documents.RuleDocumentClass
    scope: documents.RuleDocumentScope
    purpose: str
    tags: tuple[str, ...]
    local_supplement: bool = False


class RuleReadPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    requested_tags: tuple[str, ...]
    available_tags: tuple[str, ...]
    steps: tuple[RuleReadStep, ...]
    tag_selections: tuple[inference.RuleTagSelection, ...] = ()
    stop_point: str = ""

    @property
    def found(self) -> bool:
        return bool(self.steps)


def validate_rule_graph(
    documents_: tuple[documents.RuleDocument, ...],
) -> tuple[RuleGraphFinding, ...]:
    documents_by_path = _documents_by_path(documents_)
    known_paths = set(documents_by_path)
    reachable_paths = _reachable_paths(documents_)
    findings: list[RuleGraphFinding] = []

    for document in documents_:
        if (
            document.document_class is documents.RuleDocumentClass.NAVIGATIONAL
            and document.read_directly
            and not document.entrypoint
        ):
            findings.append(
                _finding(
                    document.path,
                    "invalid-direct-read",
                    "Only entrypoint navigational documents may be marked read_directly.",
                )
            )

        if (
            document.document_class is documents.RuleDocumentClass.NAVIGATIONAL
            and document.read_strategy
            and document.read_strategy not in _SUPPORTED_READ_STRATEGIES
        ):
            findings.append(
                _finding(
                    document.path,
                    "unsupported-read-strategy",
                    f"Unsupported read strategy: {document.read_strategy}",
                )
            )

        if (
            document.document_class is documents.RuleDocumentClass.NAVIGATIONAL
            and document.child_references
            and not _known_reference_targets(document.child_references, known_paths)
        ):
            findings.append(
                _finding(
                    document.path,
                    "unusable-navigation-route",
                    "Navigational document has no child target in discovered rules.",
                )
            )

        if document.scope is documents.RuleDocumentScope.LOCAL and not _has_shared_anchor(
            document,
            documents_by_path,
        ):
            findings.append(
                _finding(
                    document.path,
                    "local-rule-without-shared-anchor",
                    "Local rule document must tighten at least one shared rule.",
                )
            )

        if document.path not in reachable_paths:
            findings.append(
                _finding(
                    document.path,
                    "unreachable-rule-document",
                    "Rule document is not reachable from entrypoints or local anchors.",
                )
            )

    return tuple(findings)


def build_rule_read_plan(
    documents_: tuple[documents.RuleDocument, ...],
    requested_tags: tuple[str, ...],
    tag_selections: tuple[inference.RuleTagSelection, ...],
) -> RuleReadPlan:
    normalized_tags = _normalize_tags(requested_tags)
    available_tags = _available_tags(documents_)
    if not normalized_tags:
        return RuleReadPlan(
            requested_tags=(),
            available_tags=available_tags,
            steps=(),
            tag_selections=tag_selections,
        )

    documents_by_path = _documents_by_path(documents_)
    supplements_by_target = _supplements_by_target(documents_, documents_by_path)
    parent_paths = _navigation_parent_paths(documents_, documents_by_path)
    target_documents = _route_targets(documents_, normalized_tags, documents_by_path)
    step_paths: list[tuple[Path, bool, str]] = []
    seen: set[Path] = set()

    for target in target_documents:
        path = parent_paths.get(target.path, (target.path,))
        for index, path_item in enumerate(path):
            document = documents_by_path.get(path_item)
            if document is None:
                continue
            reason = _route_reason(
                document,
                target,
                requested_tags=normalized_tags,
                is_target=index == len(path) - 1,
            )
            _append_step_path(step_paths, seen, path_item, False, reason)
            _append_local_supplements(
                step_paths,
                seen,
                path_item,
                supplements_by_target,
            )

    steps = tuple(
        RuleReadStep(
            path=path,
            reason=reason,
            document_class=documents_by_path[path].document_class,
            scope=documents_by_path[path].scope,
            purpose=documents_by_path[path].purpose,
            tags=documents_by_path[path].tags,
            local_supplement=local_supplement,
        )
        for path, local_supplement, reason in step_paths
        if path in documents_by_path
    )
    return RuleReadPlan(
        requested_tags=normalized_tags,
        available_tags=available_tags,
        steps=steps,
        tag_selections=tag_selections,
        stop_point=steps[-1].path.as_posix() if steps else "",
    )


def available_rule_tags(
    documents_: tuple[documents.RuleDocument, ...],
) -> tuple[str, ...]:
    return _available_tags(documents_)


def _documents_by_path(
    documents_: tuple[documents.RuleDocument, ...],
) -> dict[Path, documents.RuleDocument]:
    return {document.path: document for document in documents_}


def _known_reference_targets(
    references_: tuple[references.RuleReference, ...],
    known_paths: set[Path],
) -> tuple[Path, ...]:
    return tuple(
        target
        for reference in references_
        for target in (references.resolve_reference_path(reference),)
        if target in known_paths
    )


def _has_shared_anchor(
    document: documents.RuleDocument,
    documents_by_path: dict[Path, documents.RuleDocument],
) -> bool:
    for target_path in _known_reference_targets(
        document.tightens_references,
        set(documents_by_path),
    ):
        target = documents_by_path[target_path]
        if target.scope is documents.RuleDocumentScope.SHARED:
            return True
    return False


def _reachable_paths(documents_: tuple[documents.RuleDocument, ...]) -> set[Path]:
    documents_by_path = _documents_by_path(documents_)
    roots = _route_roots(documents_)
    supplements_by_target = _supplements_by_target(documents_, documents_by_path)
    reachable: set[Path] = set()
    pending = deque(roots)

    while pending:
        path = pending.popleft()
        if path in reachable or path not in documents_by_path:
            continue
        reachable.add(path)
        document = documents_by_path[path]
        pending.extend(_known_reference_targets(document.child_references, set(documents_by_path)))
        pending.extend(supplements_by_target.get(path, ()))

    return reachable


def _route_roots(documents_: tuple[documents.RuleDocument, ...]) -> tuple[Path, ...]:
    roots = [
        document
        for document in documents_
        if document.path == Path("INDEX.md")
        and document.read_directly
    ]
    if roots:
        return tuple(document.path for document in sorted(roots, key=_document_sort_key))

    roots = [
        document
        for document in documents_
        if document.read_directly
    ]
    if not roots:
        roots = [
            document
            for document in documents_
            if document.entrypoint
            and document.scope is documents.RuleDocumentScope.SHARED
        ]
    if not roots:
        roots = [document for document in documents_ if document.entrypoint]
    return tuple(document.path for document in sorted(roots, key=_document_sort_key))


def _supplements_by_target(
    documents_: tuple[documents.RuleDocument, ...],
    documents_by_path: dict[Path, documents.RuleDocument],
) -> dict[Path, tuple[Path, ...]]:
    values: dict[Path, list[Path]] = {}
    known_paths = set(documents_by_path)
    for document in documents_:
        if document.scope is not documents.RuleDocumentScope.LOCAL:
            continue
        for target_path in _known_reference_targets(document.tightens_references, known_paths):
            values.setdefault(target_path, []).append(document.path)
    return {
        path: tuple(sorted(paths, key=lambda item: item.as_posix()))
        for path, paths in values.items()
    }


def _navigation_parent_paths(
    documents_: tuple[documents.RuleDocument, ...],
    documents_by_path: dict[Path, documents.RuleDocument],
) -> dict[Path, tuple[Path, ...]]:
    known_paths = set(documents_by_path)
    parent_paths: dict[Path, tuple[Path, ...]] = {}
    pending = deque((root, (root,)) for root in _route_roots(documents_))

    while pending:
        path, route = pending.popleft()
        if path in parent_paths:
            continue
        if path not in documents_by_path:
            continue
        parent_paths[path] = route
        document = documents_by_path[path]
        for child_path in _known_reference_targets(document.child_references, known_paths):
            pending.append((child_path, route + (child_path,)))

    return parent_paths


def _route_targets(
    documents_: tuple[documents.RuleDocument, ...],
    requested_tags: tuple[str, ...],
    documents_by_path: dict[Path, documents.RuleDocument],
) -> tuple[documents.RuleDocument, ...]:
    selected: list[documents.RuleDocument] = []
    seen: set[Path] = set()
    for requested_tag in requested_tags:
        matching = tuple(
            document
            for document in documents_
            if requested_tag in _normalize_tags(document.tags)
        )
        matching_shared = tuple(
            document
            for document in matching
            if document.scope is documents.RuleDocumentScope.SHARED
        )
        candidates = matching_shared or tuple(
            _shared_anchors_for_local_matches(matching, documents_by_path)
        )
        if not candidates:
            candidates = matching

        navigational_candidates = tuple(
            document
            for document in candidates
            if document.document_class is documents.RuleDocumentClass.NAVIGATIONAL
        )
        if navigational_candidates:
            candidates = (sorted(navigational_candidates, key=_document_sort_key)[0],)

        for document in sorted(candidates, key=_document_sort_key):
            if document.path in seen:
                continue
            seen.add(document.path)
            selected.append(document)
    return tuple(selected)


def _shared_anchors_for_local_matches(
    documents_: tuple[documents.RuleDocument, ...],
    documents_by_path: dict[Path, documents.RuleDocument],
) -> tuple[documents.RuleDocument, ...]:
    anchors: list[documents.RuleDocument] = []
    known_paths = set(documents_by_path)
    for document in documents_:
        if document.scope is not documents.RuleDocumentScope.LOCAL:
            continue
        for target_path in _known_reference_targets(document.tightens_references, known_paths):
            target = documents_by_path[target_path]
            if target.scope is documents.RuleDocumentScope.SHARED:
                anchors.append(target)
    return tuple(anchors)


def _route_reason(
    document: documents.RuleDocument,
    target: documents.RuleDocument,
    *,
    requested_tags: tuple[str, ...],
    is_target: bool,
) -> str:
    if is_target or document.path == target.path:
        matched_tags = tuple(
            tag
            for tag in requested_tags
            if tag in _normalize_tags(document.tags)
        )
        if not matched_tags:
            return "Shared anchor for selected local rule tag."
        tags = ", ".join(matched_tags)
        return f"Selected by tag: {tags}."
    if document.read_directly:
        return "Start at rule entrypoint."
    return "Navigation ancestor for selected rule tag."


def _append_local_supplements(
    step_paths: list[tuple[Path, bool, str]],
    seen: set[Path],
    target_path: Path,
    supplements_by_target: dict[Path, tuple[Path, ...]],
) -> None:
    for supplement_path in supplements_by_target.get(target_path, ()):
        reason = f"Local supplement tightening {target_path.as_posix()}."
        _append_step_path(step_paths, seen, supplement_path, True, reason)
        _append_local_supplements(
            step_paths,
            seen,
            supplement_path,
            supplements_by_target,
        )


def _append_step_path(
    step_paths: list[tuple[Path, bool, str]],
    seen: set[Path],
    path: Path,
    local_supplement: bool,
    reason: str,
) -> None:
    if path in seen:
        return
    seen.add(path)
    step_paths.append((path, local_supplement, reason))


def _available_tags(documents_: tuple[documents.RuleDocument, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                tag.strip().lower()
                for document in documents_
                for tag in document.tags
                if tag.strip()
            }
        )
    )


def _normalize_tags(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        tag = value.strip().lower()
        if tag and tag not in normalized:
            normalized.append(tag)
    return tuple(normalized)


def _document_sort_key(document: documents.RuleDocument) -> tuple[int, int, str]:
    return (
        0 if document.path == Path("INDEX.md") else 1,
        len(document.path.parts),
        document.path.as_posix(),
    )


def _finding(path: Path, code: str, message: str) -> RuleGraphFinding:
    return RuleGraphFinding(
        path=path,
        violation=documents.RuleSchemaViolation(
            code=code,
            message=message,
        ),
    )


__all__ = [
    "RuleGraphFinding",
    "RuleReadPlan",
    "RuleReadStep",
    "available_rule_tags",
    "build_rule_read_plan",
    "validate_rule_graph",
]
