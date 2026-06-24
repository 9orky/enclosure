from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath


class HexagonalLayer(StrEnum):
    APPLICATION = "application"
    ADAPTER = "adapter"
    DOMAIN = "domain"
    INFRASTRUCTURE = "infrastructure"
    PORT = "port"
    SHARED = "shared"
    UI = "ui"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DependencyDecision:
    allowed: bool
    requires_port: bool


@dataclass(frozen=True)
class DependencyRule:
    source: HexagonalLayer
    allowed_targets: tuple[HexagonalLayer, ...]
    port_required_targets: tuple[HexagonalLayer, ...]

    def applies_to(self, source: HexagonalLayer) -> bool:
        return self.source == source

    def decide(self, target: HexagonalLayer) -> DependencyDecision:
        return DependencyDecision(
            allowed=target in self.allowed_targets,
            requires_port=target in self.port_required_targets,
        )


@dataclass(frozen=True)
class DependencyPolicy:
    rules: tuple[DependencyRule, ...]

    def decide(
        self,
        source: HexagonalLayer,
        target: HexagonalLayer,
    ) -> DependencyDecision:
        for rule in self.rules:
            if rule.applies_to(source):
                return rule.decide(target)
        return DependencyDecision(allowed=False, requires_port=False)


class DependencyLayerClassifier:
    def classify(self, reference: str) -> HexagonalLayer:
        terms = self._terms_from(reference)
        if "ports" in terms or reference.endswith("Port"):
            return HexagonalLayer.PORT
        if "adapters" in terms or reference.endswith("Adapter"):
            return HexagonalLayer.ADAPTER
        for layer in HexagonalLayer:
            if layer is HexagonalLayer.UNKNOWN:
                continue
            if layer.value in terms:
                return layer
        return HexagonalLayer.UNKNOWN

    def _terms_from(self, reference: str) -> tuple[str, ...]:
        normalized = reference.replace("\\", "/").replace(".", "/")
        parts = tuple(
            part
            for part in PurePosixPath(normalized).parts
            if part not in {"", "."}
        )
        stems = tuple(PurePosixPath(part).stem for part in parts)
        return tuple(dict.fromkeys((*parts, *stems)))


class HexagonalDependencyRule:
    def __init__(self) -> None:
        self._classifier = DependencyLayerClassifier()
        self._policy = DependencyPolicy(
            rules=(
                DependencyRule(
                    HexagonalLayer.SHARED,
                    (HexagonalLayer.SHARED,),
                    (),
                ),
                DependencyRule(
                    HexagonalLayer.DOMAIN,
                    (HexagonalLayer.DOMAIN, HexagonalLayer.SHARED),
                    (),
                ),
                DependencyRule(
                    HexagonalLayer.PORT,
                    (
                        HexagonalLayer.PORT,
                        HexagonalLayer.DOMAIN,
                        HexagonalLayer.SHARED,
                    ),
                    (),
                ),
                DependencyRule(
                    HexagonalLayer.APPLICATION,
                    (
                        HexagonalLayer.APPLICATION,
                        HexagonalLayer.DOMAIN,
                        HexagonalLayer.PORT,
                        HexagonalLayer.SHARED,
                    ),
                    (HexagonalLayer.ADAPTER, HexagonalLayer.INFRASTRUCTURE),
                ),
                DependencyRule(
                    HexagonalLayer.INFRASTRUCTURE,
                    (
                        HexagonalLayer.INFRASTRUCTURE,
                        HexagonalLayer.DOMAIN,
                        HexagonalLayer.PORT,
                        HexagonalLayer.SHARED,
                    ),
                    (),
                ),
                DependencyRule(
                    HexagonalLayer.ADAPTER,
                    (
                        HexagonalLayer.ADAPTER,
                        HexagonalLayer.INFRASTRUCTURE,
                        HexagonalLayer.DOMAIN,
                        HexagonalLayer.PORT,
                        HexagonalLayer.SHARED,
                    ),
                    (),
                ),
                DependencyRule(
                    HexagonalLayer.UI,
                    (
                        HexagonalLayer.UI,
                        HexagonalLayer.APPLICATION,
                        HexagonalLayer.DOMAIN,
                        HexagonalLayer.PORT,
                        HexagonalLayer.SHARED,
                    ),
                    (),
                ),
            )
        )

    def allows(self, source: str, target: str) -> bool:
        return self._decision_for(source, target).allowed

    def requires_port(self, source: str, target: str) -> bool:
        return self._decision_for(source, target).requires_port

    def _decision_for(self, source: str, target: str) -> DependencyDecision:
        return self._policy.decide(
            self._classifier.classify(source),
            self._classifier.classify(target),
        )


__all__ = [
    "DependencyDecision",
    "DependencyLayerClassifier",
    "DependencyPolicy",
    "DependencyRule",
    "HexagonalDependencyRule",
    "HexagonalLayer",
]
