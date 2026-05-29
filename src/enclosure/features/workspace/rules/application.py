from __future__ import annotations

from pathlib import Path

from enclosure.shared import layout
import enclosure.features.architecture.config
import enclosure.features.workspace.config

from . import domain, infrastructure


def build_rule_schema_report() -> domain.RuleSchemaReport:
    project_root, _config_path, workspace_settings = (
        enclosure.features.workspace.config.load_config()
    )
    policy = domain.RuleSchemaPolicy.from_config(workspace_settings.rules)
    rules_root = layout.current_layout().rules_dir(project_root)
    document_files = infrastructure.file_repository.find(rules_root)
    known_paths = {document.path for document in document_files}
    document_checks = tuple(
        _inspect_document(document, policy, known_paths=known_paths)
        for document in document_files
    )
    checked_documents = _checked_documents(document_checks)
    graph_violations = _graph_violations_by_path(checked_documents)
    documents = tuple(
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
        for document in documents
        if document.exception or bool(document.violations)
    )
    return domain.RuleSchemaReport(
        documents=documents,
        documents_discovered=len(document_files),
        documents_checked=len(documents),
        documents_with_issues=documents_with_issues,
        local_documents_checked=sum(1 for document in documents if document.is_local),
        local_documents_with_issues=sum(
            1
            for document in documents
            if document.is_local and (document.exception or bool(document.violations))
        ),
        local_max_content_chars=policy.local_max_content_chars,
        available_route_tags=domain.available_rule_tags(checked_documents),
        collection_complete=len(documents) == len(document_files),
        has_findings=documents_with_issues > 0,
    )


def build_rule_read_plan(
    tags: tuple[str, ...],
    *,
    paths: tuple[Path, ...] = (),
    task: str = "",
) -> domain.RuleReadPlan:
    project_root, _config_path, _workspace_settings = (
        enclosure.features.workspace.config.load_config()
    )
    _architecture_project_root, _architecture_config_path, architecture_settings = (
        enclosure.features.architecture.config.load_config()
    )
    rules_root = layout.current_layout().rules_dir(project_root)
    document_files = infrastructure.file_repository.find(rules_root)
    documents: list[domain.RuleDocument] = []
    parse_errors: list[str] = []

    for document_file in document_files:
        try:
            documents.append(domain.RuleDocument.from_file(document_file))
        except domain.RuleDocumentParseError as exc:
            parse_errors.append(f"{document_file.path.as_posix()}: {exc}")

    if parse_errors:
        raise ValueError(
            "Rule route planning requires parseable rule documents: "
            + "; ".join(parse_errors)
        )

    tag_selections = (
        domain.explicit_rule_tag_selections(tuple(tags))
        + domain.infer_rule_tag_selections(
            paths=tuple(paths),
            task=task,
            project_root=project_root,
            architecture_root=architecture_settings.architecture_root,
        )
    )
    selected_tags = domain.selected_tags(tag_selections)
    return domain.build_rule_read_plan(
        tuple(documents),
        selected_tags,
        tag_selections,
    )


def _inspect_document(
    document_file: domain.RuleDocumentFile,
    policy: domain.RuleSchemaPolicy,
    *,
    known_paths: set[Path],
) -> domain.RuleDocumentCheck | domain.RuleDocumentReport:
    try:
        document_check = policy.inspect_document(document_file)
        semantic_violations = policy.validate_references(
            document=document_check.document,
            known_paths=known_paths,
        )
        return domain.RuleDocumentCheck(
            document=document_check.document,
            violations=document_check.violations + semantic_violations,
        )
    except domain.RuleDocumentParseError as exc:
        return domain.RuleDocumentReport(
            path=document_file.path,
            scope=(
                domain.RuleDocumentScope.LOCAL
                if document_file.is_local
                else domain.RuleDocumentScope.SHARED
            ),
            is_local=document_file.is_local,
            content_char_count=document_file.content_char_count,
            violations=tuple(
                domain.RuleSchemaViolationReport.model_validate(
                    violation,
                    from_attributes=True,
                )
                for violation in policy.validate_file(document_file)
            ),
            exception=str(exc),
        )


def _map_document_report(
    document_file: domain.RuleDocumentFile,
    document_check: domain.RuleDocumentCheck | domain.RuleDocumentReport,
    *,
    graph_violations: dict[Path, tuple[domain.RuleSchemaViolation, ...]],
) -> domain.RuleDocumentReport:
    if isinstance(document_check, domain.RuleDocumentReport):
        return document_check
    return _report_from_check(
        domain.RuleDocumentCheck(
            document=document_check.document,
            violations=(
                document_check.violations
                + graph_violations.get(document_file.path, ())
            ),
        )
    )


def _checked_documents(
    document_checks: tuple[domain.RuleDocumentCheck | domain.RuleDocumentReport, ...],
) -> tuple[domain.RuleDocument, ...]:
    return tuple(
        document_check.document
        for document_check in document_checks
        if isinstance(document_check, domain.RuleDocumentCheck)
    )


def _graph_violations_by_path(
    documents: tuple[domain.RuleDocument, ...],
) -> dict[Path, tuple[domain.RuleSchemaViolation, ...]]:
    values: dict[Path, list[domain.RuleSchemaViolation]] = {}
    for finding in domain.validate_rule_graph(documents):
        values.setdefault(finding.path, []).append(finding.violation)
    return {path: tuple(violations) for path, violations in values.items()}


def _report_from_check(
    document_check: domain.RuleDocumentCheck,
) -> domain.RuleDocumentReport:
    document = document_check.document
    return domain.RuleDocumentReport(
        path=document.path,
        document_class=document.document_class,
        scope=document.scope,
        is_local=_is_local_path(document.path),
        observed_section_headings=document.observed_section_headings,
        has_navigation_targets=document.has_navigation_targets,
        content_char_count=document.content_char_count,
        violations=tuple(
            domain.RuleSchemaViolationReport.model_validate(
                violation,
                from_attributes=True,
            )
            for violation in document_check.violations
        ),
    )


def _is_local_path(path: Path) -> bool:
    return bool(path.parts and path.parts[0] == domain.RuleDocumentScope.LOCAL.value)


__all__ = [
    "build_rule_read_plan",
    "build_rule_schema_report",
]
