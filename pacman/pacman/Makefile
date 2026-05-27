.PHONY: install run debug clean lint lint-strict

PYTHON = python3

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) pac-man.py config.json

debug:
	$(PYTHON) -m pdb pac-man.py config.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache

lint:
	flake8 pac-man.py src
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 pac-man.py src
	mypy . --strict