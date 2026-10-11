# Metodika: bayesovský rozklad kandidátských hlasů na stranickou a osobní složku (Řevnice 2026)

Tento dokument popisuje přesnou mechaniku, model, identifikovatelnost, testy a omezení analýzy v notebooku `revnice_2026_bayesian_analysis.ipynb`. Výsledná čísla jsou v `results/` a v notebooku; zde je **jak** vznikla.

## 1. Mechanika hlasování (zákon č. 491/2001 Sb., § 34, § 40–41; metodika ČSÚ 2026)

Volič do 15členného zastupitelstva může označit (a) jednu kandidátku, (b) nejvýše 15 jednotlivých kandidátů, nebo (c) jednu kandidátku a kandidáty *jiných* kandidátek. Sčítání (ČSÚ, *Vyhodnocení hlasů*, 2026):

* (a) „hlasy získávají kandidáti označené volební strany v pořadí podle hlasovacího lístku“ – všech 15 kandidátů po jednom hlasu;
* (b) každý označený kandidát jeden hlas; nevyužité hlasy komise „nikomu dalšímu nepřiděluje“;
* (c) „hlasy získávají nejprve označení kandidáti jiných volebních stran než označené strany“, zbývajících $15-k$ hlasů dostanou kandidáti označené strany „podle pořadí na hlasovacím lístku“; „u označené volební strany se již nepřihlíží k označeným kandidátům této volební strany“;
* neplatný je lístek s více stranami nebo s více než 15 označenými kandidáty.

Důsledky: (i) stranicky přidělené hlasy $S_{p,s,i}$ jsou **nerostoucí** v pořadí $i$; (ii) lístek typu (a) i (c) vytvoří **přesně 15** kandidátských hlasů, lístek typu (b) nejvýše 15; (iii) lístek „strana + 15 jiných“ je v agregátu totožný s lístkem bez strany – používáme konvenci $K\in\{0,\dots,14\}$ pro *efektivně* označené strany.

## 2. Notace a rigorózní meze

$p\in\{1..4\}$ okrsek, $s\in\{1..8\}$ kandidátka, $i\in\{1..15\}$ pořadí. $H_{p,s,i}$ = hlasy kandidáta (ČSÚ), $H^{\rm tot}_p=\sum_{s,i}H_{p,s,i}$, $V$ = platné lístky v obci (1 679).

$$H_{p,s,i}=S_{p,s,i}+C_{p,s,i},\quad S_{p,s,1}\ge\dots\ge S_{p,s,15}\ge 0,\quad C\ge 0 .$$

**Mez 1 (monotonie, po kandidátech):** $C_{p,s,i}\ge\max(0,H_{p,s,i}-\min_{j\le i}H_{p,s,j})$. Součet: 1 096 (městské součty) resp. 1 493 (po okrscích). Terezie Červená 83 → 88.

**Mez 2 (zákon zachování, LP):** $B_{p,s}=S_{p,s,1}$ je počet efektivních stranických lístků a každý vytvoří 15 hlasů, lístky bez strany nejvýše 15, tedy $\sum_s B_{p,s}\le H^{\rm tot}_p/15$. Minimum $\sum_{s,i}C_{p,s,i}$ za podmínek monotonie, $S\le H$ a této nerovnosti je lineární program (řešen `scipy.optimize.linprog`, HiGHS). Výsledek: **2 890** křížků (12,1 % hlasů) jako součet přes okrsky (zaokrouhleno nahoru; po okrscích 646, 776, 708, 761), resp. 2 529 z městských součtů. Mez je relaxovaná (LP připouští neceločíselná $S$), tedy platná. Pro jednotlivé kandidáty se vazba neprojeví; pro součty podle pořadí dává $\sum_s C_{p,s,i}\ge\sum_s H_{p,s,i}-H^{\rm tot}_p/15$ (lídři: 148, 216, 162, 180 → 706 celkem).

**Nevyužité hlasy:** $15V-\sum_pH^{\rm tot}_p=25\,185-23\,939=1\,246$ vzniká výhradně na lístcích bez strany; je-li $\bar m$ jejich průměrný počet křížků, je jich $M=1246/(15-\bar m)$ a nesou $R=\bar mM$ křížků.

## 3. Generativní model

### 3.1 Stranická složka
$\pi_{s,k}=P(K=k)$, $k=0..14$, hierarchicky: $\boldsymbol\pi_s=\mathrm{softmax}(\boldsymbol\eta_0+\sigma_\eta\mathbf z_s)$, $\eta_{0,k}\sim\mathcal N(\log w_k,1)$ s $w_0=0{,}5$ a geometrickým ocasem (poměr 0,7, **bez useknutí**), $\sigma_\eta\sim\mathrm{HN}(0{,}5)$, $\mathbf z_s\sim\mathcal N(0,I)$.
$q_{s,i}=P(K\le 15-i)$, $S_{p,s,i}=B_{p,s}\,q_{s,i}$.

### 3.2 Rozklad lístků se zákonem zachování
$\bar m=1+(\bar m_{\max}-1)\,\xi$, $\xi\sim\mathrm{Beta}(2,2)$, $\bar m_{\max}=\sum_pH^{\rm tot}_p/V=14{,}26$ (průměr křížků na lístku bez strany nemůže přesáhnout průměr hlasů na lístek). $M=(15V-\sum_pH^{\rm tot}_p)/(15-\bar m)$, $R=\bar mM$, $R_p=R\,r_p$ s $\mathbf r\sim\mathrm{Dir}(2,2,2,2)$ (omezení $R_p\le H^{\rm tot}_p$), $\sum_sB_{p,s}=(H^{\rm tot}_p-R_p)/15$, $B_{p,\cdot}$ rozděleno $\mathbf g_p\sim\mathrm{Dir}(1,\dots,1)$. Celkem tedy $\sum_{p,s}B_{p,s}=V-M$.

### 3.3 Osobní složka – alokace křížků
Váhy $w_{p,s,i}\propto\exp(a_s+e_{p,s}+\theta_i+u_{s,i}+v_{p,s,i})$, normalizované přes 120 kandidátů v okrsku:
* $a_s\sim\mathcal N(0,\sigma_a)$, $\sigma_a\sim\mathrm{HN}(1)$ – osobní přitažlivost kandidátky;
* $e_{p,s}\sim\mathcal N(0,\sigma_e)$, $\sigma_e\sim\mathrm{HN}(0{,}5)$ – její okrsková odchylka;
* $\theta_i=-\beta\log i+\psi_i$, $\beta\sim\mathcal N(0{,}7;\,0{,}5)$, $\psi_1=0$, $\psi_i\sim\mathcal N(0,\sigma_\psi)$, $\sigma_\psi\sim\mathrm{HN}(0{,}25)$ – výhoda pozice **pro křížky** (oddělená od mechanického $q$);
* $u_{s,i}\sim\mathcal N(0,\sigma_u)$, $\sigma_u\sim\mathrm{HN}(0{,}75)$ – osobní popularita sdílená všemi okrsky;
* $v_{p,s,i}\sim\mathcal N(0,\sigma_v)$, $\sigma_v\sim\mathrm{HN}(0{,}3)$ – lokální popularita.

Křížky voličů strany $s'$ jdou jen mimo $s'$ (váhy $\tilde w=w/(1-W_{s'})$, $W_{s'}=\sum_iw_{p,s',i}$). **Saturace:** kandidát může z jednoho lístku dostat nejvýše jeden hlas, volič s $m$ křížky vybírá $m$ různých kandidátů; pravděpodobnost výběru aproximujeme poissonizací $p_c=1-\exp(-m\lambda w_c)$, $\lambda$ z podmínky $\sum_cp_c=m$ (lístky bez strany: 4 kroky pevného bodu; lístky se stranou a $k\le14$: $\lambda\approx1+\tfrac k2\sum_c\tilde w_c^2$). Očekávané křížky

$$\mu^C_{p,(s,i)}=M_p\,p^{\rm pure}_{p,(s,i)}+\sum_{s'\ne s}B_{p,s'}\sum_{k=1}^{14}\pi_{s',k}\,p^{(k)}_{p,s',(s,i)},\qquad M_p=R_p/\bar m .$$

Zachování: $\sum_{s,i}(S_{p,s,i}+\mu^C_{p,s,i})=H^{\rm tot}_p$ (až na aproximaci saturace).

### 3.4 Likelihood
$S_{p,s,i}$ je součet multinomiálních počtů, $\mathrm{Var}=B_{p,s}q_{s,i}(1-q_{s,i})$; $C$ je součet Bernoulliho pokusů, $\mathrm{Var}\approx\mu^C$:

$$H_{p,s,i}\sim\mathcal N\!\bigl(S+\mu^C,\;Bq(1-q)+\mu^C+(\varphi\mu)^2+0{,}5\bigr),\qquad\varphi\sim\mathrm{HN}(0{,}05).$$

Implementované alternativy: Poisson; vícerozměrná normální s přesnou kovariancí $\mathrm{Cov}(S_i,S_j)=B\,q_{\max(i,j)}(1-q_{\min(i,j)})$ uvnitř bloku; negativně binomická.

### 3.5 Realizované počty křížků
Posteriorní tahy dávají intenzity. Realizovaný počet křížků podmíněný pozorováním: $C\mid H\sim\mathcal N\bigl(\mu^C+\tfrac{\sigma_C^2}{\sigma_S^2+\sigma_C^2}(H-\mu),\;\tfrac{\sigma_C^2\sigma_S^2}{\sigma_S^2+\sigma_C^2}\bigr)$, zaokrouhleno a oříznuto na $[\text{mez 1},H]$ (mez je dokazatelná informace, kterou nezávislá aproximace ztrácí). Městské hodnoty jsou součty přes okrsky v každém tahu, pořadí kandidátů se počítá v každém tahu.

### 3.6 Co je aproximace
Očekávané hodnoty místo vzorkování lístků; poissonizace výběru bez vracení; společné $\bar m$ a $\pi_s$ pro všechny okrsky; nezávislost reziduí mezi pozicemi (MvNormal varianta ji uvolňuje); neznámé $V_p$ po okrscích (model má vstup `n_valid_ballots`; s okrskovými $V_p$ by šlo $M_p$ svázat přímo).

## 4. Identifikovatelnost

Uvnitř bloku $H_i=Bq_i+\lambda c_i$: $q$ je plochý vpředu a klesá na konci (ocas $K$), $c$ klesá od začátku (výhoda pozice) a $u_{s,i}$ je sdílené napříč okrsky. **Neidentifikovatelný směr:** osobní křížky rozprostřené rovnoměrně po kandidátce jsou v agregátu totožné se stranickými lístky (volič, který zakřížkuje 15 lidí jedné strany ≡ volič strany). Zákon zachování + $V$ vážou tento směr na $\bar m$, které je samo slabě identifikované. Proto:

* **robustní:** pořadí kandidátů podle křížků, osobní efekty $u$, $P(K=0)$, řádově $\beta$;
* **slabě identifikované:** celkový počet křížků, $M$, $\bar m$, $R$ – posterior je tažen priorem $\bar m$ a hierarchickými priory;
* **simulační test** (`revnice.simulate`: generování jednotlivých lístků podle skutečných pravidel, tři scénáře) ukazuje korelaci odhadů $C$ s pravdou ≈ 0,98, obnovu špičky žebříčku, ale systematické **podhodnocení celkového počtu křížků o cca 10–20 %** a pokrytí 90% intervalů cca 75–90 %. Posteriorní součty proto interpretujeme jako odhad *identifikovatelné* části s dokazatelnou dolní mezí (LP).

## 5. Testy a diagnostika
1. Prior predictive (profily, poměr 15./1. místa).
2. Simulace známé pravdy (A: málo křížků, B: hodně křížků, D: strany se liší).
3. NUTS, 4 řetězce × 1 000 tahů (+1 000 tuning), `target_accept=0.9`; R̂, ESS (bulk/tail), divergence, energie, trace ploty; vše v `results/mcmc_*`.
4. Posterior predictive checks po pořadí, stranách, okrscích, 32 blocích; standardizovaná rezidua (`results/ppc_residuals.csv`).
5. Citlivost na priory: $P(K=0)$ 0,3/0,7; ocas 0,5/0,85; $\bar m$ rovnoměrný/vysoký; $\beta\sim\mathcal N(0,1)$; $\sigma_u$ úzký/široký; Poisson; bez saturace (`results/sensitivity.csv`).
6. Baseline bez osobních efektů (PSIS-LOO, log-likelihood, MAE); srovnání s předchozím 45scénářovým modelem (pouze benchmark).
7. Leave-one-precinct-out (n = 4; ilustrace): predikce profilu 120 kandidátů ve vynechaném okrsku při známých součtech stran.

## 6. Rozlišení typů nejistoty
| typ | co znamená | kde |
|---|---|---|
| rigorózní dolní mez | plyne jen z pravidel sčítání | odd. 2, `results/rigorous_bounds_*.csv` |
| posteriorní credible interval | nejistota parametrů/realizací podmíněná modelem a priory | `results/candidate_estimates.csv` aj. |
| scénářové rozpětí | rozsah mediánů napříč prior/likelihood variantami | `results/sensitivity.csv` |
| predikční interval (PPC) | replikace dat z modelu | `results/ppc_residuals.csv` |
| benchmark | předchozí nebayesovský model, 45 scénářů | `context/predchozi_scenarovy_model_POUZE_BASELINE/` |

## 7. Bibliografie
* Zákon č. 491/2001 Sb., o volbách do zastupitelstev obcí, § 34, § 40–41, § 45 (plné znění se v analytickém prostředí nepodařilo stáhnout; paragrafy cituje metodika ČSÚ níže).
* Portál veřejné správy: *Volby do zastupitelstev obcí*, https://portal.gov.cz/rozcestniky/RZC-118.
* Český statistický úřad: *Volby do zastupitelstev obcí – Vyhodnocení hlasů* (2026), https://volby.gov.cz/prg/zo26_priklady_vyhodnoceni_hl_pro_tisk.pdf.
* ČSÚ open data kv2026: `https://volby.gov.cz/appdata/kv2026/20261009/odata/zastup/vysledky_obec_539643.xml` (ZAPSANI_VOLICI 2819, VYDANE_OBALKY 1690, ODEVZDANE_OBALKY 1689, PLATNE_LISTKY 1679, PLATNE_HLASY 23939; generováno 2026-10-10 19:12).
* Tam Cho, W. K., Gaines, B. J. (2004). The Limits of Ecological Inference: The Case of Split-Ticket Voting. *American Journal of Political Science* 48(1), 152–171. https://doi.org/10.1111/j.0092-5853.2004.00062.x
* Park, W.-h., Hanmer, M. J., Biggers, D. R. (2014). Ecological inference under unfavorable conditions: Straight and split-ticket voting in diverse settings and small samples. *Electoral Studies* 36, 192–203. https://doi.org/10.1016/j.electstud.2014.08.006
* Kaňok, D. *Analýza preferenčního hlasování ve volbách do zastupitelstev obcí v letech 2006–2018*. https://theses.cz/id/id9d17/ (nepodařilo se ověřit obsah).
* Gelman, A. et al. (2020). Bayesian Workflow. arXiv:2011.01808.
* Gabry, J. et al. (2019). Visualization in Bayesian workflow. *JRSS A* 182(2), 389–402. https://doi.org/10.1111/rssa.12378
* Vehtari, A. et al. (2021). Rank-normalization, folding, and localization: An improved R̂ for assessing convergence of MCMC. *Bayesian Analysis* 16(2), 667–718. https://doi.org/10.1214/20-BA1221
* Talts, S. et al. (2018). Validating Bayesian inference algorithms with simulation-based calibration. arXiv:1804.06788.
* Abril-Pla, O. et al. (2023). PyMC: a modern, and comprehensive probabilistic programming framework in Python. *PeerJ Computer Science* 9:e1516. https://doi.org/10.7717/peerj-cs.1516
* Kumar, R. et al. (2019). ArviZ a unified library for exploratory analysis of Bayesian models in Python. *JOSS* 4(33), 1143. https://doi.org/10.21105/joss.01143
