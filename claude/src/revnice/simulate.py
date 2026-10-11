"""Simulátor hlasovacích lístků podle skutečné mechaniky (zákon č. 491/2001 Sb., § 34, § 41).

Generuje jednotlivé lístky a sčítá je přesně tak, jak to dělá okrsková komise:
  * lístek jen se stranou              -> každý z 15 kandidátů strany dostane 1 hlas
  * lístek se stranou + k kandidátů jiných stran -> prvních 15-k kandidátů strany po 1 hlasu,
    každý označený kandidát jiné strany 1 hlas
  * lístek jen s jednotlivci (m <= 15)  -> každý označený kandidát 1 hlas
Vrací H (pozorovatelné), pravé S, C, N a parametry — slouží k testu identifikovatelnosti.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .data import N_PARTIES, N_POS, N_PRECINCTS


@dataclass
class Truth:
    H: np.ndarray  # (P, 8, 15)
    S: np.ndarray  # (P, 8, 15) hlasy ze stranických lístků
    C: np.ndarray  # (P, 8, 15) individuální křížky
    N: np.ndarray  # (P, 8, 15) počet lístků strany s a k křížků jinde (k=0..14)
    pure_marks: np.ndarray  # (P,) křížky z lístků bez strany (vč. lístků strana+15)
    params: dict = field(default_factory=dict)

    @property
    def total_C(self) -> float:
        return float(self.C.sum())


def geometric_k(p0: float, ratio: float, kmax: int = 14) -> np.ndarray:
    """Rozdělení K na 0..kmax: P(0)=p0, zbytek geometricky klesá (bez useknutí)."""
    k = np.arange(1, kmax + 1)
    tail = ratio ** (k - 1)
    tail = (1 - p0) * tail / tail.sum()
    return np.concatenate([[p0], tail])


def simulate(
    n_ballots: np.ndarray,
    party_share: np.ndarray,
    pi_k: np.ndarray,
    pure_share: float,
    beta: float,
    sigma_u: float,
    sigma_local: float = 0.0,
    party_appeal_sd: float = 0.5,
    m_pure_probs: np.ndarray | None = None,
    seed: int = 1,
) -> Truth:
    """
    n_ballots   (P,)      počet platných lístků v okrsku
    party_share (P, 8)    pravděpodobnost označení strany s (mezi lístky se stranou)
    pi_k        (8, 15)   rozdělení K (0..14) pro voliče strany s (sloupec 15 = 0)
    pure_share  float     podíl lístků bez označené strany
    beta        float     sklon poklesu individuálních křížků s log(pořadí)
    sigma_u     float     sd individuální popularity kandidátů (log-škála)
    sigma_local float     sd lokální popularity (okrsek x kandidát)
    m_pure_probs (15,)    rozdělení počtu křížků m=1..15 na lístku bez strany
    """
    rng = np.random.default_rng(seed)
    P = len(n_ballots)
    if m_pure_probs is None:
        # většina "čistě osobních" voličů využije mnoho hlasů, ale ne všichni
        m_pure_probs = np.array([0.02] * 5 + [0.03] * 5 + [0.05, 0.07, 0.10, 0.13, 0.40])
        m_pure_probs = m_pure_probs / m_pure_probs.sum()
    positions = np.arange(1, N_POS + 1)
    u = rng.normal(0, sigma_u, size=(N_PARTIES, N_POS))
    appeal = rng.normal(0, party_appeal_sd, size=N_PARTIES)
    H = np.zeros((P, N_PARTIES, N_POS), dtype=int)
    S = np.zeros_like(H)
    C = np.zeros_like(H)
    N = np.zeros((P, N_PARTIES, N_POS), dtype=int)
    pure_marks = np.zeros(P, dtype=int)
    local = rng.normal(0, sigma_local, size=(P, N_PARTIES, N_POS)) if sigma_local > 0 else np.zeros((P, N_PARTIES, N_POS))
    for p in range(P):
        # atraktivita kandidátů pro individuální křížky v okrsku p
        logw = (
            appeal[:, None]
            + np.log(party_share[p])[:, None]  # sympatie ke straně v okrsku
            - beta * np.log(positions)[None, :]
            + u
            + local[p]
        )
        w = np.exp(logw)
        w = w / w.sum()
        wflat = w.ravel()
        n_pure = rng.binomial(n_ballots[p], pure_share)
        n_party = n_ballots[p] - n_pure
        parties = rng.choice(N_PARTIES, size=n_party, p=party_share[p])
        for s in parties:
            k = rng.choice(N_POS, p=pi_k[s])
            # k křížků u kandidátů jiných stran (bez opakování)
            if k > 0:
                mask = np.ones(N_PARTIES * N_POS, dtype=bool)
                mask[s * N_POS:(s + 1) * N_POS] = False
                pw = wflat * mask
                chosen = rng.choice(N_PARTIES * N_POS, size=k, replace=False, p=pw / pw.sum())
                for c in chosen:
                    C[p, c // N_POS, c % N_POS] += 1
            if k <= 14:
                N[p, s, k] += 1
                S[p, s, : N_POS - k] += 1
            else:  # strana + 15 křížků jinde = strana nedostane nic; nerozlišitelné od čistého lístku
                pure_marks[p] += 15
        for _ in range(n_pure):
            m = rng.choice(np.arange(1, N_POS + 1), p=m_pure_probs)
            chosen = rng.choice(N_PARTIES * N_POS, size=m, replace=False, p=wflat)
            for c in chosen:
                C[p, c // N_POS, c % N_POS] += 1
            pure_marks[p] += m
        H[p] = S[p] + C[p]
    return Truth(
        H=H, S=S, C=C, N=N, pure_marks=pure_marks,
        params=dict(u=u, appeal=appeal, beta=beta, sigma_u=sigma_u, pi_k=pi_k, pure_share=pure_share,
                    party_share=party_share, n_ballots=n_ballots),
    )


def scenario(name: str, seed: int = 1) -> Truth:
    """Předdefinované scénáře s velikostí blízkou Řevnicím (cca 390-420 lístků na okrsek)."""
    rng = np.random.default_rng(seed + 100)
    n_ballots = np.array([400, 420, 400, 440])
    base_share = np.array([0.20, 0.07, 0.23, 0.05, 0.10, 0.05, 0.20, 0.10])
    party_share = np.stack([base_share * np.exp(rng.normal(0, 0.25, N_PARTIES)) for _ in range(4)])
    party_share = party_share / party_share.sum(axis=1, keepdims=True)
    if name == "A_malo_krizku":  # málo křížků: P(K=0)=0.75, krátký ocas, 6 % čistých lístků
        pi = np.tile(geometric_k(0.75, 0.55), (N_PARTIES, 1))
        return simulate(n_ballots, party_share, pi, pure_share=0.06, beta=0.8, sigma_u=0.5, sigma_local=0.15, seed=seed)
    if name == "B_hodne_krizku":  # hodně křížků: P(K=0)=0.40, dlouhý ocas, 20 % čistých lístků
        pi = np.tile(geometric_k(0.40, 0.80), (N_PARTIES, 1))
        return simulate(n_ballots, party_share, pi, pure_share=0.20, beta=0.6, sigma_u=0.6, sigma_local=0.15, seed=seed)
    if name == "C_plochy_efekt_pozice":  # žádná výhoda pozice u křížků (nejhorší případ pro identifikaci)
        pi = np.tile(geometric_k(0.60, 0.70), (N_PARTIES, 1))
        return simulate(n_ballots, party_share, pi, pure_share=0.12, beta=0.0, sigma_u=0.5, sigma_local=0.15, seed=seed)
    if name == "D_ruzne_strany":  # K-rozdělení se liší mezi stranami
        p0s = np.array([0.8, 0.4, 0.7, 0.5, 0.6, 0.45, 0.75, 0.55])
        pi = np.stack([geometric_k(p0, 0.7) for p0 in p0s])
        return simulate(n_ballots, party_share, pi, pure_share=0.10, beta=0.7, sigma_u=0.6, sigma_local=0.15, seed=seed)
    raise ValueError(name)
