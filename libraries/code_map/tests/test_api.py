from __future__ import annotations

import shutil
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from code_map import extract_code, normalize_source_id, supported_languages


APPS_DIR = Path(__file__).parent / "apps"


@dataclass(frozen=True)
class AppFixture:
    language: str
    root: Path
    runtime: str | None = None


class BuildDependencyGraphFunctionalTest(unittest.TestCase):
    def test_source_id_helpers_are_language_aware(self) -> None:
        self.assertEqual(supported_languages(), ("python", "typescript", "php"))
        self.assertEqual(normalize_source_id("python", r"src\app.py"), "src/app")
        self.assertEqual(normalize_source_id("typescript", "src/view.tsx"), "src/view")
        self.assertEqual(normalize_source_id("php", "src/Controller.php"), "src/Controller")

    def test_supported_apps_produce_the_same_dependency_graph(self) -> None:
        graphs_by_language: dict[str, set[tuple[str, str]]] = {}

        for fixture in app_fixtures():
            with self.subTest(language=fixture.language):
                if fixture.runtime is not None and shutil.which(fixture.runtime) is None:
                    self.skipTest(f"{fixture.runtime} runtime is not available")

                result = extract_code(
                    fixture.language,
                    fixture.root,
                    ("ignored/**",),
                )

                graphs_by_language[fixture.language] = internal_edges(result)

                self.assertEqual(
                    result.extraction_result.summary.files_found,
                    count_source_files(fixture.root),
                )
                self.assertEqual(
                    result.extraction_result.summary.files_excluded,
                    count_source_files(fixture.root / "ignored"),
                )
                self.assertEqual(
                    result.extraction_result.summary.files_checked,
                    len(result.extraction_result.files),
                )
                self.assert_has_nested_source_files(result)
                self.assert_has_classes_and_functions(result)
                self.assert_has_metrics(result)
                self.assert_has_import_barrier_metadata(fixture.language, result)
                self.assert_has_import_alias_metadata(fixture.language, result)
                self.assert_has_argument_count_metadata(fixture.language, result)
                self.assert_has_class_property_metadata(fixture.language, result)
                self.assert_has_visibility_metadata(fixture.language, result)

                if fixture.language == "typescript":
                    self.assert_scans_typescript_extensions(result)

        self.assertGreaterEqual(len(graphs_by_language), 2)
        self.assertEqual(len(set(map(frozenset, graphs_by_language.values()))), 1)

    def test_bare_directory_exclusions_are_recursive(self) -> None:
        result = extract_code("python", APPS_DIR / "python", ("ignored",))

        self.assertEqual(
            result.extraction_result.summary.files_excluded,
            count_source_files(APPS_DIR / "python" / "ignored"),
        )
        self.assertTrue(
            all(
                not source_id.startswith("ignored/")
                for source_id in result.extraction_result.files
            )
        )

    def test_python_visibility_distinguishes_accessibility_from_intent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            root.joinpath("sample.py").write_text(
                "class _Internal:\n"
                "    def _guarded(self):\n"
                "        pass\n"
                "    def __hidden(self):\n"
                "        pass\n"
                "    def __str__(self):\n"
                "        return 'internal'\n\n"
                "def _helper():\n"
                "    pass\n\n"
                "def __secret():\n"
                "    pass\n",
                encoding="utf-8",
            )

            result = extract_code("python", root, ())

        self.assertEqual(
            class_visibility(result, "sample", "_Internal"),
            ("public", "protected"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "_Internal", "_guarded"),
            ("public", "protected"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "_Internal", "__hidden"),
            ("public", "private"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "_Internal", "__str__"),
            ("public", "public"),
        )
        self.assertEqual(
            function_visibility(result, "sample", "_helper"),
            ("public", "protected"),
        )
        self.assertEqual(
            function_visibility(result, "sample", "__secret"),
            ("public", "private"),
        )

    def test_typescript_visibility_uses_exports_and_member_modifiers(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node runtime is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            root.joinpath("sample.ts").write_text(
                "export class PublicUser {\n"
                "    public open(): void {}\n"
                "    protected guarded(): void {}\n"
                "    private hidden(): void {}\n"
                "    #hashed(): void {}\n"
                "    _convention(): void {}\n"
                "}\n\n"
                "class LocalUser {}\n\n"
                "export function run(): void {}\n"
                "function local(): void {}\n",
                encoding="utf-8",
            )

            result = extract_code("typescript", root, ())

        self.assertEqual(
            class_visibility(result, "sample", "PublicUser"),
            ("public", "public"),
        )
        self.assertEqual(
            class_visibility(result, "sample", "LocalUser"),
            ("private", "private"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "open"),
            ("public", "public"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "guarded"),
            ("protected", "protected"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "hidden"),
            ("private", "private"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "#hashed"),
            ("private", "private"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "_convention"),
            ("public", "protected"),
        )
        self.assertEqual(
            function_visibility(result, "sample", "run"),
            ("public", "public"),
        )
        self.assertEqual(
            function_visibility(result, "sample", "local"),
            ("private", "private"),
        )

    def test_php_visibility_uses_method_modifiers(self) -> None:
        if shutil.which("php") is None:
            self.skipTest("php runtime is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            root.joinpath("sample.php").write_text(
                "<?php\n"
                "final class PublicUser\n"
                "{\n"
                "    public function open(): void {}\n"
                "    protected function guarded(): void {}\n"
                "    private function hidden(): void {}\n"
                "    public function _convention(): void {}\n"
                "    public function __construct() {}\n"
                "}\n\n"
                "function _helper(): void {}\n",
                encoding="utf-8",
            )

            result = extract_code("php", root, ())

        self.assertEqual(
            class_visibility(result, "sample", "PublicUser"),
            ("public", "public"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "open"),
            ("public", "public"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "guarded"),
            ("protected", "protected"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "hidden"),
            ("private", "private"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "_convention"),
            ("public", "protected"),
        )
        self.assertEqual(
            method_visibility(result, "sample", "PublicUser", "__construct"),
            ("public", "public"),
        )
        self.assertEqual(
            function_visibility(result, "sample", "_helper"),
            ("public", "protected"),
        )

    def test_python_extracts_abstract_classes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            root.joinpath("sample.py").write_text(
                "from abc import ABC, abstractmethod\n\n"
                "class Repository(ABC):\n"
                "    enabled: bool\n\n"
                "    @abstractmethod\n"
                "    def load(self, user_id: str):\n"
                "        raise NotImplementedError\n\n"
                "    def save(self, user_id: str | None = None):\n"
                "        return user_id\n",
                encoding="utf-8",
            )

            result = extract_code("python", root, ())

        source_file = result.extraction_result.files["sample"]
        self.assertEqual(
            [abstract.name for abstract in source_file.abstract_classes],
            ["Repository"],
        )
        self.assertEqual(source_file.classes, [])
        abstract_class = source_file.abstract_classes[0]
        self.assertEqual(
            [method.name for method in abstract_class.abstract_methods],
            ["load"],
        )
        self.assertEqual(
            [method.name for method in abstract_class.concrete_methods],
            ["save"],
        )
        self.assertEqual(
            {
                property.name: property.is_optional
                for property in abstract_class.properties
            },
            {"enabled": False},
        )
        self.assertEqual(source_file.interfaces, [])
        self.assertEqual(source_file.types, [])

    def test_typescript_extracts_interfaces_types_and_abstract_classes(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node runtime is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            root.joinpath("sample.ts").write_text(
                "export interface UserPort extends Runnable {\n"
                "    (id: string, retry?: boolean): User;\n"
                "    new (seed?: User): UserPort;\n"
                "    [key: string]: User;\n"
                "    user?: User;\n"
                "    load(id: string, retry?: boolean): User;\n"
                "}\n\n"
                "export type UserPayload = {\n"
                "    (id: string): User;\n"
                "    [key: string]: User;\n"
                "    id: string;\n"
                "    owner?: User;\n"
                "} & Audited;\n\n"
                "export abstract class BaseRepository {\n"
                "    protected cache?: User;\n"
                "    abstract load(id: string): User;\n"
                "    save(user?: User): void {}\n"
                "}\n",
                encoding="utf-8",
            )

            result = extract_code("typescript", root, ())

        source_file = result.extraction_result.files["sample"]
        self.assertEqual(source_file.classes, [])
        self.assertEqual(
            [interface.name for interface in source_file.interfaces],
            ["UserPort"],
        )
        interface = source_file.interfaces[0]
        self.assertEqual([method.name for method in interface.methods], ["load"])
        self.assertEqual(
            {property.name: property.is_optional for property in interface.properties},
            {"user": True},
        )
        self.assertEqual(
            {
                (signature.kind, signature.declared_args, signature.optional_args)
                for signature in interface.signatures
            },
            {
                ("call", 2, 1),
                ("construct", 1, 1),
                ("index", 1, 0),
            },
        )

        self.assertEqual(
            [source_type.name for source_type in source_file.types],
            ["UserPayload"],
        )
        source_type = source_file.types[0]
        self.assertEqual(
            {
                property.name: property.is_optional
                for property in source_type.properties
            },
            {"id": False, "owner": True},
        )
        self.assertEqual(
            {
                (signature.kind, signature.declared_args, signature.optional_args)
                for signature in source_type.signatures
            },
            {
                ("call", 1, 0),
                ("index", 1, 0),
            },
        )

        self.assertEqual(
            [abstract.name for abstract in source_file.abstract_classes],
            ["BaseRepository"],
        )
        abstract_class = source_file.abstract_classes[0]
        self.assertEqual(
            [method.name for method in abstract_class.abstract_methods],
            ["load"],
        )
        self.assertEqual(
            [method.name for method in abstract_class.concrete_methods],
            ["save"],
        )
        self.assertEqual(
            {
                property.name: property.is_optional
                for property in abstract_class.properties
            },
            {"cache": True},
        )

    def test_php_extracts_interfaces_and_abstract_classes(self) -> None:
        if shutil.which("php") is None:
            self.skipTest("php runtime is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            root.joinpath("sample.php").write_text(
                "<?php\n"
                "interface UserPort extends Runnable\n"
                "{\n"
                "    public const KIND = 'user';\n"
                "    public function load(string $id): User;\n"
                "}\n\n"
                "abstract class BaseRepository\n"
                "{\n"
                "    protected ?string $cache;\n"
                "    abstract protected function load(string $id): User;\n"
                "    public function save(?User $user = null): void {}\n"
                "}\n",
                encoding="utf-8",
            )

            result = extract_code("php", root, ())

        source_file = result.extraction_result.files["sample"]
        self.assertEqual(source_file.classes, [])
        self.assertEqual(
            [interface.name for interface in source_file.interfaces],
            ["UserPort"],
        )
        interface = source_file.interfaces[0]
        self.assertEqual([method.name for method in interface.methods], ["load"])
        self.assertEqual(interface.signatures, [])
        self.assertEqual(source_file.types, [])

        self.assertEqual(
            [abstract.name for abstract in source_file.abstract_classes],
            ["BaseRepository"],
        )
        abstract_class = source_file.abstract_classes[0]
        self.assertEqual(
            [method.name for method in abstract_class.abstract_methods],
            ["load"],
        )
        self.assertEqual(
            [method.name for method in abstract_class.concrete_methods],
            ["save"],
        )
        self.assertEqual(
            {property.name: property.is_optional for property in abstract_class.properties},
            {"cache": True},
        )

    def test_python_absolute_package_imports_resolve_to_known_init_files_without_source_root_assumptions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = root / "packages" / "acme" / "tools"
            package_dir.mkdir(parents=True)
            package_dir.joinpath("__init__.py").write_text(
                "class Tool:\n    pass\n",
                encoding="utf-8",
            )
            service_dir = root / "services"
            service_dir.mkdir()
            service_dir.joinpath("report.py").write_text(
                "from acme.tools import Tool\n\n"
                "class Report:\n"
                "    tool = Tool\n",
                encoding="utf-8",
            )

            result = extract_code("python", root, ())

        self.assertIn(
            ("services/report", "packages/acme/tools/__init__"),
            {
                (edge.from_id, edge.to_id)
                for edge in result.graph.edges
            },
        )

    def test_python_from_import_can_target_a_module_without_symbol_crossing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "src"
            source_dir.mkdir()
            source_dir.joinpath("service.py").write_text(
                "class Service:\n"
                "    pass\n",
                encoding="utf-8",
            )
            source_dir.joinpath("consumer.py").write_text(
                "from src import service\n\n"
                "def build():\n"
                "    return service.Service()\n",
                encoding="utf-8",
            )

            result = extract_code("python", root, ())

        imports = result.extraction_result.files["src/consumer"].imports
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].normalized_path, "src/service")
        self.assertEqual(imports[0].crossing_type, "module")
        self.assertTrue(imports[0].file_barrier_crossed)

    def test_python_import_metadata_distinguishes_joined_and_separate_parent_imports(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shared_dir = root / "enclosure" / "shared"
            shared_dir.mkdir(parents=True)
            shared_dir.joinpath("__init__.py").write_text("", encoding="utf-8")
            shared_dir.joinpath("naming.py").write_text("", encoding="utf-8")
            shared_dir.joinpath("paths.py").write_text("", encoding="utf-8")
            feature_dir = root / "src" / "feature"
            feature_dir.mkdir(parents=True)
            feature_dir.joinpath("__init__.py").write_text(
                "from . import domain\n"
                "from . import ui\n",
                encoding="utf-8",
            )
            feature_dir.joinpath("domain.py").write_text("", encoding="utf-8")
            feature_dir.joinpath("ui.py").write_text("", encoding="utf-8")
            root.joinpath("separate.py").write_text(
                "import enclosure.shared.naming\n"
                "import enclosure.shared.paths\n",
                encoding="utf-8",
            )
            root.joinpath("joined.py").write_text(
                "from enclosure.shared import naming, paths\n",
                encoding="utf-8",
            )

            result = extract_code("python", root, ())

        separate_imports = result.extraction_result.files["separate"].imports
        self.assertEqual(
            {source_import.join_key for source_import in separate_imports},
            {"enclosure/shared"},
        )
        self.assertEqual(
            len({source_import.statement_id for source_import in separate_imports}),
            2,
        )
        self.assertFalse(
            any(source_import.uses_joined_import for source_import in separate_imports)
        )

        joined_imports = result.extraction_result.files["joined"].imports
        self.assertEqual(
            {source_import.join_key for source_import in joined_imports},
            {"enclosure/shared"},
        )
        self.assertEqual(
            len({source_import.statement_id for source_import in joined_imports}),
            1,
        )
        self.assertTrue(
            all(source_import.uses_joined_import for source_import in joined_imports)
        )

        relative_imports = result.extraction_result.files["src/feature/__init__"].imports
        self.assertEqual(
            {source_import.join_key for source_import in relative_imports},
            {"src/feature"},
        )
        self.assertEqual(
            len({source_import.statement_id for source_import in relative_imports}),
            2,
        )

    def test_typescript_import_metadata_tracks_joinable_static_imports(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node runtime is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            domain_dir = root / "src" / "domain"
            domain_dir.mkdir(parents=True)
            domain_dir.joinpath("user.ts").write_text(
                "export class User {}\n"
                "export function buildUser(): User { return new User(); }\n",
                encoding="utf-8",
            )
            interfaces_dir = root / "src" / "interfaces"
            interfaces_dir.mkdir(parents=True)
            interfaces_dir.joinpath("controller.ts").write_text(
                "import { User } from '../domain/user';\n"
                "import { buildUser } from '../domain/user';\n"
                "import * as userModule from '../domain/user';\n"
                "import '../domain/user';\n"
                "const user = require('../domain/user');\n",
                encoding="utf-8",
            )

            result = extract_code("typescript", root, ())

        imports = result.extraction_result.files["src/interfaces/controller"].imports
        joinable_imports = [
            source_import for source_import in imports if source_import.join_key
        ]
        self.assertEqual(len(joinable_imports), 2)
        self.assertEqual(
            {source_import.join_key for source_import in joinable_imports},
            {"src/domain/user"},
        )
        self.assertEqual(
            len({source_import.statement_id for source_import in joinable_imports}),
            2,
        )
        self.assertTrue(
            all(source_import.uses_joined_import for source_import in joinable_imports)
        )

    def test_php_import_metadata_parses_grouped_use_imports(self) -> None:
        if shutil.which("php") is None:
            self.skipTest("php runtime is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model_dir = root / "src" / "domain" / "model"
            model_dir.mkdir(parents=True)
            model_dir.joinpath("user.php").write_text(
                "<?php\nnamespace App\\Domain\\Model;\nclass User {}\n",
                encoding="utf-8",
            )
            model_dir.joinpath("profile.php").write_text(
                "<?php\nnamespace App\\Domain\\Model;\nclass Profile {}\n",
                encoding="utf-8",
            )
            controller_dir = root / "src" / "interfaces"
            controller_dir.mkdir(parents=True)
            controller_dir.joinpath("separate.php").write_text(
                "<?php\n"
                "use App\\Domain\\Model\\User;\n"
                "use App\\Domain\\Model\\Profile;\n",
                encoding="utf-8",
            )
            controller_dir.joinpath("grouped.php").write_text(
                "<?php\n"
                "use App\\Domain\\Model\\{User, Profile};\n",
                encoding="utf-8",
            )

            result = extract_code("php", root, ())

        separate_imports = result.extraction_result.files[
            "src/interfaces/separate"
        ].imports
        self.assertEqual(
            {source_import.join_key for source_import in separate_imports},
            {"src/domain/model"},
        )
        self.assertEqual(
            len({source_import.statement_id for source_import in separate_imports}),
            2,
        )
        self.assertFalse(
            any(source_import.uses_joined_import for source_import in separate_imports)
        )

        grouped_imports = result.extraction_result.files[
            "src/interfaces/grouped"
        ].imports
        self.assertEqual(
            {source_import.join_key for source_import in grouped_imports},
            {"src/domain/model"},
        )
        self.assertEqual(
            len({source_import.statement_id for source_import in grouped_imports}),
            1,
        )
        self.assertTrue(
            all(source_import.uses_joined_import for source_import in grouped_imports)
        )

    def test_php_absolute_imports_resolve_without_app_or_source_root_assumptions(
        self,
    ) -> None:
        if shutil.which("php") is None:
            self.skipTest("php runtime is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model_dir = root / "packages" / "acme" / "domain" / "model"
            model_dir.mkdir(parents=True)
            model_dir.joinpath("user.php").write_text(
                "<?php\n\n"
                "namespace Acme\\Domain\\Model;\n\n"
                "class User {}\n",
                encoding="utf-8",
            )
            controller_dir = root / "web"
            controller_dir.mkdir()
            controller_dir.joinpath("controller.php").write_text(
                "<?php\n\n"
                "namespace Acme\\Web;\n\n"
                "use Acme\\Domain\\Model\\User;\n\n"
                "class Controller\n"
                "{\n"
                "    public function handle(User $user): void {}\n"
                "}\n",
                encoding="utf-8",
            )

            result = extract_code("php", root, ())

        self.assertIn(
            ("web/controller", "packages/acme/domain/model/user"),
            {
                (edge.from_id, edge.to_id)
                for edge in result.graph.edges
            },
        )

    def assert_has_nested_source_files(self, result) -> None:
        depths = {
            len(Path(path).with_suffix("").parts)
            for path in result.extraction_result.files
            if path.startswith("src/")
        }
        self.assertGreaterEqual(max(depths), 4)

    def assert_has_classes_and_functions(self, result) -> None:
        classes = {
            class_definition.name
            for extracted_file in result.extraction_result.files.values()
            for class_definition in extracted_file.classes
        }
        functions = {
            function_definition.name
            for extracted_file in result.extraction_result.files.values()
            for function_definition in extracted_file.functions
        }
        self.assertGreaterEqual(len(classes), 2)
        self.assertGreaterEqual(len(functions), 1)

    def assert_has_metrics(self, result) -> None:
        for source_file in result.extraction_result.files.values():
            self.assertGreater(source_file.line_count, 0)
            self.assertGreater(source_file.code_line_count, 0)
            self.assertGreaterEqual(source_file.public_symbol_count, 0)

    def assert_scans_typescript_extensions(self, result) -> None:
        self.assertIn("src/domain/model/profile", result.extraction_result.files)
        self.assertIn("src/domain/services/audit", result.extraction_result.files)
        self.assertIn("src/interfaces/http/view", result.extraction_result.files)

    def assert_has_import_barrier_metadata(self, language: str, result) -> None:
        if language == "python":
            activate_imports = imports_by_target(
                result,
                "src/application/use_cases/activate",
            )
            self.assertTrue(activate_imports["src/domain/model/user"])
            self.assertTrue(activate_imports["src/domain/services/policy"])
            self.assertFalse(activate_imports["dataclasses"])
            self.assertEqual(
                import_crossing_types_by_target(
                    result,
                    "src/application/use_cases/activate",
                )["src/domain/model/user"],
                {"symbol"},
            )
            return

        if language == "typescript":
            controller_imports = imports_by_target(
                result,
                "src/interfaces/http/controller",
            )
            self.assertTrue(controller_imports["src/application/use_cases/activate"])
            self.assertTrue(controller_imports["src/domain/model/user"])
            self.assertFalse(controller_imports["node:path"])
            self.assertEqual(
                import_crossing_types_by_target(
                    result,
                    "src/interfaces/http/controller",
                )["src/application/use_cases/activate"],
                {"symbol"},
            )
            return

        if language == "php":
            controller_imports = imports_by_target(
                result,
                "src/interfaces/http/controller",
            )
            self.assertTrue(controller_imports["src/application/use_cases/activate"])
            self.assertTrue(controller_imports["src/domain/model/user"])
            self.assertFalse(controller_imports["DateTimeImmutable"])
            self.assertEqual(
                import_crossing_types_by_target(
                    result,
                    "src/interfaces/http/controller",
                )["src/domain/model/user"],
                {"symbol"},
            )
            return

        self.fail(f"Unexpected language: {language}")

    def assert_has_import_alias_metadata(self, language: str, result) -> None:
        controller_aliases = import_aliases_by_target(
            result,
            "src/interfaces/http/controller",
        )

        if language == "python":
            self.assertTrue(controller_aliases["json"])
            self.assertTrue(controller_aliases["src/domain/model/user"])
            self.assertFalse(controller_aliases["src/application/use_cases/activate"])
            return

        if language == "typescript":
            self.assertTrue(controller_aliases["node:path"])
            self.assertTrue(controller_aliases["src/domain/model/user"])
            self.assertFalse(controller_aliases["src/application/use_cases/activate"])
            return

        if language == "php":
            self.assertTrue(controller_aliases["DateTimeImmutable"])
            self.assertTrue(controller_aliases["src/domain/model/user"])
            self.assertFalse(controller_aliases["src/application/use_cases/activate"])
            return

        self.fail(f"Unexpected language: {language}")

    def assert_has_argument_count_metadata(self, language: str, result) -> None:
        if language == "python":
            self.assertEqual(
                method_counts(result, "src/domain/model/user", "User", "__init__"),
                (2, 1),
            )
            self.assertEqual(
                method_counts(result, "src/domain/model/user", "User", "activate"),
                (0, 0),
            )
            self.assertEqual(
                function_counts(
                    result,
                    "src/application/use_cases/activate",
                    "nullable_label",
                ),
                (1, 0),
            )
            return

        if language == "typescript":
            self.assertEqual(
                method_counts(result, "src/domain/model/user", "User", "constructor"),
                (2, 1),
            )
            self.assertEqual(
                method_counts(
                    result,
                    "src/interfaces/http/controller",
                    "ActivationController",
                    "constructor",
                ),
                (1, 0),
            )
            self.assertEqual(
                function_counts(
                    result,
                    "src/application/use_cases/activate",
                    "nullableLabel",
                ),
                (1, 0),
            )
            self.assertEqual(
                function_counts(
                    result,
                    "src/application/use_cases/activate",
                    "optionalLabel",
                ),
                (1, 1),
            )
            return

        if language == "php":
            self.assertEqual(
                method_counts(result, "src/domain/model/user", "User", "__construct"),
                (2, 1),
            )
            self.assertEqual(
                method_counts(result, "src/domain/model/user", "User", "__toString"),
                (0, 0),
            )
            self.assertEqual(
                function_counts(
                    result,
                    "src/application/use_cases/activate",
                    "nullableLabel",
                ),
                (1, 0),
            )
            return

        self.fail(f"Unexpected language: {language}")

    def assert_has_class_property_metadata(self, language: str, result) -> None:
        if language == "python":
            self.assertEqual(
                class_properties(result, "src/domain/model/user", "User"),
                {"user_id": False, "active": False, "nickname": True},
            )
            return

        if language == "typescript":
            self.assertEqual(
                class_properties(result, "src/domain/model/user", "User"),
                {"id": False, "active": False, "nickname": True},
            )
            return

        if language == "php":
            self.assertEqual(
                class_properties(result, "src/domain/model/user", "User"),
                {"nickname": True, "id": False, "active": False},
            )
            return

        self.fail(f"Unexpected language: {language}")

    def assert_has_visibility_metadata(self, language: str, result) -> None:
        self.assertEqual(
            class_visibility(result, "src/domain/model/user", "User"),
            ("public", "public"),
        )

        if language == "typescript":
            self.assertEqual(
                method_visibility(
                    result,
                    "src/domain/model/user",
                    "User",
                    "fingerprint",
                ),
                ("public", "public"),
            )
            return

        if language == "php":
            self.assertEqual(
                method_visibility(
                    result,
                    "src/domain/model/user",
                    "User",
                    "__toString",
                ),
                ("public", "public"),
            )
            return

        if language == "python":
            self.assertEqual(
                method_visibility(
                    result,
                    "src/domain/model/user",
                    "User",
                    "activate",
                ),
                ("public", "public"),
            )
            return

        self.fail(f"Unexpected language: {language}")


def app_fixtures() -> tuple[AppFixture, ...]:
    return (
        AppFixture(language="python", root=APPS_DIR / "python"),
        AppFixture(language="typescript", root=APPS_DIR / "typescript", runtime="node"),
        AppFixture(language="php", root=APPS_DIR / "php", runtime="php"),
    )


def internal_edges(result) -> set[tuple[str, str]]:
    source_files = set(result.extraction_result.files)
    return {
        (edge.from_id, edge.to_id)
        for edge in result.graph.edges
        if edge.from_id in source_files and edge.to_id in source_files
    }


def count_source_files(root: Path) -> int:
    return sum(1 for path in root.rglob("*") if path.suffix in source_extensions())


def source_extensions() -> set[str]:
    return {".py", ".ts", ".tsx", ".js", ".jsx", ".php"}


def imports_by_target(result, source_id: str) -> dict[str, bool]:
    return {
        source_import.normalized_path: source_import.file_barrier_crossed
        for source_import in result.extraction_result.files[source_id].imports
    }


def import_crossing_types_by_target(result, source_id: str) -> dict[str, set[str]]:
    imports: dict[str, set[str]] = {}
    for source_import in result.extraction_result.files[source_id].imports:
        imports.setdefault(source_import.normalized_path, set()).add(
            source_import.crossing_type
        )
    return imports


def import_aliases_by_target(result, source_id: str) -> dict[str, bool]:
    return {
        source_import.normalized_path: source_import.is_aliased
        for source_import in result.extraction_result.files[source_id].imports
    }


def method_counts(
    result,
    source_id: str,
    class_name: str,
    method_name: str,
) -> tuple[int, int]:
    for class_definition in result.extraction_result.files[source_id].classes:
        if class_definition.name != class_name:
            continue
        for method in class_definition.methods:
            if method.name == method_name:
                return method.declared_args, method.optional_args
    raise AssertionError(f"Missing method {source_id}:{class_name}.{method_name}")


def function_counts(result, source_id: str, function_name: str) -> tuple[int, int]:
    for function in result.extraction_result.files[source_id].functions:
        if function.name == function_name:
            return function.declared_args, function.optional_args
    raise AssertionError(f"Missing function {source_id}:{function_name}")


def class_properties(result, source_id: str, class_name: str) -> dict[str, bool]:
    for class_definition in result.extraction_result.files[source_id].classes:
        if class_definition.name == class_name:
            return {
                property_definition.name: property_definition.is_optional
                for property_definition in class_definition.properties
            }
    raise AssertionError(f"Missing class {source_id}:{class_name}")


def class_visibility(result, source_id: str, class_name: str) -> tuple[str, str]:
    for class_definition in result.extraction_result.files[source_id].classes:
        if class_definition.name == class_name:
            return class_definition.visibility, class_definition.visibility_intent
    raise AssertionError(f"Missing class {source_id}:{class_name}")


def method_visibility(
    result,
    source_id: str,
    class_name: str,
    method_name: str,
) -> tuple[str, str]:
    for class_definition in result.extraction_result.files[source_id].classes:
        if class_definition.name != class_name:
            continue
        for method in class_definition.methods:
            if method.name == method_name:
                return method.visibility, method.visibility_intent
    raise AssertionError(f"Missing method {source_id}:{class_name}.{method_name}")


def function_visibility(
    result,
    source_id: str,
    function_name: str,
) -> tuple[str, str]:
    for function in result.extraction_result.files[source_id].functions:
        if function.name == function_name:
            return function.visibility, function.visibility_intent
    raise AssertionError(f"Missing function {source_id}:{function_name}")


if __name__ == "__main__":
    unittest.main()
