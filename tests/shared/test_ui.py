from __future__ import annotations

import unittest
from unittest.mock import patch

from enclosure.shared import ui


class RenderTest(unittest.TestCase):
    def test_render_exposes_mapping_data_as_result_alias(self) -> None:
        with (
            patch.object(ui, "_local_template_text", return_value="{{ result.value }}"),
            patch("typer.echo") as echo,
        ):
            ui.render({"value": "ok"}, template_name="test.tmpl", context={})

        echo.assert_called_once_with("ok")

    def test_render_llm_includes_packaged_enclosure_yaml(self) -> None:
        with (
            patch.object(
                ui,
                "_local_template_text",
                return_value="config:\n```yaml\n{{ config_yaml }}\n```",
            ),
            patch.object(ui.layout, "current_project_root", return_value=None),
            patch("typer.echo") as echo,
        ):
            ui.render_llm("llm.tmpl")

        output = echo.call_args.args[0]
        self.assertIn("architecture:", output)
        self.assertIn("workspace:", output)
        self.assertIn("# Local architecture contract for this repository.", output)

    def test_render_docs_renders_local_template(self) -> None:
        with (
            patch.object(
                ui,
                "_local_template_text",
                return_value="Docs for {{ project_root }}",
            ),
            patch.object(
                ui.layout,
                "current_project_root",
                return_value="repo",
            ),
            patch("typer.echo") as echo,
        ):
            ui.render_docs("docs.tmpl")

        echo.assert_called_once_with("Docs for repo")


if __name__ == "__main__":
    unittest.main()
