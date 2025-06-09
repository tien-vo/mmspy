NAME := mmspy.publish
MICROMAMBA := $(shell command -v micromamba 2> /dev/null)
CONDA_LOCK := conda-lock.yml
UV_LOCK := uv.lock

.DEFAULT_GOAL := help
.PHONY: help
help:
	@echo "Edit help string"

.PHONY: install
install: pyproject.toml ${UV_LOCK} ${CONDA_LOCK}
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
	@echo "Uv: Installing packages from ${UV_LOCK} ..."
	@${MICROMAMBA} run -n ${NAME} uv pip install -e .
	@echo "Done installation!"

.PHONY: clean
clean:
	find . -type d -name "__pycache__" | xargs rm -rf {};
