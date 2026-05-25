from __future__ import annotations

from pathlib import Path

from enclosure.shared import layout
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
    documents = tuple(
        _map_document_report(document, policy, known_paths=known_paths)
        for document in document_files
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
        collection_complete=len(documents) == len(document_files),
        has_findings=documents_with_issues > 0,
    )


def _map_document_report(
    document_file: domain.RuleDocumentFile,
    policy: domain.RuleSchemaPolicy,
    *,
    known_paths: set[Path],
) -> domain.RuleDocumentReport:
    try:
        document_check = policy.inspect_document(document_file)
        semantic_violations = policy.validate_references(
            document=document_check.document,
            known_paths=known_paths,
        )
        return _report_from_check(
            domain.RuleDocumentCheck(
                document=document_check.document,
                violations=document_check.violations + semantic_violations,
            )
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
    "build_rule_schema_report",
]
