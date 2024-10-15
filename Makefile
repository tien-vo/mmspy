NAME := mmspy
MICROMAMBA := $(shell command -v micromamba 2> /dev/null)
CONDA_LOCK := conda-lock.yml
POETRY_LOCK := poetry.lock

.DEFAULT_GOAL := help
.PHONY: help
help:
	@echo "Edit help string"

.PHONY: install
install: pyproject.toml ${POETRY_LOCK} ${CONDA_LOCK}
	@if [ -z ${MICROMAMBA} ]; then \
		echo "Micromamba binary not found!"; \
		echo "See the README or https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html for installation instruction."; \
		exit 1; \
	fi
	@echo "Conda: Creating virtual environment from ${CONDA_LOCK} ..."
	@${MICROMAMBA} create \
		--yes \
		--override-channels \
		--name ${NAME} \
		--file ${CONDA_LOCK}
	@echo "Poetry: Installing packages from ${POETRY_LOCK} ..."
	@${MICROMAMBA} run -n ${NAME} poetry install
	@echo "Done installation!"

.PHONY: clean
clean:
	find . -type d -name "__pycache__" | xargs rm -rf {};
