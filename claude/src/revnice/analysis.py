"""Vyšší analytické kroky volané z notebooku: prior predictive, recovery test,
citlivostní analýza, leave-one-precinct-out, posterior predictive."""
from __future__ import annotations

import time
from dataclasses import replace

import numpy as np
import pandas as pd
import pymc as pm
from scipy import stats

from . import data as D
from . import model as M
from . import posterior as PO
from . import simulate as SIM


# ---------------------------------------------------------------------------
# Prior predictive
# ---------------------------------------------------------------------------

def prior_predictive(H: np.ndarray, cfg: M.PriorConfig, n: int = 300, seed: int = 1) -> np.ndarray:
    model = M.build_model(H, cfg)
    with model:
        pp = pm.sample_prior_predictive(draws=n, random_seed=seed)
    Hpp = pp.prior_predictive["H"].values  # (chain, draw, ...) nebo (chain, draw, 32, 15) u mvnormal
    Hpp = Hpp.reshape((-1,) + H.shape)
    return Hpp


# ---------------------------------------------------------------------------
# Posterior predictive replikace
# ---------------------------------------------------------------------------

def posterior_predictive(idata, H_shape, n: int = 500, seed: int = 2) -> np.ndarray:
    """Replikace H z posterioru podle mechanistického rozptylu (Normal aproximace),
    zaokrouhleno a oříznuto na >= 0. Vrací (n, P, 8, 15)."""
    rng = np.random.default_rng(seed)
    post = idata.posterior
    mu = PO.stack_draws(post["mu"])
    sd = PO.stack_draws(post["sd_H"]) if "sd_H" in post else np.sqrt(mu)
    idx = rng.choice(mu.shape[0], size=min(n, mu.shape[0]), replace=False)
    rep = mu[idx] + sd[idx] * rng.standard_normal((len(idx),) + mu.shape[1:])
    return np.maximum(0, np.rint(rep))


# ---------------------------------------------------------------------------
# Recovery test (simulace známé pravdy)
# ---------------------------------------------------------------------------

def recovery_test(scenario: str, cfg: M.PriorConfig, draws=600, tune=600, chains=4, seed=11) -> dict:
    t = SIM.scenario(scenario)
    cfg_s = replace(cfg, n_valid_ballots=float(t.params["n_ballots"].sum()))
    model = M.build_model(t.H, cfg_s)
    t0 = time.time()
    idata = M.sample(model, seed=seed, draws=draws, tune=tune, chains=chains)
    runtime = time.time() - t0
    lb = D.rigorous_lower_bound(t.H)
    C_real = PO.realized_C(idata, t.H, lb, seed=seed)
    C_city = C_real.sum(axis=1)  # (n, 8, 15)
    C_true = t.C.sum(axis=0)
    med = np.median(C_city, axis=0)
    lo, hi = np.quantile(C_city, [0.05, 0.95], axis=0)
    tot = C_real.sum(axis=(1, 2, 3))
    post = idata.posterior
    u_true = t.params["u"]
    u_med = post["u"].median(("chain", "draw")).values
    ranks_true = (-C_true.ravel()).argsort().argsort() + 1
    ranks_med = (-med.ravel()).argsort().argsort() + 1
    top15 = np.argsort(-C_true.ravel())[:15]
    summary = dict(
        scenario=scenario,
        total_true=float(t.total_C), total_med=float(np.median(tot)),
        total_lo=float(np.quantile(tot, 0.05)), total_hi=float(np.quantile(tot, 0.95)),
        share_true=float(t.total_C / t.H.sum()),
        R_true=float(t.pure_marks.sum()), R_med=float(np.median(PO.stack_draws(post["R"]).sum(1))),
        B_true=float(t.N.sum()), B_med=float(np.median(PO.stack_draws(post["B"]).sum((1, 2)))),
        p_k0_true_mean=float(t.params["pi_k"][:, 0].mean()), p_k0_med_mean=float(post["p_k0"].median(("chain", "draw")).mean()),
        beta_true=float(t.params["beta"]), beta_med=float(post["beta"].median()),
        beta_lo=float(post["beta"].quantile(0.05)), beta_hi=float(post["beta"].quantile(0.95)),
        sigma_u_true=float(t.params["sigma_u"]), sigma_u_med=float(post["sigma_u"].median()),
        mbar_true=float(t.pure_marks.sum() / max(1, (t.params["n_ballots"].sum() - t.N.sum()))),
        mbar_med=float(post["mbar"].median()) if "mbar" in post else np.nan,
        corr=float(np.corrcoef(C_true.ravel(), med.ravel())[0, 1]),
        coverage90=float(((C_true >= lo) & (C_true <= hi)).mean()),
        coverage50=float(((C_true >= np.quantile(C_city, 0.25, axis=0)) & (C_true <= np.quantile(C_city, 0.75, axis=0))).mean()),
        mae=float(np.abs(C_true - med).mean()), bias=float((med - C_true).mean()),
        u_corr=float(np.corrcoef(u_true.ravel(), u_med.ravel())[0, 1]),
        rank_corr=float(stats.spearmanr(ranks_true, ranks_med).correlation),
        top15_recovered_in_top20=int((ranks_med[top15] <= 20).sum()),
        divergences=PO.n_divergences(idata),
        max_rhat=float(PO.mcmc_diagnostics(idata).iloc[0]["max_rhat"]),
        runtime_s=float(runtime),
    )
    return dict(name=scenario, truth=t, idata=idata, C_true=C_true.ravel(), C_med=med.ravel(), C_lo=lo.ravel(), C_hi=hi.ravel(), summary=summary)


# ---------------------------------------------------------------------------
# Citlivostní analýza
# ---------------------------------------------------------------------------

SENSITIVITY_VARIANTS = [
    ("hlavní model", {}),
    ("P(K=0) prior 0,30", dict(p0_mean=0.30)),
    ("P(K=0) prior 0,70", dict(p0_mean=0.70)),
    ("ocas K: ratio 0,50 (krátký)", dict(tail_ratio=0.50)),
    ("ocas K: ratio 0,85 (dlouhý)", dict(tail_ratio=0.85)),
    ("m̄ prior rovnoměrný", dict(mbar_beta=(1.0, 1.0))),
    ("m̄ prior vysoký (Beta 5,2)", dict(mbar_beta=(5.0, 2.0))),
    ("efekt pozice: prior β ~ N(0, 1)", dict(beta_mu=0.0, beta_sd=1.0)),
    ("σ_u prior úzký (HN 0,25)", dict(sigma_u_sd=0.25)),
    ("σ_u prior široký (HN 1,5)", dict(sigma_u_sd=1.5)),
    ("likelihood Poisson", dict(likelihood="poisson")),
    ("bez saturace (1 křížek/lístek ignorován)", dict(saturation=False)),
]


def sensitivity_metrics(idata, H: np.ndarray, label: str, cervena=(0, 9)) -> dict:
    lb = D.rigorous_lower_bound(H)
    C_real = PO.realized_C(idata, H, lb, seed=3)
    post = idata.posterior
    tot = C_real.sum(axis=(1, 2, 3))
    out = dict(label=label)

    def add(key, arr):
        q = np.quantile(arr, [0.05, 0.5, 0.95])
        out[f"{key}_median"], out[f"{key}_q05"], out[f"{key}_q95"] = float(q[1]), float(q[0]), float(q[2])

    add("total_C", tot)
    add("share_C", tot / H.sum())
    add("p_k0_mean", PO.stack_draws(post["p_k0"]).mean(axis=1))
    if "mbar" in post:
        add("mbar", PO.stack_draws(post["mbar"]))
    add("cervena_C", C_real[:, :, cervena[0], cervena[1]].sum(axis=1))
    add("beta", PO.stack_draws(post["beta"]))
    add("sigma_u", PO.stack_draws(post["sigma_u"]))
    add("R", PO.stack_draws(post["R"]).sum(axis=1))
    diag = PO.mcmc_diagnostics(idata).iloc[0]
    out["divergences"] = int(diag["divergences"])
    out["max_rhat"] = float(diag["max_rhat"])
    out["min_ess_bulk"] = float(diag["min_ess_bulk"])
    out["runtime_s"] = float(diag["sampling_time_s"])
    return out


def run_sensitivity(H: np.ndarray, base_cfg: M.PriorConfig, variants=SENSITIVITY_VARIANTS, draws=500, tune=500,
                    chains=4, seed=5, idata_main=None, keep_idata=False):
    rows, store = [], {}
    for label, over in variants:
        if label == "hlavní model" and idata_main is not None:
            idata = idata_main
        else:
            cfg = replace(base_cfg, **over)
            model = M.build_model(H, cfg)
            idata = M.sample(model, seed=seed, draws=draws, tune=tune, chains=chains)
        rows.append(sensitivity_metrics(idata, H, label))
        if keep_idata:
            store[label] = idata
    return pd.DataFrame(rows), store


# ---------------------------------------------------------------------------
# Leave-one-precinct-out
# ---------------------------------------------------------------------------

def _predict_profile(post, s: int, H_tot_block: float, use_u: bool):
    """Predikce rozdělení hlasů strany s v neznámém okrsku: tvar z posterioru,
    úroveň podle známého součtu hlasů strany v okrsku."""
    q = PO.stack_draws(post["q"])[:, s, :]  # (n, 15)
    theta = PO.stack_draws(post["theta"])  # (n, 15)
    u = PO.stack_draws(post["u"])[:, s, :] if (use_u and "u" in post) else np.zeros_like(theta)
    shapeC = np.exp(theta + u)
    # poměr osobních křížků ke stranickým lístkům u této strany: průměr přes trénovací okrsky
    muC = PO.stack_draws(post["muC"])[:, :, s, :].sum(axis=2)  # (n, P_train)
    B = PO.stack_draws(post["B"])[:, :, s]  # (n, P_train)
    ratio = (muC / B).mean(axis=1)  # (n,) křížky na stranický lístek
    # H_tot = B * (sum q) + B * ratio  =>  B = H_tot / (sum q + ratio)
    Bp = H_tot_block / (q.sum(axis=1) + ratio)
    S = Bp[:, None] * q
    C = (Bp * ratio)[:, None] * shapeC / shapeC.sum(axis=1, keepdims=True)
    return S + C  # (n, 15)


def lopo(H: np.ndarray, cfg: M.PriorConfig, draws=500, tune=500, chains=4, seed=21) -> pd.DataFrame:
    """Pro každý okrsek: fit na zbylých 3, predikce profilu 120 kandidátů ve vynechaném okrsku
    při známých součtech hlasů stran v tom okrsku. Srovnání: model s osobními efekty u,
    model bez u (jen strana + pořadí), a naivní prediktor = podíly kandidátů v ostatních okrscích."""
    rows = []
    P = H.shape[0]
    for p_out in range(P):
        keep = [p for p in range(P) if p != p_out]
        Htr = H[keep]
        # počet platných lístků známe jen za město: pro trénovací okrsky jej škálujeme podílem hlasů
        # (předpoklad stejného průměru hlasů na lístek ve všech okrscích)
        cfg_tr = cfg if cfg.n_valid_ballots is None else replace(cfg, n_valid_ballots=float(cfg.n_valid_ballots) * Htr.sum() / H.sum())
        model = M.build_model(Htr, cfg_tr)
        idata = M.sample(model, seed=seed + p_out, draws=draws, tune=tune, chains=chains)
        post = idata.posterior
        Hout = H[p_out]
        res = dict(precinct_out=p_out + 1)
        for name, use_u in [("model s u", True), ("model bez u", False)]:
            pred = np.stack([_predict_profile(post, s, Hout[s].sum(), use_u) for s in range(8)], axis=1)  # (n, 8, 15)
            mu = pred.mean(axis=0)
            sd = pred.std(axis=0) + np.sqrt(np.maximum(mu, 1.0))  # nejistota parametrů + Poissonovský šum
            res[f"mae_{name}"] = float(np.abs(mu - Hout).mean())
            res[f"lpd_{name}"] = float(stats.norm.logpdf(Hout, mu, sd).sum())
        # naivní prediktor: podíl kandidáta na hlasech strany v ostatních okrscích
        share = Htr.sum(axis=0) / Htr.sum(axis=0).sum(axis=1, keepdims=True)
        mu = share * Hout.sum(axis=1, keepdims=True)
        sd = np.sqrt(np.maximum(mu, 1.0)) * 1.5
        res["mae_naivní podíly"] = float(np.abs(mu - Hout).mean())
        res["lpd_naivní podíly"] = float(stats.norm.logpdf(Hout, mu, sd).sum())
        # prediktor "stejný podíl pro všechny pozice" (žádná informace o kandidátech)
        mu = np.repeat(Hout.sum(axis=1, keepdims=True) / 15, 15, axis=1)
        sd = np.sqrt(np.maximum(mu, 1.0)) * 2.0
        res["mae_rovnoměrně"] = float(np.abs(mu - Hout).mean())
        res["lpd_rovnoměrně"] = float(stats.norm.logpdf(Hout, mu, sd).sum())
        res["divergences"] = PO.n_divergences(idata)
        rows.append(res)
    return pd.DataFrame(rows)
