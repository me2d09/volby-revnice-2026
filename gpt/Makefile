PYTHON ?= python

.PHONY: validate test fit notebook all
validate:
	$(PYTHON) scripts/prepare_and_validate.py
test:
	$(PYTHON) -m pytest -q
fit:
	$(PYTHON) scripts/run_analysis.py --force
notebook:
	$(PYTHON) scripts/execute_notebook.py
all: validate test notebook
