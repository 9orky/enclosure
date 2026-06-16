from __future__ import annotations

import re
import shlex
import unittest
from pathlib import Path

from typer.testing import CliRunner

from enclosure.__main__ import app
from enclosure.features.workspace import config as workspace_config
from enclosure.shared import config
from scripts import generate_module_docs


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = PROJECT_ROOT / "src" / "enclosure"
DOC_FILES = (
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs" / "repo" / "CONTRIBUTING.md",
)
GUIDANCE_FILE_GLOBS = (
    "src/enclosure/templates/*.tmpl",
    "src/enclosure/features/**/ui/templates/docs.tmpl",
    "src/enclosure/features/**/ui/templates/llm.tmpl",
    "docs/modules/*.md",
)
GUIDANCE_TEMPLATE_GLOBS = (
    "src/enclosure/templates/*.tmpl",
    "src/enclosure/features/**/ui/templates/docs.tmpl",
    "src/enclosure/features/**/ui/templates/llm.tmpl",
)
ENCLOSURE_COMMAND_PATTERN = re.compile(r"`(enclosure(?:\s+[^`]+)?)`")
MINIMAL_AGENT_INSTRUCTION = (
    "Start in the `.enclosure/` folder and stay anchored there while discovering "
    "project-specific operating guidance."
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

    def test_llm_surfaces_render_successfully(self) -> None:
        runner = CliRunner()

        for command in llm_commands():
            with self.subTest(command="enclosure " + " ".join(command)):
                result = runner.invoke(app, command)

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Guide", result.output)

    def test_documented_enclosure_commands_resolve(self) -> None:
        runner = CliRunner()

        for command in documented_commands():
            with self.subTest(command=" ".join(command)):
                result = runner.invoke(app, validation_command(command))

            self.assertNotEqual(result.exit_code, 2, result.output)

    def test_guidance_enclosure_commands_resolve(self) -> None:
        runner = CliRunner()

        for command, source in documented_guidance_commands():
            with self.subTest(
                command=" ".join(command),
                source=str(source.relative_to(PROJECT_ROOT)),
            ):
                result = runner.invoke(app, validation_command(command))

            self.assertNotEqual(result.exit_code, 2, result.output)

    def test_guidance_templates_stay_reviewable(self) -> None:
        max_template_chars = guidance_max_template_chars()

        for file_path in guidance_template_files():
            with self.subTest(template=str(file_path.relative_to(PROJECT_ROOT))):
                text = file_path.read_text(encoding="utf-8")
                headings = [
                    line
                    for line in text.splitlines()
                    if line.startswith("#") and not line.startswith("###")
                ]

                if max_template_chars >= 0:
                    self.assertLessEqual(
                        len(text),
                        max_template_chars,
                        f"{file_path.relative_to(PROJECT_ROOT)} is too large; split or trim it",
                    )
                self.assertTrue(text.startswith("# "))
                self.assertGreaterEqual(len(headings), 2)

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

    def test_first_run_onboarding_path_is_documented(self) -> None:
        readme_text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        llm_text = (TEMPLATE_ROOT / "templates" / "llm.tmpl").read_text(
            encoding="utf-8"
        )
        expected_commands = (
            "enclosure workspace sync init",
            "enclosure --llm",
            "enclosure workspace rules route --task calibration",
            "enclosure workspace recipe --list",
            "enclosure workspace recipe <name> --show",
            "enclosure workspace recipe <name> <path> --shell",
            "enclosure health",
        )

        for command in expected_commands:
            with self.subTest(command=command, source="README.md"):
                self.assertIn(command, readme_text)

        for command in expected_commands:
            with self.subTest(command=command, source="llm.tmpl"):
                self.assertIn(command, llm_text)

    def test_agent_instruction_assets_stay_minimal(self) -> None:
        instruction_paths = (
            PROJECT_ROOT / "AGENTS.md",
            PROJECT_ROOT / ".github" / "copilot-instructions.md",
            TEMPLATE_ROOT / "resources" / "AGENTS.md",
            TEMPLATE_ROOT / "resources" / "copilot-instructions.md",
        )

        for instruction_path in instruction_paths:
            with self.subTest(path=str(instruction_path.relative_to(PROJECT_ROOT))):
                lines = [
                    line.strip()
                    for line in instruction_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]

                self.assertEqual(("# enclosure", MINIMAL_AGENT_INSTRUCTION), tuple(lines))


def docs_commands() -> tuple[list[str], ...]:
    return (
        ["--docs"],
        ["health", "--docs"],
        ["workspace", "--docs"],
        ["architecture", "--docs"],
        ["workspace", "sync", "--docs"],
        ["workspace", "sync", "init", "--docs"],
        ["workspace", "sync", "update", "--docs"],
        ["workspace", "sync", "migrate", "--docs"],
        ["workspace", "health", "--docs"],
        ["workspace", "plan", "--docs"],
        ["workspace", "recipe", "--docs"],
        ["workspace", "rules", "--docs"],
        ["architecture", "boundaries", "--docs"],
        ["architecture", "shape", "--docs"],
        ["architecture", "map", "--docs"],
        ["architecture", "pressure", "--docs"],
        ["architecture", "clusters", "--docs"],
        ["architecture", "coherence", "--docs"],
        ["architecture", "health", "--docs"],
    )


def llm_commands() -> tuple[list[str], ...]:
    return tuple([*command[:-1], "--llm"] for command in docs_commands())


def documented_commands() -> tuple[list[str], ...]:
    commands: list[list[str]] = []
    for doc_file in DOC_FILES:
        for line in doc_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("enclosure"):
                continue
            commands.append(shlex.split(stripped))
    return tuple(commands)


def documented_guidance_commands() -> tuple[tuple[list[str], Path], ...]:
    commands: list[tuple[list[str], Path]] = []
    for file_path in guidance_files():
        text = file_path.read_text(encoding="utf-8")
        for match in ENCLOSURE_COMMAND_PATTERN.finditer(text):
            command_text = match.group(1).strip().rstrip(".,:;")
            commands.append((shlex.split(command_text), file_path))
    return tuple(commands)


def guidance_files() -> tuple[Path, ...]:
    files: list[Path] = []
    for pattern in GUIDANCE_FILE_GLOBS:
        files.extend(PROJECT_ROOT.glob(pattern))
    return tuple(sorted(set(files)))


def guidance_template_files() -> tuple[Path, ...]:
    files: list[Path] = []
    for pattern in GUIDANCE_TEMPLATE_GLOBS:
        files.extend(PROJECT_ROOT.glob(pattern))
    return tuple(sorted(set(files)))


def guidance_max_template_chars() -> int:
    config_path = PROJECT_ROOT / ".enclosure" / "enclosure.yaml"
    raw_data = config.load_yaml_mapping(
        config_path,
        label="Workspace config",
        error_type=workspace_config.WorkspaceConfigError,
    )
    return workspace_config.WorkspaceConfig.validate_mapping(
        raw_data,
        config_path,
    ).guidance.max_template_chars


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
