from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from modwire.architecture import ArchitecturePolicyEvaluator


@dataclass(frozen=True)
class ArchitectureRealm:
    name: str
    module_tag: str
    layers: tuple[str, ...]


def configured_realms(config: object) -> tuple[ArchitectureRealm, ...]:
    flow = getattr(getattr(config, "rules", object()), "flow", object())
    default_layers = tuple(getattr(flow, "layers", ()) or ())
    realms: list[ArchitectureRealm] = []

    for realm in getattr(flow, "realms", ()) or ():
        module_tag = getattr(realm, "module_tag", "")
        if not module_tag:
            continue
        realm_layers = _configured_realm_layers(realm, default_layers)
        realms.append(
            ArchitectureRealm(
                name=getattr(realm, "name", "") or module_tag,
                module_tag=module_tag,
                layers=realm_layers,
            )
        )

    for module_tag in getattr(flow, "module_tags", ()) or ():
        if module_tag:
            realms.append(
                ArchitectureRealm(
                    name=module_tag,
                    module_tag=module_tag,
                    layers=default_layers,
                )
            )

    legacy_module_tag = getattr(flow, "module_tag", "")
    if legacy_module_tag:
        realms.append(
            ArchitectureRealm(
                name=legacy_module_tag,
                module_tag=legacy_module_tag,
                layers=default_layers,
            )
        )

    return _dedupe_realms(tuple(realms))


def configured_module_tags(config: object) -> tuple[str, ...]:
    return tuple(realm.module_tag for realm in configured_realms(config))


def _configured_realm_layers(
    realm: object,
    default_layers: tuple[str, ...],
) -> tuple[str, ...]:
    fields_set = getattr(realm, "model_fields_set", None)
    if fields_set is not None:
        if "layers" not in fields_set:
            return default_layers
        return tuple(getattr(realm, "layers", ()) or ())

    realm_layers = getattr(realm, "layers", None)
    if realm_layers is None:
        return default_layers
    return tuple(realm_layers)


def public_seam_patterns(
    config: object,
    source_pattern: str,
) -> tuple[str, ...]:
    source_patterns = (source_pattern,) if source_pattern else ()
    specific_patterns = _allowed_patterns(config, source_patterns)
    if specific_patterns:
        return specific_patterns
    return _allowed_patterns(config, ())


def evaluate_policy(graph: object, config: object) -> tuple[object, ...]:
    evaluator = ArchitecturePolicyEvaluator()
    violations: list[object] = list(
        evaluator.evaluate(graph, _policy_config(config, analyzers=(), realm=None))
    )
    flow = getattr(getattr(config, "rules", object()), "flow", object())
    analyzers = tuple(getattr(flow, "analyzers", ()) or ())
    for realm in configured_realms(config):
        realm_analyzers = _realm_analyzers(analyzers, realm)
        if not realm_analyzers:
            continue
        violations.extend(
            evaluator.evaluate(
                graph,
                _policy_config(config, analyzers=realm_analyzers, realm=realm),
            )
        )
    return _dedupe_violations(tuple(violations))


def _realm_analyzers(
    analyzers: tuple[str, ...],
    realm: ArchitectureRealm,
) -> tuple[str, ...]:
    if realm.layers:
        return analyzers
    return tuple(analyzer for analyzer in analyzers if analyzer != "backward-flow")


def _policy_config(
    config: object,
    *,
    analyzers: tuple[str, ...],
    realm: ArchitectureRealm | None,
) -> object:
    rules = getattr(config, "rules")
    return SimpleNamespace(
        language=getattr(config, "language"),
        architecture_root=getattr(config, "architecture_root", ""),
        rules=SimpleNamespace(
            tags=getattr(rules, "tags", ()),
            boundaries=() if realm is not None else getattr(rules, "boundaries", ()),
            flow=SimpleNamespace(
                layers=() if realm is None else realm.layers,
                module_tag="" if realm is None else realm.module_tag,
                analyzers=analyzers,
            ),
        ),
    )


def _dedupe_realms(
    realms: tuple[ArchitectureRealm, ...],
) -> tuple[ArchitectureRealm, ...]:
    seen: set[str] = set()
    unique: list[ArchitectureRealm] = []
    for realm in realms:
        if realm.module_tag in seen:
            continue
        seen.add(realm.module_tag)
        unique.append(realm)
    return tuple(unique)


def _dedupe_violations(violations: tuple[object, ...]) -> tuple[object, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[object] = []
    for violation in violations:
        key = (type(violation).__name__, repr(violation))
        if key in seen:
            continue
        seen.add(key)
        unique.append(violation)
    return tuple(unique)


def _allowed_patterns(
    config: object,
    source_patterns: tuple[str, ...],
) -> tuple[str, ...]:
    patterns: list[str] = []
    for rule in getattr(getattr(config, "rules", object()), "boundaries", ()):
        if source_patterns and getattr(rule, "source", "") not in source_patterns:
            continue
        patterns.extend(getattr(rule, "allow", ()) or ())
    return tuple(dict.fromkeys(patterns))


__all__ = [
    "ArchitectureRealm",
    "configured_module_tags",
    "configured_realms",
    "evaluate_policy",
    "public_seam_patterns",
]
