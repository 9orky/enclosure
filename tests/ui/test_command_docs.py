from __future__ import annotations

import re
import shlex
import unittest
from pathlib import Path

from typer.testing import CliRunner

from enclosure.__main__ import app
from scripts import generate_module_docs


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = PROJECT_ROOT / "src" / "enclosure"
DOC_FILES = (
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs" / "repo" / "CONTRIBUTING.md",
)


class CommandDocsTest(unittest.TestCase):
    def test_docs_surfaces_render_successfully(self) -> None:
        runner = CliRunner()

        for command in docs_commands():
            with self.subTest(command="enclosure " + " ".join(command)):
                result = runner.invoke(app, command)

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Docs", result.output)

    def test_every_llm_template_has_human_docs_template(self) -> None:
        llm_templates = tuple(TEMPLATE_ROOT.glob("**/llm.tmpl"))

        self.assertGreater(len(llm_templates), 0)
        for llm_template in llm_templates:
            with self.subTest(template=str(llm_template.relative_to(PROJECT_ROOT))):
                docs_template = llm_template.with_name("docs.tmpl")

            self.assertTrue(
                docs_template.is_file(),
                f"{docs_template.relative_to(PROJECT_ROOT)} is missing",
            )

    def test_documented_enclosure_commands_resolve(self) -> None:
        runner = CliRunner()

        for command in documented_commands():
            with self.subTest(command=" ".join(command)):
                result = runner.invoke(app, validation_command(command))

            self.assertNotEqual(result.exit_code, 2, result.output)

    def test_generated_module_docs_match_feature_templates(self) -> None:
        template_paths = tuple(
            sorted((TEMPLATE_ROOT / "features").glob("**/ui/templates/docs.tmpl"))
        )
        expected_doc_paths = {
            PROJECT_ROOT
            / "docs"
            / "modules"
            / f"{generate_module_docs.module_doc_slug(template_path)}.md"
            for template_path in template_paths
        }
        actual_doc_paths = set((PROJECT_ROOT / "docs" / "modules").glob("*.md"))

        self.assertEqual(expected_doc_paths, actual_doc_paths)
        for template_path in template_paths:
            doc_path = (
                PROJECT_ROOT
                / "docs"
                / "modules"
                / f"{generate_module_docs.module_doc_slug(template_path)}.md"
            )
            with self.subTest(doc=str(doc_path.relative_to(PROJECT_ROOT))):
                self.assertEqual(
                    generate_module_docs.module_doc_text(template_path),
                    doc_path.read_text(encoding="utf-8"),
                )


def docs_commands() -> tuple[list[str], ...]:
    return (
        ["--docs"],
        ["workspace", "--docs"],
        ["architecture", "--docs"],
        ["workspace", "sync", "--docs"],
        ["workspace", "sync", "init", "--docs"],
        ["workspace", "sync", "update", "--docs"],
        ["workspace", "recipe", "--docs"],
        ["workspace", "rules", "--docs"],
        ["architecture", "boundaries", "--docs"],
        ["architecture", "shape", "--docs"],
        ["architecture", "map", "--docs"],
        ["architecture", "clusters", "--docs"],
        ["architecture", "health", "--docs"],
    )


def documented_commands() -> tuple[list[str], ...]:
    commands: list[list[str]] = []
    for doc_file in DOC_FILES:
        for line in doc_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("enclosure"):
                continue
            commands.append(shlex.split(stripped))
    return tuple(commands)


def validation_command(command: list[str]) -> list[str]:
    tokens = command[1:]
    if not tokens:
        return ["--help"]

    command_path: list[str] = []
    options: list[str] = []
    for token in tokens:
        if token.startswith("<"):
            continue
        if token.startswith("--"):
            options.append(token)
            continue
        if "=" in token or re.match(r"^[A-Z_]+=", token):
            continue
        if options:
            continue
        command_path.append(token)

    return [*command_path, *options, "--help"]


if __name__ == "__main__":
    unittest.main()
