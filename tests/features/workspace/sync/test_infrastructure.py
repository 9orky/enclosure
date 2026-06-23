from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from enclosure.features.workspace.sync import domain, infrastructure
from enclosure.shared.config import settings


class WorkspaceSyncGeneratedAssetValidationTest(unittest.TestCase):
    def test_generated_config_asset_is_validated(self) -> None:
        with self.assertRaisesRegex(ValueError, "Generated config asset"):
            infrastructure.validate_generated_assets(
                config_content="[]",
                bootstrap_instruction_content="# enclosure\n",
                agent_instruction_content="# enclosure\n",
                shared_rule_documents=(),
            )

    def test_generated_instruction_assets_are_validated(self) -> None:
        with self.assertRaisesRegex(ValueError, "copilot-instructions.md"):
            infrastructure.validate_generated_assets(
                config_content=_packaged_config_content(),
                bootstrap_instruction_content="",
                agent_instruction_content="# enclosure\n",
                shared_rule_documents=(),
            )

    def test_generated_shared_rule_assets_are_validated(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid generated rule asset"):
            infrastructure.validate_generated_assets(
                config_content=_packaged_config_content(),
                bootstrap_instruction_content="# enclosure\n",
                agent_instruction_content="# enclosure\n",
                shared_rule_documents=(
                    domain.SharedRuleDocument(
                        shared_rule_path=domain.SharedRulePath(Path("INDEX.md")),
                        content="# Missing Frontmatter\n",
                    ),
                ),
            )


def _packaged_config_content() -> str:
    raw_data = yaml.safe_load(settings.dump_manifest())
    raw_data["architecture"]["language"] = "python"
    return yaml.dump(raw_data, sort_keys=False)


if __name__ == "__main__":
    unittest.main()
