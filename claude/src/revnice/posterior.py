"""Zpracování posterioru: realizované počty křížků, souhrny, diagnostika."""
from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats

from .data import N_PARTIES, N_POS, PARTY_SHORT, rigorous_lower_bound


def n_divergences(idata) -> int:
    """Počet divergentních přechodů (PyMC ukládá bool `diverging` na každý tah)."""
    ss = idata.sample_stats
    if "diverging" in ss:
        return int(ss["diverging"].sum())
    return int((ss["divergences"] > 0).sum())


def stack_draws(da: xr.DataArray) -> np.ndarray:
    """(chain, draw, ...) -> (n_draws, ...)"""
    return da.stack(sample=("chain", "draw")).transpose("sample", ...).values


def realized_C(idata, H: np.ndarray, bound: np.ndarray | None = None, seed: int = 0) -> np.ndarray:
    """Posterior REALIZOVANÉHO počtu individuálních křížků C[p,s,i] podmíněný H.

    V modelu je H = S + C se složkami s rozptyly var_S = B q (1-q) a var_C = muC.
    Pro každý posteriorní tah vezmeme podmíněné rozdělení C | H (normální
    aproximace), zaokrouhlíme a ořízneme na [bound, H]; ``bound`` je rigorózní
    dolní mez (dokazatelná informace, kterou nezávislá aproximace ztrácí).
    Vrací pole (n_draws, P, 8, 15).
    """
    rng = np.random.default_rng(seed)
    post = idata.posterior
    muC = stack_draws(post["muC"])
    S = stack_draws(post["S"])
    B = stack_draws(post["B"])
    q = stack_draws(post["q"])
    var_S = B[:, :, :, None] * q[:, None, :, :] * (1 - q[:, None, :, :]) + 0.25
    var_C = muC + 0.25
    mu = S + muC
    resid = H[None] - mu
    cond_mean = muC + var_C / (var_S + var_C) * resid
    cond_sd = np.sqrt(var_C * var_S / (var_S + var_C))
    C = cond_mean + cond_sd * rng.standard_normal(cond_mean.shape)
    C = np.rint(C)
    lo = np.zeros_like(H) if bound is None else bound
    C = np.clip(C, lo[None], H[None])
    return C


def summarize_draws(x: np.ndarray, axis: int = 0) -> dict:
    qs = np.quantile(x, [0.025, 0.05, 0.25, 0.5, 0.75, 0.95, 0.975], axis=axis)
    return dict(
        mean=x.mean(axis=axis), median=qs[3], q025=qs[0], q05=qs[1], q25=qs[2], q75=qs[4], q95=qs[5], q975=qs[6]
    )


def candidate_table(idata, data, C_real: np.ndarray, baseline_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Tabulka 120 kandidátů s mezemi, posteriorními odhady a robustností pořadí."""
    H = data.H
    lb_prec = rigorous_lower_bound(H)  # (4,8,15)
    lb_city_sum = lb_prec.sum(axis=0)
    lb_city = rigorous_lower_bound(data.H_city)
    post = idata.posterior
    muC = stack_draws(post["muC"]).sum(axis=1)  # (n, 8, 15) očekávané křížky (město)
    C_city = C_real.sum(axis=1)  # (n, 8, 15) realizované křížky (město)
    u = stack_draws(post["u"]) if "u" in post else np.zeros_like(muC)
    share = C_city / H.sum(axis=0)[None]
    # pořadí kandidátů podle realizovaných křížků (1 = nejvíc) v každém tahu
    flat = C_city.reshape(C_city.shape[0], -1)
    ranks = (-flat).argsort(axis=1).argsort(axis=1) + 1
    ranks = ranks.reshape(C_city.shape)
    rows = []
    sm = summarize_draws(muC)
    sc = summarize_draws(C_city)
    su = summarize_draws(u)
    sr = summarize_draws(ranks)
    city = data.city.set_index(["party_id", "position"])
    for s in range(N_PARTIES):
        for i in range(N_POS):
            cityrow = city.loc[(s + 1, i + 1)]
            rows.append(
                dict(
                    party_id=s + 1,
                    party=PARTY_SHORT[s + 1],
                    position=i + 1,
                    name=data.names[s, i],
                    age=int(cityrow["age"]),
                    elected=str(cityrow["elected_2026"]) == "ANO",
                    votes_city=int(H[:, s, i].sum()),
                    votes_p1=int(H[0, s, i]), votes_p2=int(H[1, s, i]), votes_p3=int(H[2, s, i]), votes_p4=int(H[3, s, i]),
                    lb_city=int(lb_city[s, i]),
                    lb_precinct_sum=int(lb_city_sum[s, i]),
                    C_median=float(sc["median"][s, i]),
                    C_mean=float(sc["mean"][s, i]),
                    C_q25=float(sc["q25"][s, i]), C_q75=float(sc["q75"][s, i]),
                    C_q05=float(sc["q05"][s, i]), C_q95=float(sc["q95"][s, i]),
                    C_q025=float(sc["q025"][s, i]), C_q975=float(sc["q975"][s, i]),
                    C_share_median=float(np.median(share[:, s, i])),
                    muC_median=float(sm["median"][s, i]), muC_q05=float(sm["q05"][s, i]), muC_q95=float(sm["q95"][s, i]),
                    u_median=float(su["median"][s, i]), u_q05=float(su["q05"][s, i]), u_q95=float(su["q95"][s, i]),
                    p_u_positive=float((u[:, s, i] > 0).mean()),
                    rank_median=float(sr["median"][s, i]), rank_q05=float(sr["q05"][s, i]), rank_q95=float(sr["q95"][s, i]),
                    p_top10=float((ranks[:, s, i] <= 10).mean()),
                    p_top20=float((ranks[:, s, i] <= 20).mean()),
                )
            )
    df = pd.DataFrame(rows)
    df["rank_width_90"] = df["rank_q95"] - df["rank_q05"]
    if baseline_df is not None:
        df = df.merge(baseline_df, on=["party_id", "position"], how="left")
    return df


def party_table(idata, data, C_real: np.ndarray) -> pd.DataFrame:
    post = idata.posterior
    H = data.H
    rows = []
    B = stack_draws(post["B"])  # (n, 4, 8)
    EK = stack_draws(post["EK"])
    pk0 = stack_draws(post["p_k0"])
    C_party = C_real.sum(axis=(1, 3))  # (n, 8)
    muC_party = stack_draws(post["muC"]).sum(axis=(1, 3))
    lb = rigorous_lower_bound(H).sum(axis=(0, 2))
    for s in range(N_PARTIES):
        votes = int(H[:, s, :].sum())
        d = dict(party_id=s + 1, party=PARTY_SHORT[s + 1], votes=votes, lb_precinct_sum=int(lb[s]))
        for key, arr in [("C", C_party[:, s]), ("muC", muC_party[:, s]), ("B_total", B[:, :, s].sum(axis=1)),
                         ("EK", EK[:, s]), ("p_k0", pk0[:, s])]:
            q = np.quantile(arr, [0.05, 0.5, 0.95])
            d[f"{key}_median"], d[f"{key}_q05"], d[f"{key}_q95"] = q[1], q[0], q[2]
        d["C_share_median"] = float(np.median(C_party[:, s] / votes))
        d["C_share_q05"] = float(np.quantile(C_party[:, s] / votes, 0.05))
        d["C_share_q95"] = float(np.quantile(C_party[:, s] / votes, 0.95))
        rows.append(d)
    return pd.DataFrame(rows)


def precinct_table(idata, data, C_real: np.ndarray, lp_bounds: list[float]) -> pd.DataFrame:
    post = idata.posterior
    H = data.H
    rows = []
    B = stack_draws(post["B"])
    R = stack_draws(post["R"])
    G = stack_draws(post["G"])
    Cp = C_real.sum(axis=(2, 3))  # (n, 4)
    for p in range(H.shape[0]):
        votes = int(H[p].sum())
        d = dict(precinct=p + 1, votes=votes, max_party_ballots=votes / N_POS,
                 lb_monotone=int(rigorous_lower_bound(H[p]).sum()), lb_lp=float(np.ceil(lp_bounds[p])))
        for key, arr in [("C", Cp[:, p]), ("party_ballots", B[:, p, :].sum(axis=1)), ("pure_marks", R[:, p]),
                         ("marks_from_party_voters", G[:, p, :].sum(axis=1))]:
            q = np.quantile(arr, [0.05, 0.5, 0.95])
            d[f"{key}_median"], d[f"{key}_q05"], d[f"{key}_q95"] = q[1], q[0], q[2]
        d["C_share_median"] = float(np.median(Cp[:, p] / votes))
        d["C_share_q05"] = float(np.quantile(Cp[:, p] / votes, 0.05))
        d["C_share_q95"] = float(np.quantile(Cp[:, p] / votes, 0.95))
        rows.append(d)
    return pd.DataFrame(rows)


def mcmc_diagnostics(idata, var_names=None) -> pd.DataFrame:
    """Souhrn R-hat, ESS, divergencí, runtime."""
    import arviz as az

    summ = az.summary(idata, var_names=var_names)
    ss = idata.sample_stats
    out = dict(
        n_chains=int(ss.sizes["chain"]),
        n_draws=int(ss.sizes["draw"]),
        divergences=n_divergences(idata),
        max_rhat=float(np.nanmax(summ["r_hat"].values)),
        min_ess_bulk=float(np.nanmin(summ["ess_bulk"].values)),
        min_ess_tail=float(np.nanmin(summ["ess_tail"].values)),
        share_rhat_gt_1_01=float((summ["r_hat"].values > 1.01).mean()),
        share_ess_lt_400=float((summ["ess_bulk"].values < 400).mean()),
        sampling_time_s=float(ss.attrs.get("sampling_time", np.nan)),
        max_treedepth_hits=int(ss["reached_max_treedepth"].sum()) if "reached_max_treedepth" in ss else -1,
    )
    try:
        out["bfmi_min"] = float(np.min(az.bfmi(idata)))
    except Exception:
        out["bfmi_min"] = np.nan
    return pd.DataFrame([out])
