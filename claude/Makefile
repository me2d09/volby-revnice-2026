# Řevnice 2026 – bayesovská analýza křížkování
# Použití:  make setup   (instalace)   make validate (kontrola dat)
#           make fits    (všechny MCMC fity do fits/, ~1,5–2 h na 2 jádrech)
#           make notebook (spustí notebook od začátku do konce s uloženými fity)
#           make all     (validate + fits + notebook)      make clean
PY ?= python3
NB = revnice_2026_bayesian_analysis.ipynb

setup:
	$(PY) -m pip install -r requirements.txt

validate:
	$(PY) -I scripts/prepare_and_validate.py

fits:
	$(PY) scripts/run_all_fits.py

fits-fast:
	$(PY) scripts/run_all_fits.py --fast

build-notebook:
	$(PY) scripts/build_notebook.py

notebook:
	REVNICE_USE_CACHE=1 $(PY) -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 $(NB)

notebook-fresh:
	REVNICE_USE_CACHE=0 $(PY) -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 $(NB)

notebook-fast:
	REVNICE_FAST=1 REVNICE_USE_CACHE=0 $(PY) -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 $(NB)

all: validate fits notebook

clean:
	rm -rf fits/*.nc fits/*.npz results/*.csv results/*.json figures/*.png interactive/*.html .ipynb_checkpoints
