.PHONY: install run debug clean lint lint-strict

PYTHON = python3

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install mazegenerator-00001-py3-none-any.whl

run:
	$(PYTHON) pac-man.py config.json

debug:
	$(PYTHON) -m pdb pac-man.py config.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	$(PYTHON) -m pip uninstall -y mazegenerator

lint:
	$(PYTHON) -m flake8 pac-man.py src
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 pac-man.py src
	$(PYTHON) -m mypy . --strict