PYTHON ?= python3
PIPX ?= pipx
UV ?= uv
DEV_DIR ?= .dev
DEV_WHEELHOUSE ?= $(DEV_DIR)/wheels
UV_CACHE_DIR ?= $(DEV_DIR)/uv-cache
PYTEST ?= $(UV) run pytest

.PHONY: dev-refresh docs-modules test

dev-refresh:
	UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) build --wheel --clear --out-dir $(DEV_WHEELHOUSE) libraries/code_map
	$(PIPX) install --force --editable --pip-args="--find-links=$(abspath $(DEV_WHEELHOUSE))" .
	rm -rf libraries/code_map/build libraries/code_map/src/*.egg-info src/*.egg-info

docs-modules:
	UV_CACHE_DIR=$(abspath $(UV_CACHE_DIR)) $(UV) run python scripts/generate_module_docs.py

test:
	UV_CACHE_DIR=$(UV_CACHE_DIR) PYTHONDONTWRITEBYTECODE=1 $(PYTEST) tests libraries/code_map/tests
