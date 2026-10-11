# Řevnice 2026 – bayesovský odhad individuálních křížků z okrskových výsledků

Výzkumná analýza komunálních voleb v Řevnicích (9.–10. 10. 2026): pro každého ze **120 kandidátů** (8 kandidátek × 15) odhadujeme, kolik jeho hlasů pochází z **individuálních křížků** a kolik z mechanického přidělení při zakřížkování celé kandidátky. Vstupem je **480 agregátů** (4 okrsky × 8 kandidátek × 15 kandidátů) z ČSÚ a počet platných lístků (1 679).

Hlavní výstup je česky psaný, spustitelný notebook **`revnice_2026_bayesian_analysis.ipynb`** (PyMC 6 + ArviZ 1), který obsahuje:

* ověření dat a pravidel sčítání (zákon č. 491/2001 Sb., metodika ČSÚ 2026) s citacemi;
* **rigorózní dolní meze** bez modelu – monotónní mez (1 096 z městských součtů, 1 493 po okrscích) a novou, silnější LP mez ze zákona zachování hlasů (**2 890 křížků**);
* **hierarchický generativní model** s explicitní mechanikou lístků (rozdělení počtu křížků na lístku se stranou, lístky bez strany, výhoda pozice, osobní popularita napříč okrsky, lokální odchylky, saturace „1 křížek na kandidáta a lístek“, zákon zachování hlasů);
* prior predictive checks, **simulační test se známou pravdou** (generátor jednotlivých lístků), MCMC diagnostiku (R̂, ESS, divergence, energie, trace), posterior predictive checks, citlivost na priory a likelihood, leave-one-precinct-out, srovnání s baseline modely;
* výsledky pro kandidáty, kandidátky a okrsky, změny 2022 → 2026 a **souhrn ≥ 10 zjištění** s označením *fakt / rigorózní mez / modelový odhad*.

> Posteriorní odhady **nejsou** změřené křížky ČSÚ. Jsou podmíněné modelem a priory; simulace ukazují, že pořadí kandidátů a osobní efekty jsou robustní, zatímco celkový počet křížků je identifikován slabě (a spíše podhodnocen). Notebook to na každém místě říká a nabízí dokazatelné meze.

## Hlavní výsledky (stručně; detaily a označení fakt / mez / model v notebooku, odd. 10)

* **Rigorózně (bez modelu):** individuálních křížků bylo nejméně **2 890** (12,1 % všech hlasů); samotní lídři kandidátek jich museli dostat nejméně 706. Terezie Červená (ŠANCE, 10. místo) nejméně 88 (17+21+28+22 po okrscích).
* **Model (hlavní varianta):** cca **6 900 identifikovatelných osobních křížků** (90 %: 5 600–8 200, tj. ~29 % hlasů); citlivostní varianty 4 900–7 800; v simulacích se celkový součet obnovil s chybou −23 % až +15 %, zatímco pořadí kandidátů a osobní efekty byly robustní (korelace odhadů s pravdou ≈ 0,98–0,99).
* Přibližně tři čtvrtiny lístků se zakřížkovanou stranou nemají žádný křížek jinde; lístků bez strany model odhaduje ~460 (28 %) s průměrem ~12 křížků – slabě identifikováno (záleží na předpokladu o ocasu rozdělení K).
* **Osobnosti** (největší osobní efekt po očištění o pozici, stranu a okrsek): T. Červená, O. Masner, M. Cvanciger, B. Ciglerová, I. Junková, J. Lojda, P. Hartmann (TOP 09), Š. Martinec. Lídři nejsou automaticky osobnosti (Smrčka, Chabera, Schlindenbuch pod očekáváním).
* ODS chybělo **15 hlasů = jeden stranický lístek** k 5% klauzuli; Renata Dudová (DOBŘE) měla více hlasů než zvolený Bobek, ale o 3 hlasy minula pravidlo 10 %.

## Rychlé spuštění

```bash
python -m venv .venv && source .venv/bin/activate     # volitelné
pip install -r requirements.txt                        # připnuté verze (Python 3.13)
python scripts/prepare_and_validate.py                 # kontrola dat (bez závislostí)
jupyter lab revnice_2026_bayesian_analysis.ipynb       # Run All
```

* Plný běh notebooku (všechny MCMC fity: hlavní model, baseline, 3 simulační scénáře, 11 citlivostních variant, 4 LOPO fity; 4 řetězce NUTS) trvá na 2 jádrech **cca 1,5–2 hodiny**. Nic nevyžaduje síť ani externí API.
* `make fits` spustí stejné fity dávkově do `fits/` (NetCDF); notebook je pak s `REVNICE_USE_CACHE=1` (výchozí) jen načte a doběhne za pár minut. `REVNICE_USE_CACHE=0` vše přepočítá; `REVNICE_FAST=1` zkrátí řetězce (orientační výsledky, ~15 minut).
* `make notebook` spustí notebook od začátku do konce přes `nbconvert` (čistý kernel), `make notebook-fresh` totéž bez cache.
* Notebook je sestaven skriptem `scripts/build_notebook.py` (zdroj textu i kódu notebooku, verzovatelný).

## Struktura projektu

```text
revnice_2026_bayesian_analysis.ipynb   hlavní notebook (česky, spuštěný, se statickými grafy)
methodology.md                         mechanika, model, identifikovatelnost, testy, bibliografie
README.md · requirements.txt · Makefile · .gitignore
src/revnice/
  data.py        načtení dat, rigorózní meze (monotonie, LP se zákonem zachování)
  model.py       PyMC model (PriorConfig + build_model), varianty likelihoodu
  simulate.py    generátor jednotlivých hlasovacích lístků podle pravidel (recovery test)
  posterior.py   realizované křížky C | H, tabulky kandidátů/stran/okrsků, diagnostika
  analysis.py    prior predictive, PPC, recovery, citlivost, leave-one-precinct-out
  plots.py       statické grafy (matplotlib) a interaktivní grafy (Plotly)
scripts/
  prepare_and_validate.py   regenerace a 100% kontrola součtů (jen stdlib)
  run_all_fits.py           dávkové spuštění všech fitů do fits/ a results/
  build_notebook.py         sestavení .ipynb
data/raw/                   původní exporty ČSÚ (32 CSV v zipu) a historické podklady 2022
data/processed/             480 okrskových a 120 městských řádků (UTF-8 BOM, oddělovač ;)
context/                    metodické poznámky zadání a předchozí NEbayesovský scénářový model (jen benchmark)
results/                    CSV/JSON výstupy (viz níže)
figures/                    statické PNG grafy (zobrazují se i na GitHubu)
interactive/                samostatné Plotly HTML grafy (otevřít v prohlížeči; sdílená plotly.min.js)
fits/                       uložené MCMC fity (NetCDF; v gitu ignorováno, regeneruje se)
```

## Data

* `data/processed/precinct_candidates_2026.csv` – 480 řádků: `year;precinct;party_id;party;position;name;age;votes;pct_of_party_precinct;source_file;rigorous_min_personal_marks`.
* `data/processed/city_candidates_2026.csv` – 120 řádků s `elected_2026`, `elected_order`, `rigorous_min_personal_marks_city`, `rigorous_min_personal_marks_sum_precincts`.
* `data/raw/strany_2022_2026.csv`, `okrsky_2022.csv` (pozor: v roce 2022 jen 2 okrsky – jiné území), `okrsky_2026_party.csv`, `zvoleni_2026_a_srovnani_2022.csv`.
* Počet platných lístků (1 679), zapsaných voličů (2 819) a vydaných obálek (1 690) pochází z ČSÚ open dat (`vysledky_obec_539643.xml`, 10. 10. 2026 19:12) a je zapsán přímo v notebooku (`V_CITY`). Počty lístků **po okrscích** v balíčku nejsou – jejich doplnění by model nejvíce zpřesnilo (viz methodology.md).

Zdroj volebních údajů: **ČSÚ / volby.gov.cz** (uživatelské CSV exporty). Před veřejným zveřejněním ověřte podmínky opětovného užití dat ČSÚ a uveďte původ. Uživatelská mapka okrsků z předávacího balíčku do repozitáře **zařazena není** (neověřená licence).

## Výstupy v `results/`

| soubor | obsah |
|---|---|
| `candidate_estimates.csv` | 120 kandidátů: strana, pozice, hlasy (město + 4 okrsky), rigorózní minimum (město / součet okrsků), posteriorní medián realizovaných křížků, 50/90/95% intervaly, podíl křížků, očekávaná intenzita μ^C, osobní efekt u (po očištění o pozici) s intervalem a P(u>0), posteriorní pořadí (medián, 90 %), robustnost pořadí, srovnání s benchmarkem |
| `party_estimates.csv` | 8 kandidátek: křížky, podíl, stranické lístky, P(K=0), E[K] |
| `precinct_estimates.csv` | 4 okrsky: křížky, stranické lístky, křížky z lístků bez strany, LP mez |
| `rigorous_bounds_candidates.csv`, `rigorous_bounds_precincts.csv` | dokazatelné meze |
| `mcmc_summary_main.csv`, `mcmc_diagnostics_main.csv` | R̂, ESS, divergence, runtime |
| `ppc_residuals.csv` | posterior predictive rezidua všech 480 pozorování |
| `recovery_*.csv` | simulační test: pravda vs. odhad |
| `sensitivity.csv` | citlivost na priory / likelihood |
| `lopo.csv` | leave-one-precinct-out |
| `model_comparison_loo.csv` | PSIS-LOO hlavní model vs. baseline |
| `souhrn_zjisteni.md` | souhrn zjištění (generovaný z výsledků) |
| `prior_config_main.json`, `run_info.json` | priory, verze, seedy, runtime |

## Grafy

Statické PNG ve `figures/` (strany a mandáty, heatmapa okrsků, profily kandidátů, posteriorní žebříček, osobní efekt, rozklad strana/osobní, příspěvky okrsků, citlivost, MCMC diagnostika, PPC, změny 2022→2026, recovery, K-rozdělení a efekt pozice, prior predictive, LOPO, srovnání s benchmarkem). Interaktivní Plotly grafy v `interactive/` (hover, filtr strany, procházení kandidátů): otevřete `.html` v prohlížeči – soubory odkazují na `interactive/plotly.min.js`, takže je nutné zachovat celou složku; GitHub JavaScript v `.ipynb` nevykresluje, proto jsou v notebooku uloženy i statické verze. Pro web lze složku `interactive/` publikovat přes GitHub Pages.

## Předchozí model

`context/predchozi_scenarovy_model_POUZE_BASELINE/` obsahuje starší nebayesovský 45scénářový model (medián 6 884 křížků). Není to ground truth ani posterior; v notebooku slouží jen ke srovnání.
