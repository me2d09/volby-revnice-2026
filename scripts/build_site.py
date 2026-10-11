#!/usr/bin/env python3
"""Sestaví data a notebooky pro GitHub Pages web ve složce ``docs/``.

Kroky:
  1. přepočítá základní statistiky (basic/prepare_basic.py) a zkopíruje je do docs/data/,
  2. z výsledků jednotlivých analýz (claude/results, později gpt/...) vytáhne
     to, co web zobrazuje, do docs/data/<analyza>.json,
  3. převede notebooky do HTML (docs/notebooky/<analyza>.html) tak, aby v nich
     fungovaly interaktivní Plotly grafy, a přiloží originální .ipynb ke stažení,
  4. zkopíruje infografiku a plotly.js.

Složky analýz (claude/, gpt/) se pouze čtou, nikdy se do nich nezapisuje.

Spuštění z kořene repozitáře:  python scripts/build_site.py [--skip-notebooks]
"""
from __future__ import annotations

import argparse
import copy
import csv
import html
import json
import math
import runpy
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = DOCS / "data"
NB_OUT = DOCS / "notebooky"
PLOTLY_JS = "plotly-4.1.1.min.js"   # verze, se kterou byly vytvořeny grafy v notebooku Claude

# Analýzy, které web zná. Chybějící složka (např. gpt/ před dokončením) se přeskočí.
ANALYSES = {
    "claude": {
        "title": "Analýza Claude (Anthropic)",
        "notebook": ROOT / "claude" / "revnice_2026_bayesian_analysis.ipynb",
    },
    "gpt": {
        "title": "Analýza GPT (OpenAI)",
        "notebook": ROOT / "gpt" / "revnice_2026_bayesian_analysis.ipynb",
        "assets": {"interactive/": ROOT / "gpt" / "interactive"},   # iframy v notebooku
    },
}

SHORT = {"ŠANCE": "ŠANCE", "TOP 09": "TOP 09", "DOBŘE": "DOBŘE", "Srdce": "Srdce Řevnic",
         "PRO": "PRO", "ODS": "ODS", "Perspektiva": "Perspektiva", "Naše Řevnice": "Naše Řevnice"}


def read_csv(path: Path, delimiter: str = ";") -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def write_data(name: str, obj: dict) -> None:
    """Uloží data jako JSON (ke stažení) i jako JS (načte se i při otevření z file://)."""
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    (DATA / f"{name}.json").write_text(txt, encoding="utf-8")
    js = f"window.RV_DATA=window.RV_DATA||{{}};window.RV_DATA[{json.dumps(name)}]={txt};\n"
    (DATA / f"{name}.js").write_text(js, encoding="utf-8")


def num(x: str, nd: int | None = None):
    if x in ("", None):
        return None
    v = float(x)
    if nd is None:
        return v
    v = round(v, nd)
    return int(v) if nd == 0 else v


# ---------------------------------------------------------------- 1. základní data
def build_basic() -> dict:
    runpy.run_path(str(ROOT / "basic" / "prepare_basic.py"), run_name="__main__")
    data = json.loads((ROOT / "basic" / "zakladni_data.json").read_text(encoding="utf-8"))
    write_data("zakladni", data)
    return data


# ---------------------------------------------------------------- 2. analýzy (společný formát)
# Obě analýzy převádíme na stejný tvar, aby je web mohl zobrazit stejným kódem a porovnat:
#   kandidát: C (medián osobních křížků), lo/hi (90% interval), eff (osobní efekt jako násobek), rank, ...
SENS_LABELS = {
    # Claude (claude/results/sensitivity.csv)
    "hlavní model": "hlavní model",
    "P(K=0) prior 0,30": "méně stranických voličů bez křížků jinde",
    "P(K=0) prior 0,70": "víc stranických voličů bez křížků jinde",
    "ocas K: ratio 0,50 (krátký)": "málokdo dává hodně křížků jinde",
    "ocas K: ratio 0,85 (dlouhý)": "častěji hodně křížků jinde",
    "m̄ prior rovnoměrný": "lístky bez strany: neutrální předpoklad",
    "m̄ prior vysoký (Beta 5,2)": "lístky bez strany: hodně křížků",
    "efekt pozice: prior β ~ N(0, 1)": "výhoda pozice: volnější předpoklad",
    "σ_u prior úzký (HN 0,25)": "osobnosti: menší rozdíly",
    "σ_u prior široký (HN 1,5)": "osobnosti: větší rozdíly",
    "likelihood Poisson": "jiný model náhodného šumu",
    "bez saturace (1 křížek/lístek ignorován)": "bez pravidla „1 křížek na osobu“",
    # GPT (gpt/results/prior_sensitivity.csv)
    "reference": "hlavní model",
    "party_first": "voliči spíš křížkují celou stranu",
    "personal_long_tail": "víc osobního křížkování",
    "weak_position": "slabý vliv pořadí na lístku",
    "heterogeneous": "větší rozdíly mezi kandidáty",
    "strong_pooling": "silnější sdílení mezi okrsky",
    "poisson_like": "jiný model náhodného šumu",
}
ROBUST = {"stabilní": "stabilní", "střední": "středně jisté", "nestabilní": "nejisté",
          "top10_p_ge_0.8_all_models": "jistě v top 10", "scenario_rank_span_le_10": "stabilní",
          "scenario_rank_unstable": "nejisté"}
GPT_TOTALS_CACHE = ROOT / "scripts" / "derived" / "gpt_reference_totals.json"


def exact_budget_bound() -> dict:
    """Nezávislé ověření dolní meze: celočíselné i spojité (LP) minimum osobních křížků po okrscích.

    Pro kandidátku s horní hranicí b stranických lístků je maximum stranických hlasů
    sum_i min(b, min_{j<=i} H_j) – konkávní funkce b. Při rozpočtu sum_s b_s <= H_p / 15
    je proto optimální hladové přidělování jednotek s největším přírůstkem (přesné řešení).
    """
    rows = read_csv(ROOT / "input" / "data" / "processed" / "precinct_candidates_2026.csv")
    out = {"integer": {}, "lp": {}}
    for p in sorted({r["precinct"] for r in rows}):
        H: dict[str, list[int]] = {}
        for r in rows:
            if r["precinct"] == p:
                H.setdefault(r["party_id"], [0] * 15)[int(r["position"]) - 1] = int(r["votes"])
        total = sum(map(sum, H.values()))
        gains = []
        for h in H.values():
            pm, cur = [], 10 ** 9
            for x in h:
                cur = min(cur, x)
                pm.append(cur)
            gains += [sum(1 for v in pm if v >= b + 1) for b in range(pm[0])]
        gains.sort(reverse=True)
        k = total // 15
        s_int = sum(gains[:k])
        s_lp = s_int + (total / 15 - k) * (gains[k] if k < len(gains) else 0)
        out["integer"][p] = total - s_int
        out["lp"][p] = round(total - s_lp, 2)
    out["integer_total"] = sum(out["integer"].values())
    out["lp_total"] = round(sum(out["lp"].values()), 1)
    return out


def _names(basic: dict) -> dict:
    return {(c["party"], c["position"]): c for c in basic["candidates"]}


def build_claude(basic: dict) -> dict:
    res = ROOT / "claude" / "results"
    B = _names(basic)
    cands = []
    for r in read_csv(res / "candidate_estimates.csv"):
        party, pos = SHORT[r["party"]], int(r["position"])
        votes, c_med = int(r["votes_city"]), num(r["C_median"], 0)
        cands.append({
            "party": party, "position": pos, "name": B[(party, pos)]["name"], "age": int(r["age"]),
            "elected": r["elected"] == "True", "votes": votes, "vp": [int(r[f"votes_p{k}"]) for k in (1, 2, 3, 4)],
            "lb": int(r["lb_precinct_sum"]), "lb_p": B[(party, pos)]["min_personal_marks_precincts"],
            "C": c_med, "lo": num(r["C_q05"], 0), "hi": num(r["C_q95"], 0), "S": votes - c_med,
            "share": num(r["C_share_median"], 3),
            "eff": round(math.exp(float(r["u_median"])), 3), "eff_lo": round(math.exp(float(r["u_q05"])), 3),
            "eff_hi": round(math.exp(float(r["u_q95"])), 3), "p_eff": num(r["p_u_positive"], 3),
            "rank": num(r["rank_median"], 0), "rank_lo": num(r["rank_q05"], 0), "rank_hi": num(r["rank_q95"], 0),
            "p_top10": num(r["p_top10"], 3), "robust": ROBUST.get(r["robust_rank"], r["robust_rank"]),
        })
    parties = [{
        "party": SHORT[r["party"]], "votes": int(r["votes"]), "lb": int(r["lb_precinct_sum"]),
        "C": num(r["C_median"], 0), "lo": num(r["C_q05"], 0), "hi": num(r["C_q95"], 0),
        "share": num(r["C_share_median"], 3), "share_lo": num(r["C_share_q05"], 3), "share_hi": num(r["C_share_q95"], 3),
        "ballots": num(r["B_total_median"], 0), "ballots_lo": num(r["B_total_q05"], 0), "ballots_hi": num(r["B_total_q95"], 0),
    } for r in read_csv(res / "party_estimates.csv")]
    precincts = [{
        "id": int(r["precinct"]), "votes": int(r["votes"]), "lb": num(r["lb_lp"], 0),
        "C": num(r["C_median"], 0), "lo": num(r["C_q05"], 0), "hi": num(r["C_q95"], 0), "share": num(r["C_share_median"], 3),
    } for r in read_csv(res / "precinct_estimates.csv")]
    sensitivity = [{
        "label": SENS_LABELS.get(r["label"], r["label"]), "tech": r["label"], "main": r["label"] == "hlavní model",
        "C": num(r["total_C_median"], 0), "lo": num(r["total_C_q05"], 0), "hi": num(r["total_C_q95"], 0),
        "ok": int(float(r["divergences"])) == 0 or r["label"] == "hlavní model",
    } for r in read_csv(res / "sensitivity.csv", delimiter=",")]
    rec_names = {"A_malo_krizku": "Málo křížků", "B_hodne_krizku": "Hodně křížků", "D_ruzne_strany": "Kandidátky se liší"}
    recovery = []
    for f in sorted(res.glob("recovery_*.csv")):
        r = read_csv(f, delimiter=",")[0]
        recovery.append({"label": rec_names.get(r["scenario"], r["scenario"]), "true": num(r["total_true"], 0),
                         "est": num(r["total_med"], 0), "lo": num(r["total_lo"], 0), "hi": num(r["total_hi"], 0),
                         "rank_corr": num(r["rank_corr"], 3)})
    run_info = json.loads((res / "run_info.json").read_text(encoding="utf-8"))
    v = run_info.get("versions", {})
    out = {
        "key": "claude", "model": "Claude", "vendor": "Anthropic", "page": "krizky.html", "notebook": "notebooky/claude.html",
        # Souhrnná čísla z claude/results/souhrn_zjisteni.md (notebook, odd. 10) – spočtená z posterioru.
        "headline": {"total": 6878, "lo": 5621, "hi": 8202, "share": 0.287, "sens_min": 5075, "sens_max": 7729,
                     "lb_budget": 2890, "lb_budget_method": "lineární program (spojitá relaxace)",
                     "lb_monotone": 1493, "lb_city": 1096, "valid_ballots_used": True,
                     "no_party_ballots": 462, "no_party_lo": 332, "no_party_hi": 574, "p_k0": 0.76},
        "eff_def": "násobek oproti typickému kandidátovi na stejném místě stejné kandidátky",
        "interval": "90 %", "recovery_interval": "90 %",
        "method": f"Hierarchický bayesovský model v PyMC {v.get('pymc', '')} (NUTS, 4 řetězce), počet platných lístků 1 679 jako omezení.",
        "candidates": cands, "parties": parties, "precincts": precincts, "sensitivity": sensitivity, "recovery": recovery,
        "run_info": {"software": f"PyMC {v.get('pymc', '?')}, ArviZ {v.get('arviz', '?')}",
                     "params": run_info.get("n_free_params"), "minutes": round(run_info.get("sampling_time_main_s", 0) / 60),
                     "diagnostics": f"{run_info.get('divergences_main')} divergence, R̂ ≤ 1,014"},
    }
    write_data("claude", out)
    return out


def gpt_reference_totals() -> dict:
    """90% intervaly součtů z posteriorových vzorků GPT (gpt/results/chains/reference.npz).

    Vzorky jsou v .gitignore, proto výsledek ukládáme do scripts/derived/ a příště ho jen načteme.
    """
    npz = ROOT / "gpt" / "results" / "chains" / "reference.npz"
    if npz.exists():
        import numpy as np
        C = np.load(npz)["C"].astype(np.int64)            # (řetězec, los, okrsek, strana, pozice)
        C = C.reshape(-1, *C.shape[2:])
        q = lambda x: [int(round(v)) for v in np.quantile(x, [0.05, 0.5, 0.95])]
        out = {"total": q(C.sum(axis=(1, 2, 3))),
               "party": [q(C[:, :, s, :].sum(axis=(1, 2))) for s in range(C.shape[2])],
               "precinct": [q(C[:, p].sum(axis=(1, 2))) for p in range(C.shape[1])],
               "n_draws": int(C.shape[0])}
        GPT_TOTALS_CACHE.parent.mkdir(parents=True, exist_ok=True)
        GPT_TOTALS_CACHE.write_text(json.dumps(out, indent=1), encoding="utf-8")
        return out
    return json.loads(GPT_TOTALS_CACHE.read_text(encoding="utf-8"))


def build_gpt(basic: dict) -> dict | None:
    res = ROOT / "gpt" / "results"
    if not (res / "candidate_estimates.csv").exists():
        print("[gpt] výsledky nejsou k dispozici – přeskakuji")
        return None
    B = _names(basic)
    tot = gpt_reference_totals()
    long2short = {r["strana"]: s for r, s in zip(read_csv(ROOT / "input" / "data" / "raw" / "strany_2022_2026.csv"),
                                                ["ŠANCE", "TOP 09", "DOBŘE", "Srdce Řevnic", "PRO", "ODS", "Perspektiva", "Naše Řevnice", "SPOLEČNĚ"])}
    long2short["DOBŘE - Dialog o budoucnosti Řevnic"] = "DOBŘE"
    cands = []
    for r in read_csv(res / "candidate_estimates.csv"):
        party, pos = long2short[r["party"]], int(r["position"])
        votes, c_med = int(r["votes"]), num(r["personal_median"], 0)
        cands.append({
            "party": party, "position": pos, "name": B[(party, pos)]["name"], "age": int(r["age"]),
            "elected": r["elected_2026"] == "ANO", "votes": votes, "vp": [int(r[f"votes_p{k}"]) for k in (1, 2, 3, 4)],
            "lb": int(r["rigorous_min_personal_marks_sum_precincts"]), "lb_p": B[(party, pos)]["min_personal_marks_precincts"],
            "C": c_med, "lo": num(r["personal_q05"], 0), "hi": num(r["personal_q95"], 0), "S": votes - c_med,
            "share": round(c_med / votes, 3) if votes else 0,
            "eff": num(r["position_adjusted_effect_median"], 3), "eff_lo": num(r["position_adjusted_effect_q05"], 3),
            "eff_hi": num(r["position_adjusted_effect_q95"], 3), "p_eff": num(r["p_effect_above_party_center"], 3),
            "rank": num(r["rank_median"], 0), "rank_lo": num(r["rank_q05"], 0), "rank_hi": num(r["rank_q95"], 0),
            "p_top10": num(r["p_top10"], 3), "robust": ROBUST.get(r["rank_robustness"], r["rank_robustness"]),
        })
    parties = []
    for i, r in enumerate(read_csv(res / "party_estimates.csv")):
        votes = int(r["votes"])
        lo, med, hi = tot["party"][i]
        parties.append({
            "party": long2short[r["party"]], "votes": votes, "lb": int(r["rigorous_min_sum"]),
            "C": num(r["personal_median"], 0), "lo": lo, "hi": hi,
            "share": round(float(r["personal_median"]) / votes, 3), "share_lo": round(lo / votes, 3), "share_hi": round(hi / votes, 3),
            "ballots": num(r["effective_party_ballots_median"], 0), "ballots_lo": num(r["effective_party_ballots_q05"], 0),
            "ballots_hi": num(r["effective_party_ballots_q95"], 0),
        })
    precincts = []
    for i, r in enumerate(read_csv(res / "precinct_estimates.csv")):
        lo, med, hi = tot["precinct"][i]
        precincts.append({"id": int(r["precinct"]), "votes": int(r["votes"]), "lb": int(r["budget_lower_bound"]),
                          "C": num(r["personal_median"], 0), "lo": lo, "hi": hi,
                          "share": round(float(r["personal_median"]) / int(r["votes"]), 3)})
    sensitivity = [{
        "label": SENS_LABELS.get(r["scenario"], r["scenario"]), "tech": r["scenario"], "main": r["scenario"] == "reference",
        "C": num(r["personal_total_median"], 0), "lo": num(r["personal_total_q025"], 0), "hi": num(r["personal_total_q975"], 0),
        "ok": r["mcmc_gate_pass"] == "True",
    } for r in read_csv(res / "prior_sensitivity.csv")]
    rec_names = {"matched": "Stejný generátor jako model", "ballot": "Jiný generátor lístků"}
    recovery = [{"label": rec_names.get(r["experiment"], r["experiment"]), "true": num(r["true_personal_total"], 0),
                 "est": num(r["posterior_median"], 0), "lo": num(r["q025"], 0), "hi": num(r["q975"], 0),
                 "rank_corr": num(r["candidate_rank_spearman"], 3)} for r in read_csv(res / "synthetic_recovery.csv")]
    runs = read_csv(res / "mcmc_run_summary.csv")
    ref = next(r for r in runs if r["label"] == "reference")
    sens_scen = [r for r in runs if r["label"] in {s["tech"] for s in sensitivity}]
    lo, med, hi = tot["total"]
    out = {
        "key": "gpt", "model": "GPT", "vendor": "OpenAI", "page": "gpt.html", "notebook": "notebooky/gpt.html",
        "headline": {"total": med, "lo": lo, "hi": hi, "share": round(med / 23939, 3),
                     "sens_min": min(s["C"] for s in sensitivity), "sens_max": max(s["C"] for s in sensitivity),
                     "lb_budget": 2897, "lb_budget_method": "přesné celočíselné minimum s konstrukcí lístků",
                     "lb_monotone": 1493, "lb_city": 1096, "valid_ballots_used": False},
        "eff_def": "násobek oproti „průměrnému“ kandidátovi téže kandidátky po očištění o pořadí",
        "interval": "90 %", "recovery_interval": "95 %",
        "method": "Vlastní celočíselný MCMC sampler (Gibbs/Metropolis, 4 řetězce); počet platných lístků model nepoužívá.",
        "candidates": cands, "parties": parties, "precincts": precincts, "sensitivity": sensitivity, "recovery": recovery,
        "run_info": {"software": "vlastní celočíselný sampler (NumPy)",
                     "params": None, "minutes": round(float(ref["wall_seconds"]) / 60),
                     "diagnostics": f"R̂ ≤ {RVfmt(float(ref['max_rhat']), 3)}; varianty: {sum(r['mcmc_gate_pass'] == 'True' for r in sens_scen)} z {len(sens_scen)} prošlo kontrolou"},
        "n_draws": tot.get("n_draws"),
    }
    write_data("gpt", out)
    return out


def RVfmt(x: float, d: int) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def build_comparison(basic: dict, cl: dict, gp: dict | None) -> None:
    if gp is None:
        return
    bound = exact_budget_bound()
    G = {(c["party"], c["position"]): c for c in gp["candidates"]}
    pairs = []
    for c in cl["candidates"]:
        g = G[(c["party"], c["position"])]
        pairs.append({"party": c["party"], "position": c["position"], "name": c["name"], "votes": c["votes"],
                      "elected": c["elected"], "lb": c["lb"],
                      "cl": c["C"], "cl_lo": c["lo"], "cl_hi": c["hi"], "gp": g["C"], "gp_lo": g["lo"], "gp_hi": g["hi"],
                      "cl_eff": c["eff"], "gp_eff": g["eff"], "cl_rank": c["rank"], "gp_rank": g["rank"],
                      "overlap": not (g["hi"] < c["lo"] or c["hi"] < g["lo"])})

    def pearson(x, y):
        mx, my = sum(x) / len(x), sum(y) / len(y)
        return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))

    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for k, i in enumerate(order):
            r[i] = k
        return r

    cx, gx = [p["cl"] for p in pairs], [p["gp"] for p in pairs]
    ce, ge = [math.log(p["cl_eff"]) for p in pairs], [math.log(p["gp_eff"]) for p in pairs]
    top = lambda key, n: {(p["party"], p["position"]) for p in sorted(pairs, key=lambda p: -p[key])[:n]}
    top_eff = lambda key, n: {(p["party"], p["position"]) for p in sorted(pairs, key=lambda p: -p[key])[:n]}
    by_pos = [{"position": k, "cl": sum(p["cl"] for p in pairs if p["position"] == k),
               "gp": sum(p["gp"] for p in pairs if p["position"] == k)} for k in range(1, 16)]
    out = {
        "bound": bound,
        "stats": {"pearson_C": round(pearson(cx, gx), 3), "spearman_C": round(pearson(ranks(cx), ranks(gx)), 3),
                  "pearson_eff": round(pearson(ce, ge), 3), "spearman_eff": round(pearson(ranks(ce), ranks(ge)), 3),
                  "overlap_n": sum(p["overlap"] for p in pairs), "n": len(pairs),
                  "top10_common": len(top("cl", 10) & top("gp", 10)), "top10_eff_common": len(top_eff("cl_eff", 10) & top_eff("gp_eff", 10)),
                  "sum_cl": sum(cx), "sum_gp": sum(gx)},
        "pairs": pairs, "by_position": by_pos,
    }
    write_data("srovnani", out)
    print(f"[srovnání] Pearson {out['stats']['pearson_C']}, Spearman {out['stats']['spearman_C']}, "
          f"překryv intervalů {out['stats']['overlap_n']}/{out['stats']['n']}, mez celočíselně {bound['integer_total']} / LP {bound['lp_total']}")


# ---------------------------------------------------------------- 3. notebooky
HEADER_CSS = """
<style>
  .rv-bar{position:sticky;top:0;z-index:1000;display:flex;gap:16px;align-items:center;flex-wrap:wrap;
    padding:10px 20px;background:#14342b;color:#f4f1e8;font:500 14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}
  .rv-bar a{color:#f4f1e8;text-decoration:none;border-bottom:1px solid rgba(244,241,232,.35)}
  .rv-bar a:hover{border-bottom-color:#f4f1e8}
  .rv-bar strong{font-weight:650}
  .rv-bar .rv-sp{flex:1}
  .jp-RenderedHTMLCommon table{font-size:12px}
  .rv-plotly{width:100%;min-height:420px}
  body.jp-Notebook{max-width:1180px;margin:0 auto}
  .rv-bar{margin:0 -20px 12px}
</style>
"""


def notebook_header(title: str, ipynb_name: str) -> str:
    return (f'<div class="rv-bar"><a href="../index.html">← Volby Řevnice 2026</a>'
            f'<strong>{html.escape(title)}</strong><span class="rv-sp"></span>'
            f'<a href="{html.escape(ipynb_name)}" download>Stáhnout .ipynb</a></div>')


def plotly_to_html(fig: dict, n: int) -> str:
    div = f"rvplot-{n}"
    height = fig.get("layout", {}).get("height", 480)
    payload = json.dumps({"data": fig.get("data", []), "layout": fig.get("layout", {})}, ensure_ascii=False)
    payload = payload.replace("</", "<\\/")
    return (f'<div id="{div}" class="rv-plotly" style="height:{height}px"></div>'
            f'<script>(function(){{var f={payload};'
            f'Plotly.newPlot("{div}",f.data,f.layout,{{responsive:true,displaylogo:false}});}})();</script>')


def render_notebook(key: str, cfg: dict) -> bool:
    import nbformat
    from nbconvert import HTMLExporter

    src: Path | None = cfg["notebook"]
    if src is None or not src.exists():
        print(f"[{key}] notebook není k dispozici – přeskakuji")
        return False
    nb = nbformat.read(src, as_version=4)
    nb = copy.deepcopy(nb)
    n_plotly = 0
    for cell in nb.cells:
        for out in cell.get("outputs", []):
            data = out.get("data", {})
            if "application/vnd.plotly.v1+json" in data:
                fig = data.pop("application/vnd.plotly.v1+json")
                data.pop("text/html", None)
                n_plotly += 1
                data["text/html"] = plotly_to_html(fig, n_plotly)
    exporter = HTMLExporter(template_name="lab")
    body, _ = exporter.from_notebook_node(nb)
    ipynb_name = f"{key}.ipynb"
    head_inject = (f'<script src="../vendor/{PLOTLY_JS}"></script>'
                   f'<meta name="viewport" content="width=device-width, initial-scale=1">' + HEADER_CSS)
    body = body.replace("</head>", head_inject + "</head>", 1)
    body = body.replace("<html>", '<html lang="cs">', 1)
    body = body.replace("<title>", f"<title>{html.escape(cfg['title'])} – ", 1)
    i = body.find("<body")
    j = body.find(">", i) + 1
    body = body[:j] + notebook_header(cfg["title"], ipynb_name) + body[j:]
    for prefix, folder in cfg.get("assets", {}).items():
        target = NB_OUT / f"{key}-{prefix.strip('/')}"
        target.mkdir(parents=True, exist_ok=True)
        for f in folder.glob("*.html"):
            if f'src="{prefix}{f.name}"' in body:
                shutil.copyfile(f, target / f.name)
        body = body.replace(f'src="{prefix}', f'src="{target.name}/')
    (NB_OUT / f"{key}.html").write_text(body, encoding="utf-8")
    shutil.copyfile(src, NB_OUT / ipynb_name)
    print(f"[{key}] notebook → docs/notebooky/{key}.html ({n_plotly} Plotly grafů, {len(body) // 1024} kB)")
    return True


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-notebooks", action="store_true")
    args = ap.parse_args()

    for d in (DATA, NB_OUT, DOCS / "vendor", DOCS / "assets"):
        d.mkdir(parents=True, exist_ok=True)

    basic = build_basic()
    cl = build_claude(basic)
    gp = build_gpt(basic)
    build_comparison(basic, cl, gp)
    shutil.copyfile(ROOT / "claude" / "interactive" / "plotly.min.js", DOCS / "vendor" / PLOTLY_JS)
    shutil.copyfile(ROOT / "infografika-v1.png", DOCS / "assets" / "infografika-revnice-2026.png")

    available = {}
    for key, cfg in ANALYSES.items():
        if args.skip_notebooks:
            available[key] = (NB_OUT / f"{key}.html").exists()
        else:
            available[key] = render_notebook(key, cfg)
    write_data("analyzy", {k: {"title": ANALYSES[k]["title"], "notebook": available[k]} for k in ANALYSES})
    print("Hotovo: docs/ je připraveno.")


if __name__ == "__main__":
    sys.exit(main())
