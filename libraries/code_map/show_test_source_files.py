from __future__ import annotations

import json
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).parent
APPS_ROOT = PACKAGE_ROOT / "tests" / "apps"

sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from code_map import extract_code  # noqa: E402


def main() -> int:
    for language in ("python", "typescript", "php"):
        result = extract_code(language, APPS_ROOT / language, ("ignored/**",))
        print(f"\n=== {language.upper()} SourceFile JSONs ===")
        for source_id, source_file in sorted(result.extraction_result.files.items()):
            print(f"\n--- {source_id} ---")
            print(json.dumps(source_file.model_dump(), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
