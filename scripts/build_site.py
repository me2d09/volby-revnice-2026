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
import runpy
import shutil
import sys
import uuid
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
        "notebook": None,   # doplní se, až bude hotová (např. ROOT / "gpt" / "....ipynb")
    },
}

SHORT = {"ŠANCE": "ŠANCE", "TOP 09": "TOP 09", "DOBŘE": "DOBŘE", "Srdce": "Srdce Řevnic",
         "PRO": "PRO", "ODS": "ODS", "Perspektiva": "Perspektiva", "Naše Řevnice": "Naše Řevnice"}


def read_csv(path: Path, delimiter: str = ";") -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


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
    (DATA / "zakladni.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return data


# ---------------------------------------------------------------- 2. analýza Claude
def build_claude(basic: dict) -> None:
    res = ROOT / "claude" / "results"
    names = {(c["party"], c["position"]): c["name"] for c in basic["candidates"]}

    cands = []
    for r in read_csv(res / "candidate_estimates.csv"):
        party = SHORT[r["party"]]
        pos = int(r["position"])
        votes = int(r["votes_city"])
        c_med = num(r["C_median"], 0)
        cands.append({
            "party": party, "position": pos, "name": names[(party, pos)], "age": int(r["age"]),
            "elected": r["elected"] == "True", "votes": votes,
            "votes_precincts": [int(r[f"votes_p{k}"]) for k in (1, 2, 3, 4)],
            "lb": int(r["lb_precinct_sum"]), "lb_city": int(r["lb_city"]),
            "C": c_med, "C_q05": num(r["C_q05"], 0), "C_q95": num(r["C_q95"], 0),
            "C_q25": num(r["C_q25"], 0), "C_q75": num(r["C_q75"], 0),
            "S": votes - c_med,
            "C_share": num(r["C_share_median"], 3),
            "u": num(r["u_median"], 3), "u_q05": num(r["u_q05"], 3), "u_q95": num(r["u_q95"], 3),
            "p_u_pos": num(r["p_u_positive"], 3),
            "rank": num(r["rank_median"], 0), "rank_q05": num(r["rank_q05"], 0), "rank_q95": num(r["rank_q95"], 0),
            "p_top10": num(r["p_top10"], 3), "robust": r["robust_rank"],
            "baseline": num(r["baseline_median"], 1),
        })

    parties = []
    for r in read_csv(res / "party_estimates.csv"):
        parties.append({
            "party": SHORT[r["party"]], "votes": int(r["votes"]), "lb": int(r["lb_precinct_sum"]),
            "C": num(r["C_median"], 0), "C_q05": num(r["C_q05"], 0), "C_q95": num(r["C_q95"], 0),
            "C_share": num(r["C_share_median"], 3), "C_share_q05": num(r["C_share_q05"], 3),
            "C_share_q95": num(r["C_share_q95"], 3),
            "party_ballots": num(r["B_total_median"], 0), "party_ballots_q05": num(r["B_total_q05"], 0),
            "party_ballots_q95": num(r["B_total_q95"], 0),
            "p_k0": num(r["p_k0_median"], 3), "EK": num(r["EK_median"], 2),
        })

    precincts = []
    for r in read_csv(res / "precinct_estimates.csv"):
        precincts.append({
            "id": int(r["precinct"]), "votes": int(r["votes"]), "lb_monotone": int(r["lb_monotone"]),
            "lb_lp": num(r["lb_lp"], 0), "C": num(r["C_median"], 0), "C_q05": num(r["C_q05"], 0),
            "C_q95": num(r["C_q95"], 0), "C_share": num(r["C_share_median"], 3),
            "party_ballots": num(r["party_ballots_median"], 0),
            "pure_marks": num(r["pure_marks_median"], 0),
            "marks_from_party_voters": num(r["marks_from_party_voters_median"], 0),
        })

    sensitivity = []
    for r in read_csv(res / "sensitivity.csv", delimiter=","):
        sensitivity.append({
            "label": r["label"], "C": num(r["total_C_median"], 0), "C_q05": num(r["total_C_q05"], 0),
            "C_q95": num(r["total_C_q95"], 0), "cervena": num(r["cervena_C_median"], 0),
            "cervena_q05": num(r["cervena_C_q05"], 0), "cervena_q95": num(r["cervena_C_q95"], 0),
        })

    recovery = []
    for f in sorted(res.glob("recovery_*.csv")):
        r = read_csv(f, delimiter=",")[0]
        recovery.append({
            "scenario": r["scenario"], "true": num(r["total_true"], 0), "est": num(r["total_med"], 0),
            "lo": num(r["total_lo"], 0), "hi": num(r["total_hi"], 0),
            "corr": num(r["corr"], 3), "rank_corr": num(r["rank_corr"], 3),
            "top15_in_top20": int(float(r["top15_recovered_in_top20"])),
        })

    lopo = []
    for r in read_csv(res / "lopo.csv", delimiter=","):
        lopo.append({"precinct": int(r["precinct_out"]),
                     "mae_model": num(r["mae_model s u"], 2), "mae_no_u": num(r["mae_model bez u"], 2),
                     "mae_naive": num(r["mae_naivní podíly"], 2), "mae_uniform": num(r["mae_rovnoměrně"], 2)})

    run_info = json.loads((res / "run_info.json").read_text(encoding="utf-8"))

    out = {
        "source": "claude/results (notebook revnice_2026_bayesian_analysis.ipynb)",
        # Souhrnná čísla přebíráme z claude/results/souhrn_zjisteni.md (notebook, odd. 10),
        # kde jsou spočtena z posterioru realizovaných křížků.
        "headline": {
            "total_C": 6878, "total_C_q05": 5621, "total_C_q95": 8202, "total_C_share": 0.29,
            "sens_min": 5075, "sens_max": 7729,
            "lb_lp": 2890, "lb_lp_share": 0.121, "lb_monotone": 1493, "lb_city": 1096, "lb_leaders": 706,
            "p_k0": 0.76, "EK": 1.0, "no_party_ballots": 462, "no_party_ballots_q05": 332,
            "no_party_ballots_q95": 574, "no_party_mean_marks": 12,
            "beta": 0.63, "beta_q05": 0.51, "beta_q95": 0.77, "pos15_vs_leader": 0.18,
            "leaders_C_share": 0.59, "tail_C_share": 0.26,
            "recovery_err_min": -0.22, "recovery_err_max": 0.15, "valid_ballots": 1679, "unused_votes": 1246,
        },
        "candidates": cands, "parties": parties, "precincts": precincts,
        "sensitivity": sensitivity, "recovery": recovery, "lopo": lopo,
        "run_info": {"versions": run_info.get("versions"), "seed": run_info.get("seed"),
                     "sampling_time_s": round(run_info.get("sampling_time_main_s", 0)),
                     "divergences": run_info.get("divergences_main"), "n_free_params": run_info.get("n_free_params")},
    }
    (DATA / "claude.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


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
</style>
"""


def notebook_header(title: str, ipynb_name: str) -> str:
    return (f'<div class="rv-bar"><a href="../index.html">← Volby Řevnice 2026</a>'
            f'<strong>{html.escape(title)}</strong><span class="rv-sp"></span>'
            f'<a href="{html.escape(ipynb_name)}" download>Stáhnout .ipynb</a></div>')


def plotly_to_html(fig: dict) -> str:
    div = f"rvplot-{uuid.uuid4().hex[:10]}"
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
                data["text/html"] = plotly_to_html(fig)
                n_plotly += 1
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
    build_claude(basic)
    shutil.copyfile(ROOT / "claude" / "interactive" / "plotly.min.js", DOCS / "vendor" / PLOTLY_JS)
    shutil.copyfile(ROOT / "infografika-v1.png", DOCS / "assets" / "infografika-revnice-2026.png")

    available = {}
    for key, cfg in ANALYSES.items():
        if args.skip_notebooks:
            available[key] = (NB_OUT / f"{key}.html").exists()
        else:
            available[key] = render_notebook(key, cfg)
    (DATA / "analyzy.json").write_text(json.dumps(
        {k: {"title": ANALYSES[k]["title"], "notebook": available[k]} for k in ANALYSES},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("Hotovo: docs/ je připraveno.")


if __name__ == "__main__":
    sys.exit(main())
