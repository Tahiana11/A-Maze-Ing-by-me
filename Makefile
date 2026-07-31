SRCS_DIR := src
MAZEGEN_DIR := $(SRCS_DIR)/mazegen
EXCEPTIONS_DIR := $(SRCS_DIR)/exception
GRAPHIC_DIR := $(SRCS_DIR)/graphic

SRCS_ALGORITHM := __init__.py algorithm_generator.py \
                backtracking.py prim.py maze_resolver.py
SRCS_MAZEGEN_EXCEPTION := config_exception.py maze_exception.py
SRCS_SERVICE := __init__.py config_parser.py generator_utils.py file_generator.py
SRCS_EXCEPTION := __init__.py args_exception.py mlx_exception.py
SRCS_GRAPHIC := __init__.py mlx_utils.py mlx_window.py ui_manager.py maze_renderer.py \
                ui/mlx_component.py ui/mlx_button.py

SRCS := $(addprefix $(MAZEGEN_DIR)/algorithm/, $(SRCS_ALGORITHM)) \
    $(addprefix $(MAZEGEN_DIR)/exception/, $(SRCS_MAZEGEN_EXCEPTION)) \
    $(addprefix $(MAZEGEN_DIR)/service/, $(SRCS_SERVICE)) \
    $(addprefix $(EXCEPTIONS_DIR)/, $(SRCS_EXCEPTION)) \
    $(addprefix $(GRAPHIC_DIR)/, $(SRCS_GRAPHIC)) \
    $(MAZEGEN_DIR)/maze_generator.py \
    $(SRCS_DIR)/maze_app.py \
    $(SRCS_DIR)/__init__.py \
    a_maze_ing.py

VENV := .venv
VENV_BIN := @$(VENV)/bin

PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
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
	. $(VENV)/bin/activate && pip install --upgrade pip
	. $(VENV)/bin/activate && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
	. $(VENV)/bin/activate && if [ -f lib/mlx-2.2-py3-none-any.whl ]; then pip install lib/mlx-2.2-py3-none-any.whl; else echo "Warning: lib/mlx-2.2-py3-none-any.whl not found, skipping local install."; fi

.PHONY: run
run: $(VENV)
	$(PYTHON) a_maze_ing.py config.txt

.PHONY: debug
debug: $(VENV)
	$(PDB) a_maze_ing.py config.txt

.PHONY: clean
clean:
	@echo "Cleaning project"
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@rm -rf .mypy_cache .pytest_cache
	@rm -rf src/mazegen.egg-info
	@rm -rf .venv
	@rm -f maze.txt

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

#----------------------------------------------
# Other Commands
#----------------------------------------------
$(NAME): $(VENV) $(SRCS)
	@echo "Building project"
	$(PYTHON) -m build
	@cp dist/$(NAME) .
	@cp dist/mazegen-1.0.0.tar.gz .
	@rm -rf dist

#----------------------------------------------
# Dependencies
#----------------------------------------------
$(VENV):
	@$(MAKE) install
