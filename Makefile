MAZEGEN_DIR := mazegen
UTILS_DIR := utils
DISPLAY_DIR := display
MAIN_SRC := a_maze_ing.py
SRCS_MAZEGEN := __init__.py generator.py imperfect_generator.py solver.py
SRCS_UTILS := config_parser.py maze_writer.py
SRCS_DISPLAY := mlx_view.py
WHEEL_SRCS := $(addprefix $(MAZEGEN_DIR)/, $(SRCS_MAZEGEN)) \
    pyproject.toml \
    README.md
LINT_SRCS := $(MAIN_SRC) \
    $(addprefix $(DISPLAY_DIR)/, $(SRCS_DISPLAY)) \
    $(addprefix $(MAZEGEN_DIR)/, $(SRCS_MAZEGEN)) \
    $(addprefix $(UTILS_DIR)/, $(SRCS_UTILS))
SRCS := $(WHEEL_SRCS)

VENV := .venv
VENV_BIN := @$(VENV)/bin

PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
UV := $(VENV_BIN)/uv
PDB := $(PYTHON) -m pdb
FLAKE8 := $(VENV_BIN)/flake8
MYPY := $(VENV_BIN)/mypy

NAME := mazegen-1.0.0-py3-none-any.whl
WHEEL_DIR := lib
WHEEL := $(WHEEL_DIR)/$(NAME)

TARBALL_NAME := mazegen.tar.gz
TARBALL := $(WHEEL_DIR)/$(TARBALL_NAME)

.DEFAULT_GOAL := $(WHEEL)

#----------------------------------------------
# Main Commands
#----------------------------------------------
.PHONY: install
install:
	@echo "Creating virtual environment and installing dependencies"
	python3 -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip uv
	. $(VENV)/bin/activate && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
	. $(VENV)/bin/activate && if [ -f lib/mlx-2.2-py3-none-any.whl ]; then pip install lib/mlx-2.2-py3-none-any.whl; else echo "Warning: lib/mlx-2.2-py3-none-any.whl not found, skipping local install."; fi

.PHONY: run
run: pip-install
	$(PYTHON) a_maze_ing.py config.txt

.PHONY: debug
debug: pip-install
	$(PDB) a_maze_ing.py config.txt

.PHONY: clean
clean:
	@echo "Cleaning project"
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@rm -rf .mypy_cache .pytest_cache
	@rm -rf mazegen.egg-info dist
	@rm -rf .venv
	@rm -f maze.txt

.PHONY: lint
lint: $(VENV)
	@echo "Check Project Types"
	$(FLAKE8) $(LINT_SRCS)
	$(MYPY) $(LINT_SRCS) --warn-return-any --warn-unused-ignores \
			--ignore-missing-imports --disallow-untyped-defs \
			--check-untyped-defs \
			--explicit-package-bases

.PHONY: lint-strict
lint-strict: $(VENV)
	@echo "Check Project Types Strict Mode"
	$(FLAKE8) $(LINT_SRCS)
	$(MYPY) $(LINT_SRCS) --explicit-package-bases \
	--strict

.PHONY: pip-install
pip-install: $(WHEEL)
	@echo "Installing $(NAME) via pip"
	$(PIP) install --force-reinstall $(WHEEL)

.PHONY: tarball
tarball: $(TARBALL)

#----------------------------------------------
# Other Commands
#----------------------------------------------
$(WHEEL): $(VENV) $(WHEEL_SRCS)
	@echo "Building mazegen wheel (generator, imperfect_generator, solver)"
	@mkdir -p $(WHEEL_DIR)
	$(UV) build --wheel -o $(WHEEL_DIR)
	@rm -rf $(WHEEL_DIR)/.gitignore

$(TARBALL): $(addprefix $(MAZEGEN_DIR)/, $(SRCS_MAZEGEN))
	@echo "Archiving $(MAZEGEN_DIR)/ into $(TARBALL)"
	@mkdir -p $(WHEEL_DIR)
	tar -czf $(TARBALL) --exclude='__pycache__' $(MAZEGEN_DIR)

#----------------------------------------------
# Dependencies
#----------------------------------------------
$(VENV):
	@$(MAKE) install