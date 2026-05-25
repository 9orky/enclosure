from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, StrictUndefined


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEATURES_ROOT = PROJECT_ROOT / "src" / "enclosure" / "features"
DOCS_ROOT = PROJECT_ROOT / "docs" / "modules"
HEADER = "<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->"

_TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    lstrip_blocks=True,
    trim_blocks=True,
    undefined=StrictUndefined,
)


def main() -> None:
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    generated_paths = {
        render_module_doc(template_path)
        for template_path in sorted(FEATURES_ROOT.glob("**/ui/templates/docs.tmpl"))
    }
    remove_stale_generated_docs(generated_paths)


def render_module_doc(template_path: Path) -> Path:
    module_slug = module_doc_slug(template_path)
    output_path = DOCS_ROOT / f"{module_slug}.md"
    output_path.write_text(module_doc_text(template_path), encoding="utf-8")
    return output_path


def module_doc_text(template_path: Path) -> str:
    rendered = _TEMPLATE_ENVIRONMENT.from_string(
        template_path.read_text(encoding="utf-8")
    ).render(project_root=PROJECT_ROOT)
    return f"{HEADER}\n\n{rendered.rstrip()}\n"


def module_doc_slug(template_path: Path) -> str:
    relative_path = template_path.relative_to(FEATURES_ROOT)
    module_parts = relative_path.parts[:-3]
    if not module_parts:
        raise ValueError(f"Could not resolve module path for {template_path}")
    return "-".join(module_parts)


def remove_stale_generated_docs(generated_paths: set[Path]) -> None:
    for doc_path in DOCS_ROOT.glob("*.md"):
        if doc_path in generated_paths:
            continue
        if doc_path.read_text(encoding="utf-8").startswith(HEADER):
            doc_path.unlink()


if __name__ == "__main__":
    main()
