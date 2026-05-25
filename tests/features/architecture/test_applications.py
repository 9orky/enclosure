from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from enclosure.shared import architecture_code


class ArchitectureApplicationTest(unittest.TestCase):
    def test_code_map_errors_are_not_reported_as_successful_reports(self) -> None:
        cases = (
            (
                "enclosure.features.architecture.map.application",
                "build_map_report",
            ),
            (
                "enclosure.features.architecture.boundaries.application",
                "build_boundaries_report",
            ),
            (
                "enclosure.features.architecture.clusters.application",
                "build_clusters_report",
            ),
            (
                "enclosure.features.architecture.health.application",
                "build_health_report",
            ),
            (
                "enclosure.features.architecture.shape.application",
                "build_shape_report",
            ),
        )

        for application_path, builder_name in cases:
            with self.subTest(builder=builder_name):
                application_module = importlib.import_module(application_path)
                project_root = Path("project")
                config = SimpleNamespace(language="python", exclusions=[])
                code_map_error = RuntimeError("code map failed")

                load_config_patch = patch.object(
                    architecture_code.config,
                    "load_project_mapping",
                    return_value=(project_root, Path("enclosure.yaml"), {}),
                )
                validate_mapping_patch = patch(
                    "enclosure.features.architecture.config.domain.ArchitectureConfig.validate_mapping",
                    return_value=config,
                )
                extract_code_patch = patch.object(
                    architecture_code,
                    "extract_code",
                    side_effect=code_map_error,
                )
                load_config_patch.start()
                validate_mapping_patch.start()
                extract_code = extract_code_patch.start()
                try:
                    raised = self.assertRaises(RuntimeError)
                    with raised:
                        getattr(application_module, builder_name)()
                finally:
                    extract_code_patch.stop()
                    validate_mapping_patch.stop()
                    load_config_patch.stop()

                self.assertIs(code_map_error, raised.exception)
                extract_code.assert_called_once_with("python", project_root, ())


if __name__ == "__main__":
    unittest.main()
