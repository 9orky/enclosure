PYTHON ?= python3
PIPX ?= pipx
UV ?= uv
DEV_DIR ?= .dev
DEV_WHEELHOUSE ?= $(DEV_DIR)/wheels
UV_CACHE_DIR ?= $(DEV_DIR)/uv-cache
PYTEST ?= $(UV) run --group dev python -m pytest
DEV_REFRESH_VERSION ?= 0.0.0.dev0

.PHONY: dev-refresh docs-modules test

dev-refresh:
	SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ENCLOSURE=$(DEV_REFRESH_VERSION) $(PIPX) install --force --editable .
	rm -rf src/*.egg-info src/enclosure/_version.py

docs-modules:
	UV_CACHE_DIR=$(abspath $(UV_CACHE_DIR)) $(UV) run python scripts/generate_module_docs.py

test:
	UV_CACHE_DIR=$(UV_CACHE_DIR) PYTHONDONTWRITEBYTECODE=1 $(PYTEST) tests
