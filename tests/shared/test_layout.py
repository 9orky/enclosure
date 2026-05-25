from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from enclosure.shared.layout import EnclosureProjectLayout


class EnclosureProjectLayoutTest(unittest.TestCase):
    def test_enclosure_directory_is_the_project_contract_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory).resolve()
            contract_root = project_root / ".enclosure"
            contract_root.mkdir()
            (contract_root / "enclosure.yaml").write_text("workspace: {}\n")

            project_layout = EnclosureProjectLayout()

            self.assertEqual(
                project_root,
                project_layout.discover_project_root(contract_root),
            )
            self.assertEqual(contract_root, project_layout.target_dir(project_root))
            self.assertEqual(project_root / ".dev", project_layout.dev_dir(project_root))
            self.assertEqual(
                project_root / ".dev" / "cache",
                project_layout.cache_dir(project_root),
            )
            self.assertEqual(
                (contract_root / "enclosure.yaml", contract_root / "enclosure.yml"),
                project_layout.config_candidate_paths(project_root),
            )
            self.assertNotIn(
                "enclosure/enclosure.yaml",
                project_layout.config_candidate_labels(),
            )


if __name__ == "__main__":
    unittest.main()
