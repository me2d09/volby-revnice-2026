"""Grafy: statické (matplotlib -> PNG do figures/) i interaktivní (Plotly -> interactive/*.html).

Jednotný vizuální systém: 8 kandidátek = 8 pevných kategorických barev (pořadí
podle čísla kandidátky, nikdy se nepřebarvuje při filtrování), sekvenční modrá
pro velikosti (heatmapa), divergentní modrá-šedá-červená pro změny 2022→2026.
Paleta ověřena validátorem (CVD ΔE >= 8 pro sousední dvojice).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import N_PARTIES, N_POS, PARTY_SHORT

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures"
INTER = ROOT / "interactive"

PARTY_COLORS = {
    1: "#2a78d6",  # ŠANCE – modrá
    2: "#eb6834",  # TOP 09 – oranžová
    3: "#1baf7a",  # DOBŘE – akvamarín
    4: "#eda100",  # Srdce – žlutá
    5: "#e87ba4",  # PRO – magenta
    6: "#008300",  # ODS – zelená
    7: "#6250d6",  # Perspektiva – fialová
    8: "#e34948",  # Naše Řevnice – červená
}
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e6e6e3"
SEQ_BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
            "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
DIV_MID = "#f0efec"


def setup_style():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "axes.titlecolor": TEXT, "axes.labelcolor": TEXT2, "xtick.color": TEXT2, "ytick.color": TEXT2,
        "text.color": TEXT, "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
        "axes.titleweight": "bold", "axes.titlelocation": "left", "legend.frameon": False,
        "legend.fontsize": 9, "xtick.major.size": 0, "ytick.major.size": 0, "figure.dpi": 110,
        "savefig.dpi": 160, "savefig.bbox": "tight", "axes.axisbelow": True,
    })


def _save(fig, name: str):
    FIG.mkdir(exist_ok=True, parents=True)
    fig.savefig(FIG / name)
    return FIG / name


def seq_cmap():
    return mpl.colors.LinearSegmentedColormap.from_list("seqblue", SEQ_BLUE)


def div_cmap():
    return mpl.colors.LinearSegmentedColormap.from_list("divbr", ["#2a78d6", DIV_MID, "#e34948"])


# ---------------------------------------------------------------------------
# 1. Strany: hlasy a mandáty
# ---------------------------------------------------------------------------

def fig_parties(data, mandates: dict, save=True):
    df = data.parties_2022_2026.copy()
    df = df[df["hlasy_2026"] > 0]
    order = {PARTY_SHORT[k]: k for k in PARTY_SHORT}
    full2short = {v: PARTY_SHORT[k] for k, v in __import__("revnice.data", fromlist=["PARTY_FULL"]).PARTY_FULL.items()}
    df["short"] = df["strana"].map(full2short)
    df["pid"] = df["short"].map(order)
    df = df.sort_values("hlasy_2026", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    y = np.arange(len(df))
    ax.barh(y, df["hlasy_2026"], color=[PARTY_COLORS[p] for p in df["pid"]], height=0.62)
    ax.scatter(df["hlasy_2022"], y, marker="|", s=260, color=TEXT2, zorder=3, linewidths=1.6, label="hlasy 2022")
    for yi, (v, pid) in enumerate(zip(df["hlasy_2026"], df["pid"])):
        m = mandates.get(pid, 0)
        ax.text(v + 60, yi, f"{v:,}".replace(",", " ") + f"  ·  {m} mand.", va="center", fontsize=9, color=TEXT)
    ax.set_yticks(y, df["short"])
    ax.set_xlim(0, df["hlasy_2026"].max() * 1.28)
    ax.set_xlabel("Kandidátské hlasy (součet hlasů všech 15 kandidátů)")
    ax.set_title("Řevnice 2026: hlasy kandidátek a mandáty (svislá čárka = hlasy 2022)")
    ax.legend(loc="lower right")
    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", " ")))
    if save:
        _save(fig, "fig01_strany_hlasy_mandaty.png")
    return fig


# ---------------------------------------------------------------------------
# 2. Heatmapa okrsků
# ---------------------------------------------------------------------------

def fig_precinct_heatmap(data, save=True):
    H = data.H
    share = H.sum(axis=2) / H.sum(axis=(1, 2))[:, None] * 100  # (4, 8)
    fig, ax = plt.subplots(figsize=(9, 3.9))
    im = ax.imshow(share, cmap=seq_cmap(), aspect="auto", vmin=0, vmax=share.max())
    ax.set_xticks(range(N_PARTIES), [PARTY_SHORT[s + 1] for s in range(N_PARTIES)])
    ax.set_yticks(range(4), [f"okrsek {p+1}\n({int(H[p].sum()):,} hl.)".replace(",", " ") for p in range(4)])
    for p in range(4):
        for s in range(N_PARTIES):
            val = share[p, s]
            ax.text(s, p, f"{val:.1f} %", ha="center", va="center", fontsize=9,
                    color="white" if val > 0.55 * share.max() else TEXT)
    ax.grid(False)
    ax.set_title("Podíl kandidátek na kandidátských hlasech ve 4 okrscích (2026)")
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.set_label("% hlasů v okrsku")
    cb.outline.set_visible(False)
    if save:
        _save(fig, "fig02_heatmapa_okrsky.png")
    return fig


# ---------------------------------------------------------------------------
# 3. Rozdělení hlasů kandidátů podle pozice a strany
# ---------------------------------------------------------------------------

def fig_candidate_profiles(data, bounds: pd.DataFrame, save=True):
    Hc = data.H_city
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.2), sharex=True)
    pos = np.arange(1, N_POS + 1)
    for s, ax in enumerate(axes.ravel()):
        h = Hc[s]
        runmin = np.minimum.accumulate(h)
        col = PARTY_COLORS[s + 1]
        ax.fill_between(pos, 0, runmin, step="mid", color=col, alpha=0.12, linewidth=0)
        ax.step(pos, runmin, where="mid", color=col, linewidth=1.2, alpha=0.7)
        ax.plot(pos, h, "-", color=col, linewidth=1.6)
        ax.scatter(pos, h, s=22, color=col, zorder=3, edgecolor=SURFACE, linewidth=0.8)
        lb = bounds[bounds["party_id"] == s + 1].sort_values("position")["lb_precinct_sum"].values
        idx = np.where(lb >= 25)[0]
        for j, i in enumerate(idx):
            name = data.names[s, i].split()[0]
            dy = (8, 19, 30)[j % 3]
            ax.annotate(f"{name} (+{lb[i]})", (pos[i], h[i]), textcoords="offset points", xytext=(0, dy),
                        ha="center", fontsize=6.8, color=TEXT2)
        ax.set_title(f"{PARTY_SHORT[s+1]} · {int(h.sum()):,} hl.".replace(",", " "))
        ax.set_ylim(0, h.max() * 1.38)
        if s >= 4:
            ax.set_xlabel("pořadí na kandidátce")
        ax.set_xticks([1, 5, 10, 15])
    axes[0, 0].set_ylabel("hlasy kandidáta (město)")
    axes[1, 0].set_ylabel("hlasy kandidáta (město)")
    fig.suptitle("Hlasy kandidátů podle pořadí na kandidátce (město, 2026)\n"
                 "vyplněná plocha = běžné minimum H (horní mez stranické složky); popisky = rigorózní minimum osobních křížků ≥ 25",
                 x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    if save:
        _save(fig, "fig03_distribuce_kandidatu.png")
    return fig


# ---------------------------------------------------------------------------
# 4. Posteriorní žebříček
# ---------------------------------------------------------------------------

def fig_posterior_ranking(tab: pd.DataFrame, n=35, save=True, name="fig04_posterior_zebricek.png",
                          title="Odhad osobních křížků – 35 nejvyšších posteriorních mediánů"):
    t = tab.sort_values("C_median", ascending=False).head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9.5, 0.3 * n + 1.6))
    y = np.arange(len(t))
    cols = [PARTY_COLORS[p] for p in t["party_id"]]
    ax.hlines(y, t["C_q05"], t["C_q95"], color=cols, linewidth=1.2, alpha=0.6)
    ax.hlines(y, t["C_q25"], t["C_q75"], color=cols, linewidth=4)
    ax.scatter(t["C_median"], y, color=cols, s=26, zorder=4, edgecolor=SURFACE, linewidth=0.8)
    ax.scatter(t["lb_precinct_sum"], y, marker="|", s=90, color=TEXT, zorder=5, linewidths=1.2)
    labels = [f"{r.name}  ({r.party} {r.position}.)" + ("  ★" if r.elected else "") for r in t.itertuples()]
    ax.set_yticks(y, labels, fontsize=8.5)
    ax.set_xlabel("osobní křížky (město): medián, 50% a 90% interval; svislá čárka = rigorózní minimum")
    ax.set_title(title)
    xlo = min(0.0, float(t["C_q05"].min()) * 1.05)
    ax.set_xlim(xlo, max(t["C_q95"].max() * 1.05, 10))
    if xlo < 0:
        ax.axvline(0, color=TEXT2, linewidth=0.8)
    fig.text(0.99, 0.005, "★ = zvolen/a", ha="right", fontsize=8, color=TEXT2)
    if save:
        _save(fig, name)
    return fig


# ---------------------------------------------------------------------------
# 5. Rozklad strana vs. individuální složka
# ---------------------------------------------------------------------------

def fig_decomposition(data, S_med: np.ndarray, C_med: np.ndarray, C_lo, C_hi, parties=(1, 2, 3, 5), save=True):
    """S_med, C_med: (8,15) městské mediány; C_lo/C_hi 90% meze."""
    Hc = data.H_city
    pos = np.arange(1, N_POS + 1)
    fig, axes = plt.subplots(1, len(parties), figsize=(3.4 * len(parties), 4.2), sharey=False)
    for ax, pid in zip(np.atleast_1d(axes), parties):
        s = pid - 1
        col = PARTY_COLORS[pid]
        ax.bar(pos, S_med[s], color=col, alpha=0.35, width=0.72, label="stranická složka S (medián)")
        ax.bar(pos, C_med[s], bottom=S_med[s], color=col, width=0.72, label="osobní křížky C (medián)")
        ax.errorbar(pos, S_med[s] + C_med[s], yerr=[C_med[s] - C_lo[s], C_hi[s] - C_med[s]], fmt="none",
                    ecolor=TEXT2, elinewidth=0.8, capsize=0, alpha=0.7)
        ax.scatter(pos, Hc[s], s=16, color=TEXT, zorder=4, label="pozorované hlasy H")
        ax.set_title(PARTY_SHORT[pid])
        ax.set_xticks([1, 5, 10, 15])
        ax.set_xlabel("pořadí")
    axes[0].set_ylabel("hlasy (město)")
    handles, labels_ = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels_, loc="upper right", ncol=3, fontsize=8, bbox_to_anchor=(0.99, 0.985))
    fig.suptitle("Rozklad hlasů kandidátů na stranickou a osobní složku\n(posteriorní mediány, 90% interval pro C)",
                 x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    if save:
        _save(fig, "fig05_rozklad_strana_vs_individual.png")
    return fig


# ---------------------------------------------------------------------------
# 6. Příspěvky okrsků pro vybrané kandidáty
# ---------------------------------------------------------------------------

def fig_precinct_contributions(data, C_real: np.ndarray, selection: list[tuple[int, int]], save=True):
    """C_real: (n, 4, 8, 15). selection: seznam (party_id, position)."""
    fig, axes = plt.subplots(2, int(np.ceil(len(selection) / 2)), figsize=(2.6 * np.ceil(len(selection) / 2) + 1, 5.6))
    axes = np.atleast_1d(axes).ravel()
    for ax, (pid, posn) in zip(axes, selection):
        s, i = pid - 1, posn - 1
        draws = C_real[:, :, s, i]  # (n, 4)
        med = np.median(draws, axis=0)
        lo, hi = np.quantile(draws, [0.05, 0.95], axis=0)
        H4 = data.H[:, s, i]
        from .data import rigorous_lower_bound
        lb = rigorous_lower_bound(data.H)[:, s, i]
        x = np.arange(4)
        col = PARTY_COLORS[pid]
        ax.bar(x, H4, color=col, alpha=0.18, width=0.7, label="hlasy H")
        ax.vlines(x, lo, hi, color=col, linewidth=1.4)
        ax.scatter(x, med, color=col, s=30, zorder=4, edgecolor=SURFACE, label="osobní křížky C")
        ax.scatter(x, lb, marker="_", s=120, color=TEXT, zorder=5, label="rigor. minimum")
        ax.set_xticks(x, [f"o{p+1}" for p in range(4)])
        from .data import nice_name
        ax.set_title(f"{nice_name(data.names[s, i])}\n{PARTY_SHORT[pid]} {posn}. · {int(H4.sum())} hl.", fontsize=9)
        ax.set_ylim(0, max(H4.max() * 1.15, 10))
    for ax in axes[len(selection):]:
        ax.axis("off")
    handles, labels_ = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels_, loc="upper right", ncol=3, fontsize=8, bbox_to_anchor=(0.99, 0.985))
    fig.suptitle("Příspěvky okrsků: hlasy, posteriorní osobní křížky (medián, 90 %) a rigorózní minimum",
                 x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    if save:
        _save(fig, "fig06_prispevky_okrsku.png")
    return fig


# ---------------------------------------------------------------------------
# 7. Citlivost na priory
# ---------------------------------------------------------------------------

def fig_sensitivity(sens: pd.DataFrame, save=True):
    """sens: řádky = varianty; sloupce *_median,*_q05,*_q95 pro metriky."""
    metrics = [("total_C", "Osobní křížky celkem (město)"), ("share_C", "Podíl křížků na hlasech"),
               ("p_k0_mean", "P(K = 0), průměr stran"), ("mbar", "m̄ (křížky na lístku bez strany)"),
               ("cervena_C", "T. Červená: osobní křížky"), ("beta", "Sklon výhody pozice β")]
    metrics = [m for m in metrics if f"{m[0]}_median" in sens.columns]
    fig, axes = plt.subplots(1, len(metrics), figsize=(3.1 * len(metrics), 0.42 * len(sens) + 1.6), sharey=True)
    y = np.arange(len(sens))[::-1]
    for ax, (key, lab) in zip(axes, metrics):
        ax.hlines(y, sens[f"{key}_q05"], sens[f"{key}_q95"], color="#2a78d6", linewidth=1.3)
        ax.scatter(sens[f"{key}_median"], y, color="#2a78d6", s=28, zorder=3, edgecolor=SURFACE)
        base = sens.iloc[0]
        ax.axvline(base[f"{key}_median"], color=TEXT2, linewidth=0.8, linestyle=":")
        ax.set_title(lab, fontsize=9)
        ax.set_yticks(y, sens["label"], fontsize=8.5)
    fig.suptitle("Citlivost posterioru na priory a likelihood (medián, 90% interval; tečkovaně = hlavní model)",
                 x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    if save:
        _save(fig, "fig07_citlivost_priory.png")
    return fig


# ---------------------------------------------------------------------------
# 8. MCMC diagnostika
# ---------------------------------------------------------------------------

def fig_mcmc(idata, summary: pd.DataFrame, trace_vars=("beta", "sigma_u", "mbar", "total_C_city"), save=True):
    import arviz as az

    fig = plt.figure(figsize=(13, 7.2))
    gs = fig.add_gridspec(2, 4, height_ratios=[1, 1.35])
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(summary["r_hat"].dropna(), bins=30, color="#2a78d6")
    ax1.axvline(1.01, color="#e34948", linewidth=1)
    ax1.set_title("R̂ všech parametrů")
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.hist(summary["ess_bulk"].dropna(), bins=30, color="#2a78d6")
    ax2.axvline(400, color="#e34948", linewidth=1)
    ax2.set_title("ESS (bulk)")
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.hist(summary["ess_tail"].dropna(), bins=30, color="#2a78d6")
    ax3.axvline(400, color="#e34948", linewidth=1)
    ax3.set_title("ESS (tail)")
    ax4 = fig.add_subplot(gs[0, 3])
    en = idata.sample_stats["energy"]
    for c in range(en.sizes["chain"]):
        e = en.isel(chain=c).values
        ax4.hist(e - e.mean(), bins=30, histtype="step", linewidth=1.2, color=SEQ_BLUE[2 + 3 * c], label=f"řetězec {c+1}")
        ax4.hist(np.diff(e), bins=30, histtype="step", linewidth=1.2, linestyle="--", color=SEQ_BLUE[2 + 3 * c])
    ax4.set_title("Energie (plná = okrajová, čárkovaná = přechodová)")
    ax4.legend(fontsize=7)
    post = idata.posterior
    for j, v in enumerate(trace_vars):
        ax = fig.add_subplot(gs[1, j])
        da = post[v]
        for c in range(da.sizes["chain"]):
            ax.plot(da.isel(chain=c).values, linewidth=0.5, alpha=0.75, color=SEQ_BLUE[2 + 3 * c])
        ax.set_title(f"trace: {v}", fontsize=10)
        ax.set_xlabel("iterace")
    from .posterior import n_divergences
    div = n_divergences(idata)
    fig.suptitle(f"MCMC diagnostika hlavního modelu – divergence: {div}, řetězce: {post.sizes['chain']}, "
                 f"tahy/řetězec: {post.sizes['draw']}", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    if save:
        _save(fig, "fig08_mcmc_diagnostika.png")
    return fig


# ---------------------------------------------------------------------------
# 9. Posterior predictive checks
# ---------------------------------------------------------------------------

def fig_ppc(data, ppc: np.ndarray, save=True):
    """ppc: (n_draws, 4, 8, 15) replikované hlasy."""
    H = data.H
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.8))
    # (a) podle pozice (součet přes strany a okrsky)
    obs = H.sum(axis=(0, 1))
    rep = ppc.sum(axis=(1, 2))
    lo, hi = np.quantile(rep, [0.05, 0.95], axis=0)
    pos = np.arange(1, 16)
    axes[0].fill_between(pos, lo, hi, color="#2a78d6", alpha=0.25, label="90% PPC")
    axes[0].plot(pos, np.median(rep, axis=0), color="#2a78d6", linewidth=1.5, label="medián PPC")
    axes[0].scatter(pos, obs, color=TEXT, s=18, zorder=4, label="pozorováno")
    axes[0].set_title("podle pořadí (všechny strany)")
    axes[0].set_xlabel("pořadí")
    axes[0].legend(fontsize=7.5)
    # (b) podle strany: testovací statistika tvaru profilu = hlasy 15. místa / hlasy 1. místa (město)
    obs = H.sum(axis=0)[:, 14] / H.sum(axis=0)[:, 0]
    rep = ppc.sum(axis=1)[:, :, 14] / ppc.sum(axis=1)[:, :, 0]
    lo, hi = np.quantile(rep, [0.05, 0.95], axis=0)
    x = np.arange(N_PARTIES)
    axes[1].vlines(x, lo, hi, color=[PARTY_COLORS[s + 1] for s in x], linewidth=2)
    axes[1].scatter(x, np.median(rep, axis=0), color=[PARTY_COLORS[s + 1] for s in x], s=14, zorder=3)
    axes[1].scatter(x, obs, color=TEXT, s=18, zorder=4)
    axes[1].set_xticks(x, [PARTY_SHORT[s + 1] for s in x], rotation=45, ha="right", fontsize=8)
    axes[1].set_title("podle strany: hlasy 15. / 1. místa")
    # (c) podle okrsku: statistika = podíl hlasů prvních 5 míst na hlasech okrsku
    obs = H[:, :, :5].sum(axis=(1, 2)) / H.sum(axis=(1, 2))
    rep = ppc[:, :, :, :5].sum(axis=(2, 3)) / ppc.sum(axis=(2, 3))
    lo, hi = np.quantile(rep, [0.05, 0.95], axis=0)
    x = np.arange(4)
    axes[2].vlines(x, lo, hi, color="#2a78d6", linewidth=2)
    axes[2].scatter(x, np.median(rep, axis=0), color="#2a78d6", s=14, zorder=3)
    axes[2].scatter(x, obs, color=TEXT, s=18, zorder=4)
    axes[2].set_xticks(x, [f"okrsek {p+1}" for p in x])
    axes[2].set_title("podle okrsku: podíl hlasů 1.–5. místa")
    # (d) standardizovaná rezidua na úrovni 480 pozorování
    mu = ppc.mean(axis=0)
    sd = ppc.std(axis=0) + 1e-9
    z = ((H - mu) / sd).ravel()
    axes[3].hist(z, bins=30, color="#2a78d6")
    axes[3].set_title(f"standardizovaná rezidua (480); |z|>2: {(np.abs(z) > 2).sum()}")
    axes[3].set_xlabel("(H − průměr PPC) / sd PPC")
    fig.suptitle("Posterior predictive checks hlavního modelu", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    if save:
        _save(fig, "fig09_ppc.png")
    return fig


def fig_ppc_blocks(data, ppc: np.ndarray, save=True):
    """Profily všech 32 bloků: pozorováno vs. 90% PPC."""
    H = data.H
    fig, axes = plt.subplots(4, 8, figsize=(16, 7.5), sharex=True)
    pos = np.arange(1, 16)
    for p in range(4):
        for s in range(8):
            ax = axes[p, s]
            rep = ppc[:, p, s, :]
            lo, hi = np.quantile(rep, [0.05, 0.95], axis=0)
            col = PARTY_COLORS[s + 1]
            ax.fill_between(pos, lo, hi, color=col, alpha=0.25, linewidth=0)
            ax.plot(pos, H[p, s], color=TEXT, linewidth=1)
            ax.scatter(pos, H[p, s], color=TEXT, s=6, zorder=3)
            if p == 0:
                ax.set_title(PARTY_SHORT[s + 1], fontsize=9)
            if s == 0:
                ax.set_ylabel(f"okrsek {p+1}")
            ax.set_xticks([1, 8, 15])
            ax.tick_params(labelsize=7)
    fig.suptitle("PPC po blocích okrsek × kandidátka: černě pozorované hlasy, barevně 90% predikční pás",
                 x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    if save:
        _save(fig, "fig09b_ppc_bloky.png")
    return fig


# ---------------------------------------------------------------------------
# 10. Změny 2022 -> 2026
# ---------------------------------------------------------------------------

def fig_changes_2022_2026(data, save=True):
    from .data import PARTY_FULL
    df = data.parties_2022_2026.copy()
    full2pid = {v: k for k, v in PARTY_FULL.items()}
    df["pid"] = df["strana"].map(full2pid)
    df["short"] = df["pid"].map(PARTY_SHORT).fillna("Ř. SPOLEČNĚ (jen 2022)")
    df = df.sort_values("zmena_p_b")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw={"width_ratios": [1, 1.3]})
    ax = axes[0]
    y = np.arange(len(df))
    cols = ["#2a78d6" if v > 0 else "#e34948" for v in df["zmena_p_b"]]
    ax.barh(y, df["zmena_p_b"], color=cols, height=0.6)
    ax.axvline(0, color=TEXT2, linewidth=0.8)
    ax.set_yticks(y, df["short"])
    for yi, v in enumerate(df["zmena_p_b"]):
        ax.text(v + (0.4 if v >= 0 else -0.4), yi, f"{v:+.1f} p. b.", va="center", ha="left" if v >= 0 else "right", fontsize=8.5)
    ax.set_xlim(df["zmena_p_b"].min() - 5, df["zmena_p_b"].max() + 6)
    ax.set_title("Změna podílu kandidátek 2022 → 2026 (procentní body)")
    ax.set_xlabel("p. b. (DOBŘE a Ř. SPOLEČNĚ kandidovaly jen v jednom roce)")
    # zvolení: osobní hlasy 2022 vs 2026
    el = data.elected.copy()
    el = el[el["hlasy_2022_pokud_zvolen_2022"].notna()].sort_values("hlasy_2026")
    ax = axes[1]
    y = np.arange(len(el))
    ax.hlines(y, el["hlasy_2022_pokud_zvolen_2022"], el["hlasy_2026"], color=GRID, linewidth=2.2)
    ax.scatter(el["hlasy_2022_pokud_zvolen_2022"], y, color=TEXT2, s=36, zorder=3, label="2022")
    ax.scatter(el["hlasy_2026"], y, color="#2a78d6", s=36, zorder=4, label="2026")
    ax.set_yticks(y, [f"{z} ({PARTY_SHORT[full2pid[s]]})" for z, s in zip(el["zastupitel"], el["strana_2026"])], fontsize=8.5)
    ax.set_title("Zvolení zastupitelé, kteří byli zvoleni i v roce 2022: hlasy kandidáta")
    ax.set_xlabel("kandidátské hlasy (město); pozor: 2022 jiný počet voličů i kandidátek")
    ax.legend(loc="lower right")
    fig.tight_layout()
    if save:
        _save(fig, "fig10_zmeny_2022_2026.png")
    return fig


# ---------------------------------------------------------------------------
# 11. Simulační recovery
# ---------------------------------------------------------------------------

def fig_recovery(results: list[dict], save=True):
    """results: list of dict(name, C_true (120,), C_med, C_lo, C_hi, summary dict)."""
    n = len(results)
    nice = {"A_malo_krizku": "A – málo křížků", "B_hodne_krizku": "B – hodně křížků", "C_plochy_efekt_pozice": "C – plochý efekt pozice", "D_ruzne_strany": "D – strany se liší"}
    fig, axes = plt.subplots(1, n, figsize=(4.6 * n, 4.8))
    for ax, r in zip(np.atleast_1d(axes), results):
        ct, cm, lo, hi = r["C_true"], r["C_med"], r["C_lo"], r["C_hi"]
        inside = (ct >= lo) & (ct <= hi)
        ax.vlines(ct, lo, hi, color="#2a78d6", alpha=0.35, linewidth=1)
        ax.scatter(ct, cm, s=14, color=np.where(inside, "#2a78d6", "#e34948"), zorder=3)
        m = max(ct.max(), hi.max()) * 1.05
        ax.plot([0, m], [0, m], color=TEXT2, linewidth=0.8, linestyle=":")
        ax.set_xlabel("skutečné osobní křížky (simulace)")
        ax.set_ylabel("posteriorní medián (90% interval)")
        s = r["summary"]
        ax.set_title(f"{nice.get(r['name'], r['name'])}\nr = {s['corr']:.2f} · pokrytí 90% intervalů = {s['coverage90']:.0%} · Spearman pořadí = {s['rank_corr']:.2f}\n"
                     f"celkem skutečně {s['total_true']:.0f}, odhad {s['total_med']:.0f} [{s['total_lo']:.0f}; {s['total_hi']:.0f}]",
                     fontsize=8.5)
    fig.suptitle("Zpětné určení známé pravdy ze simulovaných lístků (městské součty po kandidátech; červeně = mimo 90% interval)",
                 x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    if save:
        _save(fig, "fig11_recovery.png")
    return fig


# ---------------------------------------------------------------------------
# 12. K-rozdělení a efekt pozice
# ---------------------------------------------------------------------------

def fig_k_and_position(idata, save=True):
    post = idata.posterior
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    k = np.arange(15)
    pi = post["pi"]
    ax = axes[0]
    for s in range(N_PARTIES):
        med = pi.isel(party=s).median(("chain", "draw")).values
        ax.plot(k, med, color=PARTY_COLORS[s + 1], linewidth=1.3, label=PARTY_SHORT[s + 1])
    pi0 = post["pi0"]
    lo, hi = pi0.quantile([0.05, 0.95], dim=("chain", "draw")).values
    ax.fill_between(k, lo, hi, color=TEXT2, alpha=0.15, label="pi0 (90 %)")
    ax.set_yscale("log")
    ax.set_xlabel("k = počet křížků u jiných stran na lístku se stranou")
    ax.set_ylabel("P(K = k)")
    ax.set_title("Posteriorní rozdělení K podle kandidátky")
    ax.legend(fontsize=7, ncol=2)
    ax = axes[1]
    theta = post["theta"]
    pos = np.arange(1, 16)
    med = np.exp(theta.median(("chain", "draw")).values)
    lo, hi = np.exp(theta.quantile([0.05, 0.95], dim=("chain", "draw")).values)
    ax.fill_between(pos, lo, hi, color="#2a78d6", alpha=0.2)
    ax.plot(pos, med, color="#2a78d6", linewidth=1.6, label="osobní křížky: exp(θ_i) (relativně k 1. místu)")
    q = post["q"].mean("party")
    qmed = q.median(("chain", "draw")).values
    ax.plot(pos, qmed, color="#e34948", linewidth=1.6, label="stranická složka: q_i = P(K ≤ 15−i)")
    ax.set_xlabel("pořadí na kandidátce")
    ax.set_title("Dva různé tvary poklesu s pořadím")
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1.05)
    ax = axes[2]
    pk0 = post["p_k0"]
    med = pk0.median(("chain", "draw")).values
    lo, hi = pk0.quantile([0.05, 0.95], dim=("chain", "draw")).values
    x = np.arange(N_PARTIES)
    ax.vlines(x, lo, hi, color=[PARTY_COLORS[s + 1] for s in x], linewidth=2)
    ax.scatter(x, med, color=[PARTY_COLORS[s + 1] for s in x], s=30, zorder=3, edgecolor=SURFACE)
    ax.set_xticks(x, [PARTY_SHORT[s + 1] for s in x], rotation=45, ha="right", fontsize=8)
    ax.set_title("P(K = 0): podíl lístků se stranou bez křížků jinde")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    if save:
        _save(fig, "fig12_K_rozdeleni_a_pozice.png")
    return fig


# ---------------------------------------------------------------------------
# 13. Prior predictive
# ---------------------------------------------------------------------------

def fig_prior_predictive(prior_H: np.ndarray, data, save=True):
    """prior_H: (n, 4, 8, 15) z prior predictive."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    pos = np.arange(1, 16)
    ax = axes[0]
    prof = prior_H[:, 0, 0, :]  # okrsek 1, ŠANCE
    for j in range(min(40, prof.shape[0])):
        ax.plot(pos, prof[j], color="#2a78d6", alpha=0.25, linewidth=0.8)
    ax.plot(pos, data.H[0, 0], color=TEXT, linewidth=1.8, label="pozorováno (okrsek 1, ŠANCE)")
    ax.set_title("Prior predictive: profily hlasů podle pořadí")
    ax.legend(fontsize=8)
    ax.set_xlabel("pořadí")
    ax = axes[1]
    tot = prior_H.sum(axis=(1, 2, 3))
    ax.hist(tot, bins=30, color="#2a78d6")
    ax.axvline(data.H.sum(), color=TEXT, linewidth=1.2)
    ax.set_title("Prior predictive: celkem hlasů")
    ax = axes[2]
    share15 = prior_H[:, :, :, 14].sum(axis=(1, 2)) / np.maximum(prior_H[:, :, :, 0].sum(axis=(1, 2)), 1)
    ax.hist(share15, bins=30, color="#2a78d6")
    ax.axvline(data.H[:, :, 14].sum() / data.H[:, :, 0].sum(), color=TEXT, linewidth=1.2)
    ax.set_title("Prior predictive: hlasy 15. místa / hlasy 1. místa")
    fig.suptitle("Prior predictive checks (svislá čára = pozorovaná hodnota)", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    if save:
        _save(fig, "fig13_prior_predictive.png")
    return fig


# ---------------------------------------------------------------------------
# 14. LOPO
# ---------------------------------------------------------------------------

def fig_lopo(lopo: pd.DataFrame, save=True):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    models = [c for c in lopo.columns if c.startswith("mae_")]
    names = [m.replace("mae_", "") for m in models]
    x = np.arange(4)
    wdt = 0.8 / len(models)
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6"]
    for j, m in enumerate(models):
        axes[0].bar(x + j * wdt - 0.4 + wdt / 2, lopo[m], width=wdt - 0.03, color=cols[j], label=names[j])
    axes[0].set_xticks(x, [f"okrsek {p+1}" for p in range(4)])
    axes[0].set_xlabel("vynechaný (predikovaný) okrsek")
    axes[0].set_ylabel("střední abs. chyba (hlasy na kandidáta)")
    axes[0].set_title("MAE predikce 120 kandidátů ve vynechaném okrsku")
    ref = lopo["lpd_model s u"]
    for j, m in enumerate(models):
        lp = lopo["lpd_" + names[j]] - ref
        axes[1].bar(x + j * wdt - 0.4 + wdt / 2, lp, width=wdt - 0.03, color=cols[j], label=names[j])
    axes[1].axhline(0, color=TEXT2, linewidth=0.8)
    axes[1].set_xticks(x, [f"okrsek {p+1}" for p in range(4)])
    axes[1].set_xlabel("vynechaný (predikovaný) okrsek")
    axes[1].set_ylabel("log skóre − log skóre modelu s u")
    axes[1].set_title("Log predikční skóre relativně k modelu s u (0 = stejně)")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper right", ncol=4, fontsize=8, bbox_to_anchor=(0.99, 0.985))
    fig.suptitle("Leave-one-precinct-out (n = 4, velmi omezená výpovědní hodnota)", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    if save:
        _save(fig, "fig14_lopo.png")
    return fig


# ---------------------------------------------------------------------------
# 15. Srovnání s nebayesovským benchmarkem
# ---------------------------------------------------------------------------

def fig_vs_baseline(tab: pd.DataFrame, save=True):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    ax = axes[0]
    cols = [PARTY_COLORS[p] for p in tab["party_id"]]
    ax.scatter(tab["baseline_median"], tab["C_median"], color=cols, s=22, edgecolor=SURFACE, linewidth=0.6)
    m = max(tab["baseline_median"].max(), tab["C_median"].max()) * 1.05
    ax.plot([0, m], [0, m], color=TEXT2, linewidth=0.8, linestyle=":")
    ax.set_xlabel("předchozí scénářový model (medián 45 scénářů)")
    ax.set_ylabel("bayesovský posteriorní medián")
    ax.set_title("Osobní křížky: kandidát po kandidátovi")
    ax = axes[1]
    sub = tab.sort_values("C_median", ascending=False).head(20).iloc[::-1]
    y = np.arange(len(sub))
    ax.hlines(y, sub["C_q05"], sub["C_q95"], color=[PARTY_COLORS[p] for p in sub["party_id"]], linewidth=1.2, alpha=0.6)
    ax.scatter(sub["C_median"], y, color=[PARTY_COLORS[p] for p in sub["party_id"]], s=26, zorder=4, label="bayes (medián, 90 %)")
    ax.scatter(sub["baseline_median"], y, marker="D", color=TEXT2, s=16, zorder=5, label="scénářový model")
    ax.set_yticks(y, [f"{r.name.split()[0]} ({r.party})" for r in sub.itertuples()], fontsize=8)
    ax.set_title("20 nejvyšších: bayes vs. benchmark")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    if save:
        _save(fig, "fig15_srovnani_benchmark.png")
    return fig


# ---------------------------------------------------------------------------
# Interaktivní Plotly grafy
# ---------------------------------------------------------------------------

def _plotly_layout(fig, title, height=600):
    fig.update_layout(
        title=dict(text=title, x=0.01, font=dict(size=16)),
        template="plotly_white", paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family="DejaVu Sans, Helvetica, Arial", color=TEXT, size=12),
        height=height, margin=dict(l=60, r=30, t=70, b=60), hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, showline=False)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, showline=False)
    return fig


def save_plotly(fig, name: str):
    INTER.mkdir(exist_ok=True, parents=True)
    path = INTER / name
    fig.write_html(path, include_plotlyjs="directory", full_html=True, config={"displaylogo": False})
    return path


def plotly_candidates(tab: pd.DataFrame):
    import plotly.graph_objects as go

    t = tab.sort_values("C_median", ascending=True).reset_index(drop=True)
    fig = go.Figure()
    for pid in range(1, 9):
        sub = t[t["party_id"] == pid]
        hover = [
            f"<b>{r.name}</b><br>{r.party}, {r.position}. místo{' · zvolen/a' if r.elected else ''}"
            f"<br>hlasy (město): {r.votes_city} = {r.votes_p1}+{r.votes_p2}+{r.votes_p3}+{r.votes_p4}"
            f"<br>rigorózní minimum: {r.lb_precinct_sum} (město: {r.lb_city})"
            f"<br>osobní křížky: medián {r.C_median:.0f}, 50 %: {r.C_q25:.0f}–{r.C_q75:.0f}, 90 %: {r.C_q05:.0f}–{r.C_q95:.0f}"
            f"<br>podíl osobních křížků: {r.C_share_median:.0%}"
            f"<br>osobní efekt u (po očištění o pozici): {r.u_median:+.2f} [{r.u_q05:+.2f}; {r.u_q95:+.2f}], P(u>0) = {r.p_u_positive:.2f}"
            f"<br>pořadí podle křížků: {r.rank_median:.0f} (90 %: {r.rank_q05:.0f}–{r.rank_q95:.0f})"
            for r in sub.itertuples()
        ]
        fig.add_trace(go.Scatter(
            x=sub["C_median"], y=sub["name"], mode="markers", name=PARTY_SHORT[pid],
            marker=dict(color=PARTY_COLORS[pid], size=8, line=dict(color=SURFACE, width=1)),
            error_x=dict(type="data", symmetric=False, array=sub["C_q95"] - sub["C_median"],
                         arrayminus=sub["C_median"] - sub["C_q05"], color=PARTY_COLORS[pid], thickness=1.2, width=0),
            hovertext=hover, hoverinfo="text", legendgroup=str(pid),
        ))
        fig.add_trace(go.Scatter(
            x=sub["lb_precinct_sum"], y=sub["name"], mode="markers", name=f"{PARTY_SHORT[pid]} – minimum",
            marker=dict(symbol="line-ns", color=TEXT, size=10, line=dict(width=1.5, color=TEXT)),
            hoverinfo="skip", legendgroup=str(pid), showlegend=False,
        ))
    buttons = [dict(label="Všechny strany", method="update", args=[{"visible": [True] * 16}])]
    for pid in range(1, 9):
        vis = [((j // 2) + 1 == pid) for j in range(16)]
        buttons.append(dict(label=PARTY_SHORT[pid], method="update", args=[{"visible": vis}]))
    fig.update_layout(updatemenus=[dict(type="dropdown", buttons=buttons, x=0.0, xanchor="left", y=1.08, yanchor="bottom")])
    _plotly_layout(fig, "Odhad osobních křížků – všech 120 kandidátů (medián, 90% interval, čárka = rigorózní minimum)", height=2200)
    fig.update_yaxes(categoryorder="array", categoryarray=list(t["name"]), tickfont=dict(size=9))
    fig.update_xaxes(title="osobní křížky (město, posteriorní)")
    return fig


def plotly_precinct_heatmap(data):
    import plotly.graph_objects as go

    H = data.H
    share = H.sum(axis=2) / H.sum(axis=(1, 2))[:, None] * 100
    fig = go.Figure(go.Heatmap(
        z=share, x=[PARTY_SHORT[s + 1] for s in range(8)], y=[f"okrsek {p+1}" for p in range(4)],
        colorscale=[[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)],
        text=[[f"{share[p, s]:.1f} %<br>{int(H[p, s].sum())} hl." for s in range(8)] for p in range(4)],
        texttemplate="%{text}", hovertemplate="%{y} · %{x}: %{z:.2f} %<extra></extra>", colorbar=dict(title="% hlasů"),
    ))
    _plotly_layout(fig, "Podíl kandidátek v okrscích (2026)", height=420)
    return fig


def plotly_decomposition(data, S_med, C_med, C_lo, C_hi):
    import plotly.graph_objects as go

    Hc = data.H_city
    pos = list(range(1, 16))
    fig = go.Figure()
    for pid in range(1, 9):
        s = pid - 1
        names = [data.names[s, i] for i in range(15)]
        vis = pid == 1
        fig.add_trace(go.Bar(x=pos, y=S_med[s], name="stranická složka S", marker_color=PARTY_COLORS[pid], opacity=0.4,
                             hovertext=[f"{n}<br>S medián: {v:.0f}" for n, v in zip(names, S_med[s])], hoverinfo="text", visible=vis))
        fig.add_trace(go.Bar(x=pos, y=C_med[s], name="osobní křížky C", marker_color=PARTY_COLORS[pid],
                             error_y=dict(type="data", symmetric=False, array=C_hi[s] - C_med[s], arrayminus=C_med[s] - C_lo[s], color=TEXT2),
                             hovertext=[f"{n}<br>C medián: {v:.0f} (90 %: {lo:.0f}–{hi:.0f})" for n, v, lo, hi in zip(names, C_med[s], C_lo[s], C_hi[s])],
                             hoverinfo="text", visible=vis))
        fig.add_trace(go.Scatter(x=pos, y=Hc[s], mode="markers", name="pozorované hlasy H", marker=dict(color=TEXT, size=7),
                                 hovertext=[f"{n}<br>H: {v}" for n, v in zip(names, Hc[s])], hoverinfo="text", visible=vis))
    buttons = []
    for pid in range(1, 9):
        vis = [(j // 3) + 1 == pid for j in range(24)]
        buttons.append(dict(label=PARTY_SHORT[pid], method="update", args=[{"visible": vis}, {"title": f"Rozklad hlasů: {PARTY_SHORT[pid]}"}]))
    fig.update_layout(barmode="stack", updatemenus=[dict(type="dropdown", buttons=buttons, x=0.0, xanchor="left", y=1.12, yanchor="bottom")])
    _plotly_layout(fig, "Rozklad hlasů: ŠANCE", height=520)
    fig.update_xaxes(title="pořadí na kandidátce", dtick=1)
    fig.update_yaxes(title="hlasy (město)")
    return fig


def plotly_candidate_browser(data, C_real: np.ndarray, S_med4: np.ndarray):
    """Procházení kandidátů: pro každého 4 okrsky – H, S, C (medián, 90 %)."""
    import plotly.graph_objects as go
    from .data import rigorous_lower_bound

    lb = rigorous_lower_bound(data.H)
    fig = go.Figure()
    x = [f"okrsek {p+1}" for p in range(4)]
    labels = []
    for s in range(8):
        for i in range(15):
            draws = C_real[:, :, s, i]
            med = np.median(draws, axis=0)
            lo, hi = np.quantile(draws, [0.05, 0.95], axis=0)
            vis = (s == 0 and i == 9)
            col = PARTY_COLORS[s + 1]
            fig.add_trace(go.Bar(x=x, y=data.H[:, s, i], name="hlasy H", marker_color=col, opacity=0.25, visible=vis))
            fig.add_trace(go.Scatter(x=x, y=med, mode="markers", name="osobní křížky C (medián, 90 %)", marker=dict(color=col, size=10),
                                     error_y=dict(type="data", symmetric=False, array=hi - med, arrayminus=med - lo, color=col), visible=vis))
            fig.add_trace(go.Scatter(x=x, y=lb[:, s, i], mode="markers", name="rigorózní minimum", marker=dict(symbol="line-ew", size=16, color=TEXT, line=dict(width=2, color=TEXT)), visible=vis))
            labels.append(f"{data.names[s, i]} ({PARTY_SHORT[s+1]} {i+1}.)")
    buttons = []
    for j, lab in enumerate(labels):
        vis = [False] * (3 * 120)
        vis[3 * j:3 * j + 3] = [True, True, True]
        buttons.append(dict(label=lab, method="update", args=[{"visible": vis}, {"title": f"Příspěvky okrsků: {lab}"}]))
    fig.update_layout(updatemenus=[dict(type="dropdown", buttons=buttons, x=0.0, xanchor="left", y=1.12, yanchor="bottom", active=9)])
    _plotly_layout(fig, f"Příspěvky okrsků: {labels[9]}", height=480)
    fig.update_yaxes(title="hlasy / křížky v okrsku")
    return fig


def plotly_changes(data):
    import plotly.graph_objects as go
    from .data import PARTY_FULL

    df = data.parties_2022_2026.copy()
    full2pid = {v: k for k, v in PARTY_FULL.items()}
    df["pid"] = df["strana"].map(full2pid)
    df["short"] = df["pid"].map(PARTY_SHORT).fillna("Ř. SPOLEČNĚ")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["short"], y=df["podil_2022_pct"], name="2022", marker_color=TEXT2,
                         hovertemplate="%{x} 2022: %{y:.2f} %<extra></extra>"))
    fig.add_trace(go.Bar(x=df["short"], y=df["podil_2026_pct"], name="2026", marker_color="#2a78d6",
                         hovertemplate="%{x} 2026: %{y:.2f} %<extra></extra>"))
    fig.update_layout(barmode="group")
    _plotly_layout(fig, "Podíly kandidátek na kandidátských hlasech: 2022 vs. 2026", height=420)
    fig.update_yaxes(title="% kandidátských hlasů")
    return fig
