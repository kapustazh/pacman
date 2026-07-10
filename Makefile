export UV_SKIP_WHEEL_FILENAME_CHECK=1

.PHONY: venv install run debug clean lint lint-strict re

PYTHON = uv run python3

install:
	uv sync --python 3.12 --all-groups

run:
	$(PYTHON) pac-man.py config.json

debug:
	$(PYTHON) -m pdb pac-man.py config.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

lint:
	$(PYTHON) -m flake8 pac-man.py src
	$(PYTHON) -m mypy . \
	--warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 pac-man.py src
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores --disallow-untyped-defs --check-untyped-defs

re: clean install