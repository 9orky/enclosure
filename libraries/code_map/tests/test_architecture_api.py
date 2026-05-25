from __future__ import annotations

import unittest

from code_map.architecture import (
    ArchitecturePolicyEvaluator,
    EdgeRuleViolation,
    FlowViolation,
    supported_analyzers,
)


class ArchitectureApiTest(unittest.TestCase):
    def test_architecture_package_exports_policy_and_violation_types(self) -> None:
        self.assertIsNotNone(ArchitecturePolicyEvaluator)
        self.assertEqual(
            EdgeRuleViolation(
                source_id="src/app",
                target_id="src/domain",
                source_pattern="src/*",
                target_pattern="src/*",
                rule_name="feature-boundary",
            ).rule_name,
            "feature-boundary",
        )
        self.assertEqual(
            FlowViolation(
                violation_type="backward-flow",
                path=("src/ui", "src/domain"),
                violation_index=0,
                rule_name="analyzer:backward-flow",
                message="src/ui points backward to src/domain",
            ).message,
            "src/ui points backward to src/domain",
        )
        self.assertEqual(
            supported_analyzers(),
            ("backward-flow", "no-reentry", "no-cycles"),
        )


if __name__ == "__main__":
    unittest.main()
