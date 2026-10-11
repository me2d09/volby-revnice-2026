"""Načtení dat a model-free (rigorózní) dolní meze.

Všechna primární data jsou v ``data/processed`` (vygenerováno skriptem
``scripts/prepare_and_validate.py`` z původních exportů ČSÚ).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

N_PRECINCTS, N_PARTIES, N_POS = 4, 8, 15
SEATS = 15

PARTY_SHORT = {
    1: "ŠANCE",
    2: "TOP 09",
    3: "DOBŘE",
    4: "Srdce",
    5: "PRO",
    6: "ODS",
    7: "Perspektiva",
    8: "Naše Řevnice",
}
PARTY_FULL = {
    1: "ŠANCE Řevnice",
    2: "TOP 09 a nezávislí kandidáti",
    3: "DOBŘE - Dialog o budoucnosti Řevnic",
    4: "Hnutí Srdce Řevnic",
    5: "PRO Řevnice",
    6: "ODS a nezávislí",
    7: "Perspektiva pro město",
    8: "Naše Řevnice",
}


def read_csv(path: Path) -> pd.DataFrame:
    """CSV v balíčku jsou UTF-8 s BOM a oddělovačem ';'."""
    return pd.read_csv(path, sep=";", encoding="utf-8-sig")


@dataclass
class ElectionData:
    """Pozorovaná data H[p, s, i] a pomocné tabulky."""

    precinct: pd.DataFrame  # 480 řádků
    city: pd.DataFrame  # 120 řádků
    H: np.ndarray  # (4, 8, 15) hlasy kandidátů po okrscích
    names: np.ndarray  # (8, 15) jména
    parties_2022_2026: pd.DataFrame
    precinct_party: pd.DataFrame
    precinct_2022: pd.DataFrame
    elected: pd.DataFrame

    @property
    def H_city(self) -> np.ndarray:
        return self.H.sum(axis=0)

    @property
    def party_votes(self) -> np.ndarray:  # (8,)
        return self.H.sum(axis=(0, 2))

    @property
    def precinct_votes(self) -> np.ndarray:  # (4,)
        return self.H.sum(axis=(1, 2))

    def long(self) -> pd.DataFrame:
        """Dlouhý formát (480 řádků) s indexy 0-based pro model."""
        df = self.precinct.copy()
        df["p"] = df["precinct"].astype(int) - 1
        df["s"] = df["party_id"].astype(int) - 1
        df["i"] = df["position"].astype(int) - 1
        df["block"] = df["p"] * N_PARTIES + df["s"]
        df["cand"] = df["s"] * N_POS + df["i"]
        df["party_short"] = df["party_id"].map(PARTY_SHORT)
        return df.sort_values(["p", "s", "i"]).reset_index(drop=True)


def load() -> ElectionData:
    prec = read_csv(DATA / "processed" / "precinct_candidates_2026.csv")
    city = read_csv(DATA / "processed" / "city_candidates_2026.csv")
    assert len(prec) == 480 and len(city) == 120
    H = np.zeros((N_PRECINCTS, N_PARTIES, N_POS), dtype=int)
    names = np.empty((N_PARTIES, N_POS), dtype=object)
    for r in prec.itertuples(index=False):
        H[r.precinct - 1, r.party_id - 1, r.position - 1] = r.votes
        names[r.party_id - 1, r.position - 1] = r.name
    assert H.sum() == 23939, H.sum()
    # kontrola shody s městským exportem
    for r in city.itertuples(index=False):
        assert H[:, r.party_id - 1, r.position - 1].sum() == r.votes, r
    return ElectionData(
        precinct=prec,
        city=city,
        H=H,
        names=names,
        parties_2022_2026=read_csv(DATA / "raw" / "strany_2022_2026.csv"),
        precinct_party=read_csv(DATA / "raw" / "okrsky_2026_party.csv"),
        precinct_2022=read_csv(DATA / "raw" / "okrsky_2022.csv"),
        elected=read_csv(DATA / "raw" / "zvoleni_2026_a_srovnani_2022.csv"),
    )


# ---------------------------------------------------------------------------
# Model-free dolní meze
# ---------------------------------------------------------------------------

def rigorous_lower_bound(H_block: np.ndarray) -> np.ndarray:
    """Dolní mez individuálních křížků z nerostoucí stranické složky.

    Pro pole hlasů ``H_block`` tvaru ``(..., 15)`` (poslední osa = pořadí na
    kandidátce) vrací ``max(0, H_i - min_{j<=i} H_j)``. Jde o přesnou
    matematickou mez: stranicky přidělené hlasy S_i jsou nerostoucí v i
    a S_j <= H_j, takže S_i <= min_{j<=i} H_j a C_i = H_i - S_i >= H_i - min.
    """
    running_min = np.minimum.accumulate(H_block, axis=-1)
    return np.maximum(0, H_block - running_min)


def bounds_table(data: ElectionData) -> pd.DataFrame:
    """120 kandidátů: městská mez vs. součet okrskových mezí."""
    lb_prec = rigorous_lower_bound(data.H)  # (4,8,15)
    lb_city = rigorous_lower_bound(data.H_city)  # (8,15)
    rows = []
    for s in range(N_PARTIES):
        for i in range(N_POS):
            rows.append(
                dict(
                    party_id=s + 1,
                    party=PARTY_SHORT[s + 1],
                    position=i + 1,
                    name=data.names[s, i],
                    votes=int(data.H_city[s, i]),
                    lb_city=int(lb_city[s, i]),
                    lb_precinct_sum=int(lb_prec[:, s, i].sum()),
                    **{f"lb_p{p+1}": int(lb_prec[p, s, i]) for p in range(N_PRECINCTS)},
                )
            )
    return pd.DataFrame(rows)


def lp_total_lower_bound(H_prec: np.ndarray) -> dict:
    """Rigorózní dolní mez CELKOVÉHO počtu individuálních křížků v okrsku (LP).

    Využívá jen mechaniku sčítání (žádné priory):
      (a) S[s,i] <= H[s,i],  S[s,1] >= S[s,2] >= ... >= S[s,15] >= 0,
      (b) každý platný lístek s označenou stranou (a nejvýše 14 křížky jinde)
          vytvoří přesně 15 kandidátských hlasů, lístek bez označené strany
          nejvýše 15, takže  sum_s S[s,1] = sum_s B[s] <= H_tot / 15.
    Minimalizujeme sum_{s,i} C = H_tot - sum_{s,i} S  =>  maximalizujeme sum S.
    Vrací slovník s hodnotou meze a optimálním S (pro ilustraci, není jednoznačné).
    """
    from scipy.optimize import linprog

    H = np.asarray(H_prec, dtype=float)  # (8, 15)
    S_, I_ = H.shape
    n = S_ * I_
    idx = lambda s, i: s * I_ + i
    c = -np.ones(n)  # max sum S  <=> min -sum S
    A_ub, b_ub = [], []
    # monotonie: S[s,i+1] - S[s,i] <= 0
    for s in range(S_):
        for i in range(I_ - 1):
            row = np.zeros(n)
            row[idx(s, i + 1)] = 1.0
            row[idx(s, i)] = -1.0
            A_ub.append(row)
            b_ub.append(0.0)
    # součet stranických lístků: sum_s S[s,1] <= H_tot/15
    row = np.zeros(n)
    for s in range(S_):
        row[idx(s, 0)] = 1.0
    A_ub.append(row)
    b_ub.append(H.sum() / I_)
    bounds = [(0.0, float(H[s, i])) for s in range(S_) for i in range(I_)]
    res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method="highs")
    assert res.status == 0, res.message
    S_opt = res.x.reshape(S_, I_)
    total_min_C = H.sum() - (-res.fun)
    return dict(min_total_C=float(total_min_C), S_opt=S_opt, max_party_ballots=float(H.sum() / I_))


def position_sum_lower_bound(H_prec: np.ndarray) -> np.ndarray:
    """Dolní mez součtu individuálních křížků přes strany pro každé pořadí i:
    sum_s C[s,i] >= max(0, sum_s H[s,i] - H_tot/15)."""
    H = np.asarray(H_prec, dtype=float)
    return np.maximum(0.0, H.sum(axis=0) - H.sum() / H.shape[1])


TITLES = {"Ing.", "Mgr.", "MUDr.", "Bc.", "MgA.", "Ph.D.", "MPA", "arch.", "doc.", "Dr.", "RNDr.", "MSc.", "PhDr.", "JUDr.", "DiS."}


def nice_name(name: str) -> str:
    """'Příjmení Jméno Tituly' (formát ČSÚ) -> 'Jméno Příjmení' bez titulů."""
    toks = [t for t in str(name).split() if t not in TITLES and not t.endswith(".")]
    if len(toks) < 2:
        return " ".join(toks)
    return f"{toks[-1]} {' '.join(toks[:-1])}"
