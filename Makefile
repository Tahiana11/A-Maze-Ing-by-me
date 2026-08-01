MAZEGEN_DIR := mazegen

SRCS_MAZEGEN := __init__.py generator.py imperfect_generator.py solver.py

WHEEL_SRCS := $(addprefix $(MAZEGEN_DIR)/, $(SRCS_MAZEGEN)) \
    pyproject.toml \
    README.md

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

.DEFAULT_GOAL := $(NAME)

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
	@rm -f $(NAME) mazegen-1.0.0.tar.gz

.PHONY: lint
lint: $(VENV)
	@echo "Check Project Types"
	$(FLAKE8) .
	$(MYPY) . --warn-return-any --warn-unused-ignores \
			--ignore-missing-imports --disallow-untyped-defs \
			--check-untyped-defs

.PHONY: lint-strict
lint-strict: $(VENV)
	@echo "Check Project Types Strict Mode"
	$(FLAKE8) .
	$(MYPY) . --strict

.PHONY: pip-install
pip-install: $(NAME)
	@echo "Installing $(NAME) via pip"
	$(PIP) install --force-reinstall $(NAME)

#----------------------------------------------
# Other Commands
#----------------------------------------------
$(NAME): $(VENV) $(WHEEL_SRCS)
	@echo "Building mazegen wheel (generator, imperfect_generator, solver)"
	$(UV) build --wheel -o .
	@rm -rf dist

#----------------------------------------------
# Dependencies
#----------------------------------------------
$(VENV):
	@$(MAKE) install
