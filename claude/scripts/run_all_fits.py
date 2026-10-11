#!/usr/bin/env python3
"""Spustí všechny MCMC fity a uloží je do fits/ (NetCDF) a results/ (CSV).
Notebook tyto výsledky umí načíst (USE_CACHE=True) nebo vše přepočítat.
Použití: python scripts/run_all_fits.py [--fast]
"""
import sys, time, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np, pandas as pd, arviz as az
from revnice import data as D, model as M, posterior as PO, analysis as A

FAST = "--fast" in sys.argv
FITS = ROOT / "fits"; FITS.mkdir(exist_ok=True)
RES = ROOT / "results"; RES.mkdir(exist_ok=True)
d = D.load()
cfg = M.PriorConfig()
main_kw = dict(draws=300, tune=300, chains=4) if FAST else dict(draws=1000, tune=1000, chains=4)
sub_kw = dict(draws=150, tune=150, chains=4) if FAST else dict(draws=500, tune=500, chains=4)
rec_kw = dict(draws=150, tune=150, chains=4) if FAST else dict(draws=600, tune=600, chains=4)
log = {}

def save(idata, name):
    idata.to_netcdf(FITS / f"{name}.nc")

t0 = time.time()
# 1. hlavní model
if not (FITS / "main.nc").exists():
    m = M.build_model(d.H, cfg)
    idata = M.sample(m, **main_kw)
    save(idata, "main"); log["main_s"] = time.time() - t0; print("main done", log["main_s"], flush=True)
# 2. baseline bez osobních efektů
t1 = time.time()
if not (FITS / "baseline_no_u.nc").exists():
    m0 = M.build_model(d.H, M.PriorConfig(candidate_effects=False, local_effects=False))
    idata0 = M.sample(m0, **sub_kw)
    save(idata0, "baseline_no_u"); log["baseline_s"] = time.time() - t1; print("baseline done", flush=True)
# 3. recovery
for scen in ["A_malo_krizku", "B_hodne_krizku", "D_ruzne_strany"]:
    t1 = time.time()
    if (FITS / f"recovery_{scen}.nc").exists():
        continue
    r = A.recovery_test(scen, cfg, **rec_kw)
    save(r["idata"], f"recovery_{scen}")
    pd.DataFrame([r["summary"]]).to_csv(RES / f"recovery_{scen}.csv", index=False)
    np.savez(FITS / f"recovery_{scen}_truth.npz", C=r["truth"].C, S=r["truth"].S, H=r["truth"].H, N=r["truth"].N, pure=r["truth"].pure_marks)
    print("recovery", scen, "done", time.time() - t1, r["summary"]["total_true"], r["summary"]["total_med"], flush=True)
# 4. citlivost
t1 = time.time()
idata_main = az.from_netcdf(FITS / "main.nc")
rows = []
for label, over in A.SENSITIVITY_VARIANTS:
    import hashlib
    fn = FITS / f"sens_{hashlib.md5(label.encode()).hexdigest()[:8]}.nc"
    if label == "hlavní model":
        idata = idata_main
    elif fn.exists():
        idata = az.from_netcdf(fn)
    else:
        from dataclasses import replace
        idata = M.sample(M.build_model(d.H, replace(cfg, **over)), **sub_kw)
        save(idata, fn.stem)
    rows.append(A.sensitivity_metrics(idata, d.H, label)); print("sens", label, "done", flush=True)
pd.DataFrame(rows).to_csv(RES / "sensitivity.csv", index=False)
log["sens_s"] = time.time() - t1
# 5. LOPO
t1 = time.time()
if not (RES / "lopo.csv").exists():
    lp = A.lopo(d.H, cfg, **sub_kw)
    lp.to_csv(RES / "lopo.csv", index=False)
    log["lopo_s"] = time.time() - t1; print("lopo done", flush=True)
log["total_s"] = time.time() - t0
json.dump(log, open(RES / "runtime_log.json", "w"), indent=2)
print("ALL DONE", log)
