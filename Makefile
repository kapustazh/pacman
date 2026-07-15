export UV_SKIP_WHEEL_FILENAME_CHECK=1

# Colors
BOLD    := \033[1m
CYAN    := \033[36m
GREEN   := \033[32m
YELLOW  := \033[33m
BLUE    := \033[34m
MAGENTA := \033[35m
RESET   := \033[0m
DIM     := \033[2m

.DEFAULT_GOAL := help

.PHONY: help venv install run run-release debug clean lint lint-strict re build-itch package-itch

PYTHON = uv run python3

help:
	@printf "$(BOLD)$(CYAN)╔══════════════════════════════════════════════════╗$(RESET)\n"
	@printf "$(BOLD)$(CYAN)║$(RESET)  $(BOLD)PAC-MAN — available make targets$(RESET)                $(BOLD)$(CYAN)║$(RESET)\n"
	@printf "$(BOLD)$(CYAN)╚══════════════════════════════════════════════════╝$(RESET)\n"
	@printf "\n"
	@printf "$(BOLD)$(YELLOW)▶ Play$(RESET)\n"
	@printf "  $(GREEN)make run$(RESET)          $(DIM)Start game with config.json$(RESET)\n"
	@printf "  $(GREEN)make run-release$(RESET)  $(DIM)Run packaged build with built-in defaults$(RESET)\n"
	@printf "  $(GREEN)make debug$(RESET)        $(DIM)Start game in the Python debugger (pdb)$(RESET)\n"
	@printf "\n"
	@printf "$(BOLD)$(BLUE)▶ Setup$(RESET)\n"
	@printf "  $(GREEN)make install$(RESET)      $(DIM)Install / sync Python dependencies (uv)$(RESET)\n"
	@printf "  $(GREEN)make re$(RESET)           $(DIM)Clean caches and reinstall dependencies$(RESET)\n"
	@printf "\n"
	@printf "$(BOLD)$(MAGENTA)▶ Release (itch.io)$(RESET)\n"
	@printf "  $(GREEN)make build-itch$(RESET)   $(DIM)Build standalone game → dist/pac-man/$(RESET)\n"
	@printf "  $(GREEN)make package-itch$(RESET) $(DIM)Build + zip for upload → dist/pac-man-linux.zip$(RESET)\n"
	@printf "\n"
	@printf "$(BOLD)$(YELLOW)▶ Quality$(RESET)\n"
	@printf "  $(GREEN)make lint$(RESET)         $(DIM)Run flake8 + mypy$(RESET)\n"
	@printf "  $(GREEN)make lint-strict$(RESET)  $(DIM)Run flake8 + mypy on source only$(RESET)\n"
	@printf "\n"
	@printf "$(BOLD)$(CYAN)▶ Maintenance$(RESET)\n"
	@printf "  $(GREEN)make clean$(RESET)        $(DIM)Remove __pycache__, .pyc, and cache dirs$(RESET)\n"
	@printf "  $(GREEN)make help$(RESET)         $(DIM)Show this menu$(RESET)\n"
	@printf "\n"
	@printf "$(DIM)Run from the project root (where this Makefile lives).$(RESET)\n"

install:
	uv sync --python 3.12 --all-groups

run:
	$(PYTHON) pac-man.py config.json

run-release:
	@test -x dist/pac-man/pac-man || (printf "$(YELLOW)Run make build-itch first.$(RESET)\n" && exit 1)
	./dist/pac-man/pac-man

debug:
	$(PYTHON) -m pdb pac-man.py config.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

lint:
	$(PYTHON) -m flake8 --exclude=.venv
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

build-itch: install
	$(PYTHON) -m PyInstaller --noconfirm pacman.spec

package-itch: build-itch
	$(PYTHON) -c "import shutil; shutil.make_archive('dist/pac-man-linux', 'zip', 'dist', 'pac-man')"