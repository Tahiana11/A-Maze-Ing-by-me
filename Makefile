PYTHON = python3
VENV = maze
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP = $(VENV)/bin/pip
MAIN = a_maze_ing.py
DIST_DIR = dist

.PHONY: venv build install run debug clean lint lint-strict

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip

build: venv
	$(VENV_PYTHON) setup.py bdist_wheel

install: build
	$(VENV_PIP) install -r requirements.txt

run:
	$(VENV_PYTHON) $(MAIN) config.txt

debug:
	$(VENV_PYTHON) -m pdb $(MAIN) config.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	rm -rf $(VENV) $(DIST_DIR) build mazegen.egg-info

lint:
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . --strict