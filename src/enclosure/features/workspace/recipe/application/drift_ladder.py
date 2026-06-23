from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from enclosure.shared.scaffolding import Scaffold
from . import catalog


def drift_files_for(
    recipe: Scaffold,
    *,
    recipes_by_name: Mapping[str, Scaffold],
    expected_files: set[str],
    actual_files: set[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ladder = catalog.composed_ladder_for(recipe, recipes_by_name)
    if not ladder.is_declared():
        return (
            tuple(sorted(expected_files - actual_files)),
            tuple(sorted(actual_files - expected_files)),
        )

    required_files = set(expected_files)
    allowed_files = set(expected_files)
    allowed_prefixes: set[str] = set()
    forbidden_file_stems: set[str] = set()
    forbidden_prefixes: set[str] = set()

    for slot in ladder.slots:
        slot_path = catalog.slot_name(slot)
        slot_state_value = catalog.slot_state(slot)
        if slot_state_value == "absent":
            forbidden_file_stems.add(slot_path)
            forbidden_prefixes.add(f"{slot_path}/")
            continue

        if slot_state_value == "file":
            forbidden_prefixes.add(f"{slot_path}/")
            continue

        if slot_state_value == "package":
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_file_stems.add(slot_path)
            continue

        if slot_state_value == "split-files":
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_file_stems.add(slot_path)
            for slot_file in slot.files:
                slot_file_path = f"{slot_path}/{slot_file}"
                required_files.add(slot_file_path)
                allowed_files.add(slot_file_path)
                if Path(slot_file).suffix:
                    forbidden_prefixes.add(
                        f"{slot_path}/{Path(slot_file).with_suffix('').as_posix()}/"
                    )
            continue

        if slot_state_value == "split-packages":
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_file_stems.add(slot_path)
            for slot_package in slot.packages:
                slot_package_path = f"{slot_path}/{slot_package}"
                allowed_prefixes.add(f"{slot_package_path}/")
                forbidden_file_stems.add(slot_package_path)

    missing_files = tuple(sorted(required_files - actual_files))
    extra_files = tuple(
        sorted(
            actual_file
            for actual_file in actual_files
            if _is_extra_ladder_file(
                actual_file,
                allowed_files=allowed_files,
                allowed_prefixes=allowed_prefixes,
                forbidden_file_stems=forbidden_file_stems,
                forbidden_prefixes=forbidden_prefixes,
            )
        )
    )
    return missing_files, extra_files


def _is_extra_ladder_file(
    actual_file: str,
    *,
    allowed_files: set[str],
    allowed_prefixes: set[str],
    forbidden_file_stems: set[str],
    forbidden_prefixes: set[str],
) -> bool:
    if _matches_file_stem(actual_file, forbidden_file_stems):
        return True
    if any(actual_file.startswith(prefix) for prefix in forbidden_prefixes):
        return True
    if actual_file in allowed_files:
        return False
    return not any(actual_file.startswith(prefix) for prefix in allowed_prefixes)


def _matches_file_stem(actual_file: str, forbidden_file_stems: set[str]) -> bool:
    if not forbidden_file_stems:
        return False
    actual_path = Path(actual_file)
    if not actual_path.suffix:
        return False
    return actual_path.with_suffix("").as_posix() in forbidden_file_stems


__all__ = ["drift_files_for"]
