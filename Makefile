.PHONY: venv install run debug clean lint lint-strict

PYTHON = uv run python3

venv:
	uv venv

install:
	uv pip install -r requirements.txt
	UV_SKIP_WHEEL_FILENAME_CHECK=1 uv pip install mazegenerator-00001-py3-none-any.whl

run:
	$(PYTHON) pac-man.py config.json

debug:
	$(PYTHON) -m pdb pac-man.py config.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache

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
	$(PYTHON) -m mypy . --strict