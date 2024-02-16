##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##

.PHONY: clean clean-build clean-pyc clean-test coverage deps dist docs help install lint lint/flake8 lint/black release test test-all test-release venv
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

VENV = .venv
VENV_PYTHON = $(VENV)/bin/python
SYSTEM_PYTHON = $(or $(shell which python3), $(shell which python))
PYTHON = $(or $(wildcard $(VENV_PYTHON)), $(SYSTEM_PYTHON))

$(VENV_PYTHON):
	rm -rf $(VENV)
	$(SYSTEM_PYTHON) -m venv --upgrade-deps $(VENV)

help:
	$(PYTHON) -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

coverage: ## check code coverage quickly with the default Python
	$(PYTHON) -m coverage run --source src -m pytest
	$(PYTHON) -m coverage report -m
	$(PYTHON) -m coverage html
	$(BROWSER) htmlcov/index.html

deps: ## Install development dependencies
	$(PYTHON) -m pip install -r requirements_dev.txt
	$(PYTHON) setup.py develop

dist: clean ## builds source and wheel package
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	ls -l dist

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/qiskit_qir.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ src
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

install: clean ## install the package to the active Python's site-packages
	$(PYTHON) setup.py install

lint/flake8: ## check style with flake8
	$(PYTHON) -m flake8 src tests

lint/black: ## check style with black
	$(PYTHON) -m black --check src tests

lint: lint/flake8 lint/black ## check style

release: dist ## package and upload a release
	$(PYTHON) -m twine upload dist/*

servedocs: docs ## compile the docs watching for changes
	$(PYTHON) -m watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

test: ## run tests quickly with the default Python
	$(PYTHON) -m pytest

test-all: ## run tests on every Python version with tox
	$(PYTHON) -m tox

test-release: dist ## package and upload a release
	twine upload --repository testpypi dist/*

venv: $(VENV_PYTHON) ## Creates the python virtual environment
	$(VENV_PYTHON) --version
	$(VENV_PYTHON) -m pip --version
