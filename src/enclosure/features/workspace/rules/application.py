from __future__ import annotations

from pathlib import Path

from modwire.architecture import TagMatcher
from modwire.extractors.loader import load_extractor

from enclosure.features.architecture import flow
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
            path_facts=_path_facts(
                tuple(paths),
                project_root=project_root,
                architecture_settings=architecture_settings,
            ),
            task=task,
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


def _path_facts(
    paths: tuple[Path, ...],
    *,
    project_root: Path,
    architecture_settings: object,
) -> tuple[domain.RulePathFacts, ...]:
    matcher = TagMatcher(architecture_settings)
    architecture_root = getattr(architecture_settings, "architecture_root", "")
    source_suffixes = _source_suffixes(getattr(architecture_settings, "language", ""))
    module_tag_names = _module_tag_names(architecture_settings)
    module_api_tag_names = _module_api_tag_names(architecture_settings)
    layer_tag_names = _layer_tag_names(architecture_settings)
    return tuple(
        _path_fact(
            path,
            project_root=project_root,
            architecture_root=architecture_root,
            source_suffixes=source_suffixes,
            matcher=matcher,
            module_tag_names=module_tag_names,
            module_api_tag_names=module_api_tag_names,
            layer_tag_names=layer_tag_names,
        )
        for path in paths
    )


def _path_fact(
    path: Path,
    *,
    project_root: Path,
    architecture_root: str,
    source_suffixes: tuple[str, ...],
    matcher: TagMatcher,
    module_tag_names: tuple[str, ...],
    module_api_tag_names: tuple[str, ...],
    layer_tag_names: tuple[str, ...],
) -> domain.RulePathFacts:
    relative_path = _relative_project_path(path, project_root)
    parts = relative_path.parts
    label = relative_path.as_posix()
    is_architecture_path = _is_architecture_path(relative_path, architecture_root)
    return domain.RulePathFacts(
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
        and _matches_any(matcher, label, (*module_tag_names, *module_api_tag_names)),
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


def _is_architecture_path(path: Path, architecture_root: str) -> bool:
    try:
        path.relative_to(Path(architecture_root))
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
        for tag_name in flow.configured_module_tags(architecture_settings)
        if tag_name in tag_names
    )


def _module_api_tag_names(architecture_settings: object) -> tuple[str, ...]:
    return tuple(
        tag_name
        for tag_name in _configured_tag_names(architecture_settings)
        if tag_name == "api" or tag_name.endswith("_api")
    )


def _layer_tag_names(architecture_settings: object) -> tuple[str, ...]:
    tag_names = _configured_tag_names(architecture_settings)
    names: list[str] = []
    for realm in flow.configured_realms(architecture_settings):
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
    "build_rule_read_plan",
    "build_rule_schema_report",
]
