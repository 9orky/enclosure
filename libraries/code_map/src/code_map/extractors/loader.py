from .base import SourceExtractor

from .php import PhpExtractor
from .python import PythonExtractor
from .typescript import TypeScriptExtractor


_map: dict[str, type[SourceExtractor]] = {
    "python": PythonExtractor,
    "typescript": TypeScriptExtractor,
    "php": PhpExtractor,
}

_instances: dict[str, SourceExtractor] = {}


def supported_languages() -> tuple[str, ...]:
    return tuple(_map)


def load_extractor(language: str) -> SourceExtractor:
    assert language in _map, f"Unsupported language: {language}"

    if language not in _instances:
        _instances[language] = _map[language]()
    return _instances[language]


def normalize_source_id(language: str, value: str) -> str:
    normalized = value.replace("\\", "/").strip().strip("/")
    return load_extractor(language).normalize_source_id(normalized)
