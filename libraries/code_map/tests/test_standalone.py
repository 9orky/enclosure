from __future__ import annotations

import ast
import tomllib
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "code_map"


class StandaloneLibraryTest(unittest.TestCase):
    def test_code_map_source_does_not_import_enclosure(self) -> None:
        enclosure_imports = []
        for path in sorted(PACKAGE_ROOT.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "enclosure" or alias.name.startswith("enclosure."):
                            enclosure_imports.append((path, alias.name))
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    if node.module == "enclosure" or node.module.startswith("enclosure."):
                        enclosure_imports.append((path, node.module))

        self.assertEqual(enclosure_imports, [])

    def test_code_map_package_does_not_depend_on_enclosure(self) -> None:
        metadata = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        dependencies = metadata["project"].get("dependencies", [])
        package_names = {package_name(dependency) for dependency in dependencies}

        self.assertNotIn("enclosure", package_names)


def package_name(dependency: str) -> str:
    return dependency.split("[", 1)[0].split("=", 1)[0].split(">", 1)[0].lower()


if __name__ == "__main__":
    unittest.main()
