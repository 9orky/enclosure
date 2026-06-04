DEV_DIR ?= .dev
DEV_WHEELHOUSE ?= $(DEV_DIR)/wheels
DEV_REFRESH_VERSION ?= 0.0.0.dev0

.PHONY: install generate-module-docs test

install:
	SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ENCLOSURE=$(DEV_REFRESH_VERSION) pipx install --force --editable .
	rm -rf src/*.egg-info src/enclosure/_version.py

generate-module-docs:
	uv run python scripts/generate_module_docs.py

test:
	PYTHONDONTWRITEBYTECODE=1 uv run --group dev python -m pytest tests
	PYTHONDONTWRITEBYTECODE=1 uv run enclosure health
