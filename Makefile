DEV_DIR ?= .dev
DEV_WHEELHOUSE ?= $(DEV_DIR)/wheels
DEV_REFRESH_VERSION ?= 0.0.0.dev0
WARP_MODULE ?= workspace/recipe
WARP_REPORT ?= $(DEV_DIR)/warp/$(subst /,-,$(WARP_MODULE)).html
WARP_ALL_REPORT ?= $(DEV_DIR)/warp/index.html
OPEN ?= open

.PHONY: install generate-module-docs test warp warp-all

install:
	SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ENCLOSURE=$(DEV_REFRESH_VERSION) pipx install --force --editable .
	rm -rf src/*.egg-info src/enclosure/_version.py

generate-module-docs:
	uv run python scripts/generate_module_docs.py

test:
	PYTHONDONTWRITEBYTECODE=1 uv run --group dev python -m pytest tests
	PYTHONDONTWRITEBYTECODE=1 uv run enclosure health

warp:
	mkdir -p $(dir $(WARP_REPORT))
	uv run enclosure workspace recipe --bench $(WARP_MODULE) --html $(WARP_REPORT)
	$(OPEN) $(WARP_REPORT)

warp-all:
	mkdir -p $(dir $(WARP_ALL_REPORT))
	uv run enclosure workspace recipe --bench-all --html $(WARP_ALL_REPORT)
	$(OPEN) $(WARP_ALL_REPORT)
