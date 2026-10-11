"""Hierarchický bayesovský model rozkladu hlasů H = S + C (PyMC).

Notace (podrobně v methodology.md):
    p = okrsek (4), s = kandidátka (8), i = pořadí na kandidátce (15),
    k = počet křížků u kandidátů JINÝCH stran na lístku s označenou stranou (0..14).

Stranická složka (mechanická):
    B[p,s]   = počet efektivních lístků s označenou stranou s (k <= 14)
    pi[s,k]  = rozdělení K pro voliče strany s
    q[s,i]   = P(K <= 15 - i) = sum_{k=0}^{15-i} pi[s,k]
    S[p,s,i] = B[p,s] * q[s,i]

Zákon zachování hlasů (každý lístek se stranou vytvoří přesně 15 hlasů,
lístek bez strany nejvýše 15):
    H_tot[p] = 15 * sum_s B[p,s] + R[p],   R[p] = křížky z lístků bez označené strany
    => (15*B[p,1..8], R[p]) je rozklad H_tot[p]; parametrizujeme simplexem g[p,·].

Individuální složka (alokační):
    zásobník křížků v okrsku p = R[p] + sum_s' B[p,s'] * E[K_s']
    w[p,s,i] ∝ exp(a[s] + e[p,s] + theta[i] + u[s,i] + v[p,s,i])  (softmax přes 120 kandidátů)
    křížky voličů strany s' jdou jen na kandidáty jiných stran (renormalizace),
    muC[p,s,i] = w[p,s,i] * ( R[p] + sum_{s'!=s} B[p,s'] E[K_s'] / (1 - W[p,s']) )

Likelihood:  H[p,s,i] ~ Poisson(S + muC)   (aproximace očekávanou hodnotou; viz metodika).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pymc as pm
import pytensor.tensor as pt

from .data import N_PARTIES, N_POS


@dataclass
class PriorConfig:
    """Všechny apriorní volby na jednom místě (pro citlivostní analýzu)."""

    # --- rozdělení K (počet křížků u jiných stran na stranickém lístku) ---
    p0_mean: float = 0.5  # apriorní střed P(K=0)
    tail_ratio: float = 0.70  # geometrický pokles P(K=k+1)/P(K=k) pro k>=1 (bez useknutí)
    k_logit_sd: float = 1.0  # šířka prioru logitů pi0 (po kategoriích)
    sigma_eta_sd: float = 0.5  # HalfNormal: kolik se K-rozdělení liší mezi stranami
    # --- rozklad hlasů okrsku na stranické lístky a čistě osobní křížky ---
    g_alpha_party: float = 1.0  # Dirichlet koncentrace pro 8 stran
    g_alpha_pure: float = 1.0  # Dirichlet koncentrace pro "čistě osobní" složku R (bez V)
    n_valid_ballots: float | None = 1679  # platné lístky v celém městě (ČSÚ); None = nepoužít
    mbar_beta: tuple = (2.0, 2.0)  # Beta prior pro (m̄-1)/(m̄_max-1): průměrný počet křížků na lístku bez strany
    r_split_alpha: float = 2.0  # Dirichlet: rozdělení čistých křížků mezi okrsky
    # --- alokace individuálních křížků ---
    sigma_a_sd: float = 1.0  # strana
    sigma_e_sd: float = 0.5  # strana x okrsek
    beta_mu: float = 0.7  # sklon poklesu individuálních křížků s log(pořadí)
    beta_sd: float = 0.5
    sigma_psi_sd: float = 0.25  # hladké odchylky od log-lineárního tvaru
    sigma_u_sd: float = 0.75  # HalfNormal: rozptyl individuální popularity kandidátů
    sigma_v_sd: float = 0.3  # HalfNormal: lokální (okrsková) popularita
    # --- struktura ---
    candidate_effects: bool = True  # u[s,i]
    local_effects: bool = True  # v[p,s,i]
    conserve: bool = True  # zákon zachování hlasů (False = jen pro demonstraci)
    saturation: bool = True  # nejvýše 1 křížek pro kandidáta na lístku (poissonizovaný výběr bez vracení)
    sat_iter_pure: int = 4  # kroky pevného bodu pro lístky bez strany
    likelihood: str = "normal_mech"  # "normal_mech" | "poisson" | "negbin"
    phi_sd: float = 0.05  # HalfNormal prior dodatečné relativní disperze (normal_mech)
    negbin_alpha_mu: float = 50.0

    def k_prior_logits(self) -> np.ndarray:
        """Střed prioru logitů pi0: P(K=0)=p0, zbytek geometricky (bez useknutí)."""
        k = np.arange(1, N_POS)
        tail = self.tail_ratio ** (k - 1)
        tail = (1 - self.p0_mean) * tail / tail.sum()
        w = np.concatenate([[self.p0_mean], tail])
        return np.log(w)

    def to_dict(self):
        return asdict(self)


def build_model(H: np.ndarray, cfg: PriorConfig | None = None) -> pm.Model:
    """Sestaví PyMC model pro pole hlasů ``H`` tvaru (P, 8, 15).

    ``H`` může mít méně než 4 okrsky (použito v leave-one-precinct-out).
    """
    cfg = cfg or PriorConfig()
    H = np.asarray(H, dtype=int)
    P, S_, I_ = H.shape
    assert S_ == N_PARTIES and I_ == N_POS
    positions = np.arange(1, N_POS + 1)
    H_tot = H.sum(axis=(1, 2)).astype(float)  # (P,)
    H1 = H[:, :, 0].astype(float)
    kvals = np.arange(N_POS, dtype=float)
    offdiag = 1.0 - np.eye(N_PARTIES)  # [s, s'] = 1 pokud s != s'

    coords = {
        "precinct": np.arange(1, P + 1),
        "party": np.arange(1, N_PARTIES + 1),
        "position": positions,
        "k": np.arange(0, N_POS),
        "cell": [f"party{s}" for s in range(1, 9)] + ["pure"],
    }
    with pm.Model(coords=coords) as model:
        # ---------------- K-rozdělení (hierarchické, logistic-normal) -------------
        eta0 = pm.Normal("eta0", mu=cfg.k_prior_logits(), sigma=cfg.k_logit_sd, dims="k")
        sigma_eta = pm.HalfNormal("sigma_eta", sigma=cfg.sigma_eta_sd)
        z_eta = pm.Normal("z_eta", 0.0, 1.0, dims=("party", "k"))
        eta = eta0[None, :] + sigma_eta * z_eta
        pi = pm.Deterministic("pi", pm.math.softmax(eta, axis=1), dims=("party", "k"))
        pm.Deterministic("pi0", pm.math.softmax(eta0), dims="k")
        cum = pt.cumsum(pi, axis=1)  # cum[:, j] = P(K <= j)
        q = pm.Deterministic("q", cum[:, ::-1], dims=("party", "position"))  # q[:, i-1] = P(K <= 15-i)
        pm.Deterministic("p_k0", pi[:, 0], dims="party")
        EK = pm.Deterministic("EK", pt.sum(pi * kvals[None, :], axis=1), dims="party")

        # ---------------- rozklad hlasů okrsku: stranické lístky B a čisté křížky R ---
        if cfg.conserve and cfg.n_valid_ballots is not None:
            # Známe počet platných lístků V (ČSÚ, celé město). Lístek se stranou dává přesně
            # 15 hlasů, lístek bez strany m_b <= 15 hlasů, takže nevyužité hlasy
            # 15 V - H_tot = sum_{čisté lístky} (15 - m_b).  Parametr mbar = průměrné m
            # na lístku bez strany určuje M = počet čistých lístků a R = jejich křížky.
            V = float(cfg.n_valid_ballots)
            H_all = float(H_tot.sum())
            unused = N_POS * V - H_all
            mbar_max = H_all / V  # m̄ nemůže přesáhnout průměr hlasů na lístek (14.26 v Řevnicích)
            mbar_frac = pm.Beta("mbar_frac", alpha=cfg.mbar_beta[0], beta=cfg.mbar_beta[1])
            mbar = pm.Deterministic("mbar", 1.0 + (mbar_max - 1.0) * mbar_frac)
            M_city = pm.Deterministic("M_city", unused / (N_POS - mbar))  # čisté lístky
            R_city = pm.Deterministic("R_city", mbar * M_city)  # křížky z čistých lístků
            pm.Deterministic("B_city", V - M_city)
            r_split = pm.Dirichlet("r_split", a=np.full(P, cfg.r_split_alpha), dims="precinct")
            R = pm.Deterministic("R", R_city * r_split, dims="precinct")
            # R_p nesmí přesáhnout hlasy okrsku (jinak záporný počet stranických lístků)
            pm.Potential("R_feasible", pt.sum(pt.switch(R > H_tot, -np.inf, 0.0)))
            Bsum = (H_tot - R) / N_POS  # stranické lístky v okrsku (zákon zachování)
            g = pm.Dirichlet("g", a=np.full(N_PARTIES, cfg.g_alpha_party), dims=("precinct", "party"))
            B = pm.Deterministic("B", g * Bsum[:, None], dims=("precinct", "party"))
        elif cfg.conserve:
            alpha_g = np.array([cfg.g_alpha_party] * N_PARTIES + [cfg.g_alpha_pure])
            g = pm.Dirichlet("g", a=alpha_g, dims=("precinct", "cell"))
            B = pm.Deterministic("B", g[:, :N_PARTIES] * (H_tot / N_POS)[:, None], dims=("precinct", "party"))
            R = pm.Deterministic("R", g[:, N_PARTIES] * H_tot, dims="precinct")
        else:  # bez zákona zachování (pouze pro demonstraci nekonzistence)
            omega_logit = pm.Normal("omega_logit", mu=1.0, sigma=1.0, dims=("precinct", "party"))
            B = pm.Deterministic("B", pm.math.sigmoid(omega_logit) * H1, dims=("precinct", "party"))
            log_R = pm.Normal("log_R", mu=np.log(0.1 * H_tot), sigma=1.5, dims="precinct")
            R = pm.Deterministic("R", pm.math.exp(log_R), dims="precinct")
        S = B[:, :, None] * q[None, :, :]  # (P, 8, 15)
        G = pm.Deterministic("G", B * EK[None, :], dims=("precinct", "party"))  # křížky od voličů strany s'

        # ---------------- alokační váhy individuálních křížků --------------------
        sigma_a = pm.HalfNormal("sigma_a", sigma=cfg.sigma_a_sd)
        sigma_e = pm.HalfNormal("sigma_e", sigma=cfg.sigma_e_sd)
        a = pm.Deterministic("a", sigma_a * pm.Normal("z_a", 0, 1, dims="party"), dims="party")
        e = pm.Deterministic(
            "e", sigma_e * pm.Normal("z_e", 0, 1, dims=("precinct", "party")), dims=("precinct", "party")
        )
        beta = pm.Normal("beta", mu=cfg.beta_mu, sigma=cfg.beta_sd)
        sigma_psi = pm.HalfNormal("sigma_psi", sigma=cfg.sigma_psi_sd)
        z_psi = pm.Normal("z_psi", 0, 1, shape=N_POS - 1)
        psi = pt.concatenate([pt.zeros(1), sigma_psi * z_psi])  # psi_1 = 0
        theta = pm.Deterministic("theta", -beta * np.log(positions) + psi, dims="position")

        logw = a[None, :, None] + e[:, :, None] + theta[None, None, :]
        if cfg.candidate_effects:
            sigma_u = pm.HalfNormal("sigma_u", sigma=cfg.sigma_u_sd)
            u = pm.Deterministic(
                "u", sigma_u * pm.Normal("z_u", 0, 1, dims=("party", "position")), dims=("party", "position")
            )
            logw = logw + u[None, :, :]
        if cfg.local_effects:
            sigma_v = pm.HalfNormal("sigma_v", sigma=cfg.sigma_v_sd)
            v = pm.Deterministic(
                "v",
                sigma_v * pm.Normal("z_v", 0, 1, dims=("precinct", "party", "position")),
                dims=("precinct", "party", "position"),
            )
            logw = logw + v
        # softmax přes všech 120 kandidátů v okrsku
        logw_flat = logw.reshape((P, N_PARTIES * N_POS))
        w = pm.math.softmax(logw_flat, axis=1).reshape((P, N_PARTIES, N_POS))
        pm.Deterministic("w", w, dims=("precinct", "party", "position"))
        W = pt.sum(w, axis=2)  # (P, 8) váha celé strany
        if cfg.saturation and (not cfg.conserve or cfg.n_valid_ballots is None):
            raise ValueError("saturation vyžaduje conserve=True a n_valid_ballots")
        if not cfg.saturation:
            # zásobník křížků dostupný pro kandidáty strany s: R + sum_{s'!=s} G[s']/(1-W[s'])
            pool = R[:, None] + pt.dot(G / (1.0 - W), offdiag)  # (P, 8)
            muC = pm.Deterministic("muC", w * pool[:, :, None], dims=("precinct", "party", "position"))
        else:
            # Saturace: na jednom lístku může kandidát dostat nejvýše 1 křížek. Volič s m křížky
            # vybírá m RŮZNÝCH kandidátů; pravděpodobnost výběru kandidáta c aproximujeme
            # p_c = 1 - exp(-m * lam * w_c), kde lam je zvoleno tak, aby sum_c p_c = m
            # (poissonizace výběru bez vracení; lam se najde několika kroky pevného bodu).
            w_flat = w.reshape((P, N_PARTIES * N_POS))

            def sat_probs(m, wgt, n_iter):
                """m: (...,) počet křížků; wgt: (..., 120) váhy (součet 1). Vrací p: (..., 120)."""
                lam = pt.ones_like(m)
                for _ in range(n_iter):
                    p_ = 1.0 - pt.exp(-(m * lam)[..., None] * wgt)
                    lam = lam * m / pt.maximum(pt.sum(p_, axis=-1), 1e-9)
                return 1.0 - pt.exp(-(m * lam)[..., None] * wgt)

            # (a) lístky bez strany: M_p lístků, průměrně mbar křížků, váhy w (všech 120)
            M_p = R / mbar  # (P,)
            C_pure = M_p[:, None] * sat_probs(pt.full((P,), mbar), w_flat, n_iter=cfg.sat_iter_pure)  # (P, 120)
            # (b) lístky se stranou s' a k křížky jinde: váhy w/(1-W[s']) mimo stranu s'.
            #     Pro k <= 14 je saturace slabší; používáme lam = 1 (p_c = 1 - exp(-k w~_c)),
            #     sečteno přes rozdělení K:  sum_k pi_k (1 - exp(-k w~_c)) = 1 - PGF_K(exp(-w~_c)).
            mask = np.ones((N_PARTIES, N_PARTIES * N_POS))
            for s_ in range(N_PARTIES):
                mask[s_, s_ * N_POS:(s_ + 1) * N_POS] = 0.0
            w_excl = w_flat[:, None, :] * mask[None, :, :]  # (P, 8, 120)
            w_excl = w_excl / pt.sum(w_excl, axis=-1, keepdims=True)
            kgrid = np.arange(1, N_POS, dtype=float)  # k = 1..14
            # korekce lam prvního řádu: sum_c (1 - exp(-k lam w~_c)) = k  =>  lam ≈ 1 + k * sum_c w~_c^2 / 2
            sw2 = pt.sum(w_excl ** 2, axis=-1)  # (P, 8)
            lam_k = 1.0 + 0.5 * kgrid[None, None, :] * sw2[:, :, None]  # (P, 8, 14)
            p_k = 1.0 - pt.exp(-(kgrid[None, None, :, None] * lam_k[:, :, :, None]) * w_excl[:, :, None, :])  # (P, 8, 14, 120)
            C_party = pt.sum((B[:, :, None, None] * pi[None, :, 1:, None]) * p_k, axis=(1, 2))  # (P, 120)
            muC = pm.Deterministic(
                "muC", (C_pure + C_party).reshape((P, N_PARTIES, N_POS)), dims=("precinct", "party", "position")
            )
        mu = pm.Deterministic("mu", S + muC, dims=("precinct", "party", "position"))
        pm.Deterministic("S", S, dims=("precinct", "party", "position"))
        pm.Deterministic("share_C", muC / mu, dims=("precinct", "party", "position"))
        pm.Deterministic("total_C", pt.sum(muC, axis=(1, 2)), dims="precinct")
        pm.Deterministic("total_C_city", pt.sum(muC))

        # ---------------- likelihood ---------------------------------------------
        if cfg.likelihood == "normal_mech":
            # mechanistický rozptyl: S_i ~ Binomial(B, q_i)  => var = B q (1-q);
            # C_i ~ Poisson(muC)  => var = muC;  phi = dodatečná (nemechanická) disperze
            phi = pm.HalfNormal("phi", sigma=cfg.phi_sd)
            var = B[:, :, None] * q[None, :, :] * (1.0 - q[None, :, :]) + muC + (phi * mu) ** 2 + 0.5
            pm.Deterministic("sd_H", pt.sqrt(var), dims=("precinct", "party", "position"))
            pm.Normal("H", mu=mu, sigma=pt.sqrt(var), observed=H, dims=("precinct", "party", "position"))
        elif cfg.likelihood == "mvnormal_mech":
            # Přesnější varianta: společná kovariance stranické složky uvnitř bloku.
            # S_i = sum_{k<=15-i} N_k, N ~ Multinomial(B, pi)  =>
            # Cov(S_i, S_j) = B * q_max(i,j) * (1 - q_min(i,j));  C_i nezávislé, var = muC.
            phi = pm.HalfNormal("phi", sigma=cfg.phi_sd)
            qi = q[:, :, None]  # (8, 15, 1)
            qj = q[:, None, :]  # (8, 1, 15)
            cov_shape = pt.minimum(qi, qj) * (1.0 - pt.maximum(qi, qj))  # (8, 15, 15) na jednotku B
            eye = np.eye(N_POS)
            H_flat = H.reshape(P * N_PARTIES, N_POS)
            cov = (
                B.reshape((P * N_PARTIES,))[:, None, None] * pt.tile(cov_shape, (P, 1, 1))
                + (muC + (phi * mu) ** 2 + 0.5).reshape((P * N_PARTIES, N_POS))[:, :, None] * eye[None, :, :]
            )
            pm.MvNormal("H", mu=mu.reshape((P * N_PARTIES, N_POS)), cov=cov, observed=H_flat)
        elif cfg.likelihood == "poisson":
            pm.Poisson("H", mu=mu, observed=H, dims=("precinct", "party", "position"))
        elif cfg.likelihood == "negbin":
            alpha = pm.Gamma("alpha", mu=cfg.negbin_alpha_mu, sigma=cfg.negbin_alpha_mu)
            pm.NegativeBinomial("H", mu=mu, alpha=alpha, observed=H, dims=("precinct", "party", "position"))
        else:
            raise ValueError(cfg.likelihood)
    return model


SAMPLE_DEFAULTS = dict(draws=1000, tune=1000, chains=4, cores=2, target_accept=0.9, progressbar=False)


def sample(model: pm.Model, seed: int = 20261010, **kwargs):
    """Spustí NUTS; vrací InferenceData (DataTree) včetně log-likelihood."""
    kw = {**SAMPLE_DEFAULTS, **kwargs}
    with model:
        idata = pm.sample(random_seed=seed, **kw)
        pm.compute_log_likelihood(idata, progressbar=False)
    return idata
