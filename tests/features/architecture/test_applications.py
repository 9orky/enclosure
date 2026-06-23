from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from modwire import ExtractionCache, SourceRoots

from enclosure.shared import architecture_code
from enclosure.shared.config.metadata import ConfigMetadata


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
                "enclosure.features.architecture.coherence.application",
                "build_coherence_report",
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
                settings = SimpleNamespace(
                    metadata=ConfigMetadata(project_root=project_root),
                    query=lambda path: config,
                )

                settings_patch = patch.object(
                    architecture_code,
                    "settings",
                    settings,
                )
                extract_code_patch = patch.object(
                    architecture_code,
                    "extract_code",
                    side_effect=code_map_error,
                )
                settings_patch.start()
                extract_code = extract_code_patch.start()
                try:
                    raised = self.assertRaises(RuntimeError)
                    with raised:
                        getattr(application_module, builder_name)()
                finally:
                    extract_code_patch.stop()
                    settings_patch.stop()

                self.assertIs(code_map_error, raised.exception)
                extract_code.assert_called_once()
                self.assertEqual(
                    {
                        "language": "python",
                        "sources_root": project_root,
                        "exclusions": (),
                        "source_roots": SourceRoots(workspace_root=project_root),
                        "cache": ExtractionCache(
                            root=project_root
                            / ".enclosure"
                            / ".cache"
                            / "modwire",
                            max_entries=3,
                        ),
                    },
                    extract_code.call_args.kwargs,
                )


if __name__ == "__main__":
    unittest.main()
