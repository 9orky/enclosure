from __future__ import annotations

from pathlib import Path

from modwire.architecture import TagMatcher
from modwire.extractors.loader import load_extractor

from enclosure.shared import architecture
from enclosure.shared.config import settings

from . import infrastructure
from .domain import documents, graph, inference, metadata, policy


def build_rule_schema_report() -> documents.RuleSchemaReport:
    workspace_settings = settings.query("workspace")
    rule_schema_policy = policy.RuleSchemaPolicy.from_config(workspace_settings.rules)
    rules_root = settings.metadata.rules_dir
    document_files = infrastructure.file_repository.find(rules_root)
    known_paths = {document.path for document in document_files}
    document_checks = tuple(
        _inspect_document(document, rule_schema_policy, known_paths=known_paths)
        for document in document_files
    )
    checked_documents = _checked_documents(document_checks)
    graph_violations = _graph_violations_by_path(checked_documents)
    document_reports = tuple(
        _map_document_report(
            document_file,
            document_check,
            graph_violations=graph_violations,
        )
        for document_file, document_check in zip(
            document_files,
            document_checks,
            strict=True,
        )
    )
    documents_with_issues = sum(
        1
        for document in document_reports
        if document.exception or bool(document.violations)
    )
    return documents.RuleSchemaReport(
        documents=document_reports,
        documents_discovered=len(document_files),
        documents_checked=len(document_reports),
        documents_with_issues=documents_with_issues,
        local_documents_checked=sum(
            1 for document in document_reports if document.is_local
        ),
        local_documents_with_issues=sum(
            1
            for document in document_reports
            if document.is_local and (document.exception or bool(document.violations))
        ),
        local_max_content_chars=rule_schema_policy.local_max_content_chars,
        available_route_tags=graph.available_rule_tags(checked_documents),
        collection_complete=len(document_reports) == len(document_files),
        has_findings=documents_with_issues > 0,
    )


def build_rule_read_route(
    tags: tuple[str, ...],
    *,
    paths: tuple[Path, ...],
    task: str,
) -> graph.RuleReadRoute:
    project_root = settings.metadata.project_root
    architecture_settings = settings.query("architecture")
    rules_root = settings.metadata.rules_dir
    document_files = infrastructure.file_repository.find(rules_root)
    rule_documents: list[documents.RuleDocument] = []
    parse_errors: list[str] = []

    for document_file in document_files:
        try:
            rule_documents.append(documents.RuleDocument.from_file(document_file))
        except metadata.RuleDocumentParseError as exc:
            parse_errors.append(f"{document_file.path.as_posix()}: {exc}")

    if parse_errors:
        raise ValueError(
            "Rule routing requires parseable rule documents: "
            + "; ".join(parse_errors)
        )

    tag_selections = (
        inference.explicit_rule_tag_selections(tuple(tags))
        + inference.infer_rule_tag_selections(
            path_facts=_path_facts(
                tuple(paths),
                project_root=project_root,
                architecture_settings=architecture_settings,
            ),
            task=task,
        )
    )
    selected_tags = inference.selected_tags(tag_selections)
    return graph.build_rule_read_route(
        tuple(rule_documents),
        selected_tags,
        tag_selections,
    )


def _inspect_document(
    document_file: documents.RuleDocumentFile,
    policy: policy.RuleSchemaPolicy,
    *,
    known_paths: set[Path],
) -> documents.RuleDocumentCheck | documents.RuleDocumentReport:
    try:
        document_check = policy.inspect_document(document_file)
        semantic_violations = policy.validate_references(
            document=document_check.document,
            known_paths=known_paths,
        )
        return documents.RuleDocumentCheck(
            document=document_check.document,
            violations=document_check.violations + semantic_violations,
        )
    except metadata.RuleDocumentParseError as exc:
        return documents.RuleDocumentReport(
            path=document_file.path,
            scope=(
                documents.RuleDocumentScope.LOCAL
                if document_file.is_local
                else documents.RuleDocumentScope.SHARED
            ),
            is_local=document_file.is_local,
            content_char_count=document_file.content_char_count,
            violations=tuple(
                documents.RuleSchemaViolationReport.model_validate(
                    violation,
                    from_attributes=True,
                )
                for violation in policy.validate_file(document_file)
            ),
            exception=str(exc),
        )


def _map_document_report(
    document_file: documents.RuleDocumentFile,
    document_check: documents.RuleDocumentCheck | documents.RuleDocumentReport,
    *,
    graph_violations: dict[Path, tuple[documents.RuleSchemaViolation, ...]],
) -> documents.RuleDocumentReport:
    if isinstance(document_check, documents.RuleDocumentReport):
        return document_check
    return _report_from_check(
        documents.RuleDocumentCheck(
            document=document_check.document,
            violations=(
                document_check.violations
                + graph_violations.get(document_file.path, ())
            ),
        )
    )


def _checked_documents(
    document_checks: tuple[
        documents.RuleDocumentCheck | documents.RuleDocumentReport,
        ...,
    ],
) -> tuple[documents.RuleDocument, ...]:
    return tuple(
        document_check.document
        for document_check in document_checks
        if isinstance(document_check, documents.RuleDocumentCheck)
    )


def _graph_violations_by_path(
    rule_documents: tuple[documents.RuleDocument, ...],
) -> dict[Path, tuple[documents.RuleSchemaViolation, ...]]:
    values: dict[Path, list[documents.RuleSchemaViolation]] = {}
    for finding in graph.validate_rule_graph(rule_documents):
        values.setdefault(finding.path, []).append(finding.violation)
    return {path: tuple(violations) for path, violations in values.items()}


def _report_from_check(
    document_check: documents.RuleDocumentCheck,
) -> documents.RuleDocumentReport:
    document = document_check.document
    return documents.RuleDocumentReport(
        path=document.path,
        document_class=document.document_class,
        scope=document.scope,
        is_local=_is_local_path(document.path),
        observed_section_headings=document.observed_section_headings,
        has_navigation_targets=document.has_navigation_targets,
        content_char_count=document.content_char_count,
        violations=tuple(
            documents.RuleSchemaViolationReport.model_validate(
                violation,
                from_attributes=True,
            )
            for violation in document_check.violations
        ),
    )


def _is_local_path(path: Path) -> bool:
    return bool(
        path.parts and path.parts[0] == documents.RuleDocumentScope.LOCAL.value
    )


def _path_facts(
    paths: tuple[Path, ...],
    *,
    project_root: Path,
    architecture_settings: object,
) -> tuple[inference.RulePathFacts, ...]:
    matcher = TagMatcher(architecture_settings)
    architecture_root = _relative_project_path(
        settings.architecture_root(),
        project_root,
    )
    source_suffixes = _source_suffixes(getattr(architecture_settings, "language", ""))
    module_tag_names = _module_tag_names(architecture_settings)
    public_seam_tag_names = _public_seam_tag_names(architecture_settings)
    layer_tag_names = _layer_tag_names(architecture_settings)
    return tuple(
        _path_fact(
            path,
            project_root=project_root,
            architecture_root=architecture_root,
            source_suffixes=source_suffixes,
            matcher=matcher,
            module_tag_names=module_tag_names,
            public_seam_tag_names=public_seam_tag_names,
            layer_tag_names=layer_tag_names,
        )
        for path in paths
    )


def _path_fact(
    path: Path,
    *,
    project_root: Path,
    architecture_root: Path,
    source_suffixes: tuple[str, ...],
    matcher: TagMatcher,
    module_tag_names: tuple[str, ...],
    public_seam_tag_names: tuple[str, ...],
    layer_tag_names: tuple[str, ...],
) -> inference.RulePathFacts:
    relative_path = _relative_project_path(path, project_root)
    parts = relative_path.parts
    label = relative_path.as_posix()
    is_architecture_path = _is_architecture_path(relative_path, architecture_root)
    return inference.RulePathFacts(
        relative_path=label,
        is_workspace_rules_path=len(parts) >= 2
        and parts[0] == ".enclosure"
        and parts[1] == "rules",
        is_workspace_recipe_path=len(parts) >= 2
        and parts[0] == ".enclosure"
        and parts[1] == "recipes",
        is_architecture_contract_path=len(parts) >= 2
        and parts[0] == ".enclosure"
        and parts[1].startswith("enclosure."),
        is_test_path=bool(parts and parts[0] in {"test", "tests"}),
        is_architecture_path=is_architecture_path,
        is_configured_source_file=relative_path.suffix in source_suffixes,
        matches_module=is_architecture_path
        and _matches_any(matcher, label, (*module_tag_names, *public_seam_tag_names)),
        matches_layer=is_architecture_path
        and _matches_any(matcher, label, layer_tag_names),
    )


def _relative_project_path(path: Path, project_root: Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        try:
            return candidate.resolve(strict=False).relative_to(project_root)
        except ValueError:
            return candidate
    return candidate


def _is_architecture_path(path: Path, architecture_root: Path) -> bool:
    try:
        path.relative_to(architecture_root)
        return True
    except ValueError:
        return False


def _source_suffixes(language: str) -> tuple[str, ...]:
    if not language:
        return ()
    return tuple(load_extractor(language).file_extensions)


def _module_tag_names(architecture_settings: object) -> tuple[str, ...]:
    tag_names = _configured_tag_names(architecture_settings)
    return tuple(
        tag_name
        for tag_name in architecture.configured_module_tags(
            architecture_settings,
        )
        if tag_name in tag_names
    )


def _public_seam_tag_names(architecture_settings: object) -> tuple[str, ...]:
    public_patterns = set(
        architecture.public_seam_patterns(architecture_settings, "")
    )
    return tuple(
        getattr(rule, "name", "")
        for rule in getattr(getattr(architecture_settings, "rules", object()), "tags", ())
        if getattr(rule, "match", "") in public_patterns
        and getattr(rule, "name", "")
    )


def _layer_tag_names(architecture_settings: object) -> tuple[str, ...]:
    tag_names = _configured_tag_names(architecture_settings)
    names: list[str] = []
    for realm in architecture.configured_realms(architecture_settings):
        names.extend(realm.layers)
    return tuple(
        dict.fromkeys(tag_name for tag_name in names if tag_name in tag_names)
    )


def _configured_tag_names(architecture_settings: object) -> set[str]:
    return {
        getattr(rule, "name", "")
        for rule in getattr(getattr(architecture_settings, "rules", object()), "tags", ())
        if getattr(rule, "name", "")
    }


def _matches_any(
    matcher: TagMatcher,
    path: str,
    tag_names: tuple[str, ...],
) -> bool:
    return any(matcher.match(path, tag_name) is not None for tag_name in tag_names)


__all__ = [
    "build_rule_read_route",
    "build_rule_schema_report",
]
