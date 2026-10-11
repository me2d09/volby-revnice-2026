# Řevnice 2026: individuální křížky a meze jejich rekonstrukce

Reprodukovatelný výzkumný projekt v češtině. Odděluje pozorované výsledky, matematicky jisté meze a modelové odhady. Obsahuje všech 120 kandidátů, skutečně spuštěné čtyřřetězcové MCMC, priorové varianty, simulační recovery, predikční validaci a offline interaktivní grafy.

**Začněte notebookem `revnice_2026_bayesian_analysis.ipynb` nebo otevřete `interactive/index.html` v prohlížeči.** Notebook má uložené statické výstupy pro GitHub. Interaktivní HTML mají Plotly zabudované v souboru; nepotřebují internet ani server. Procházení osob a filtr strany jsou v `interactive/candidate_detail.html` a `interactive/candidates.html`.

## Co je jisté už bez modelu

- 4 okrsky, 8 plných listin, 120 kandidátů, 23 939 kandidátských hlasů.
- Původní bodová minima: 1 493 při použití okrsků, 1 096 pouze z městských součtů.
- Nová silnější celková mez: **2 897 individuálních křížků**, při zohlednění 15 hlasů na každý účinný stranický lístek. Důkaz a konstrukční ověření jsou v metodice.
- U Terezie Červené je bodově zaručeno nejméně 88 osobních křížků. Skutečný počet z těchto součtů přímo neznáme.

Výstupy `results/` jsou **vlastní odvozená analýza**, nikoli statistika osobních křížků publikovaná ČSÚ. Model nepředstavuje úplný generátor společné distribuce reálných lístků. Omezení, nepřístupné zdroje a numerické diagnostiky jsou uvedeny otevřeně. Automatická složka i osobní složka jsou v posteriorových losech celočíselné a dávají přesně pozorované hlasy.

## Rychlé spuštění

Ověřeno na Pythonu 3.12.14, Linux x86-64. Doporučen Python 3.12; `requirements.txt` připíná přímé závislosti a numerický runtime; `requirements-lock.txt` zachycuje přímé i nepřímé závislosti (61 balíčků) ověřeného prostředí. Pro běžné prohlížení stačí uložený notebook nebo HTML.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/prepare_and_validate.py
python -m pytest -q
python scripts/execute_notebook.py
```

Pro úplně připnutou instalaci na Linuxu/Pythonu 3.12 lze místo `requirements.txt` použít `requirements-lock.txt`.

`execute_notebook.py` spustí celý notebook v novém Python procesu s čistým skutečným jádrem `ipykernel.inprocess.InProcessKernel` a uloží standardní zprávy a výstupy Jupyteru. Tento režim nepotřebuje sockety: v použitém prostředí byly TCP i IPC sockety blokované. Není to doplňování předpřipravených výstupů. Na běžném počítači lze volitelně použít `python scripts/execute_notebook.py --transport tcp`, které spouští samostatný kernel přes nbclient. Tato TCP varianta zde kvůli omezení prostředí nebyla dokončena. Přiložené MCMC se načítá jen tehdy, pokud souhlasí fingerprint dat, modelového kódu, seedů a nastavení běhu. Výpočty tabulek, ověření mezí, PPC, recovery vyhodnocení a grafy se při běhu skutečně provádějí. Není potřeba síť ani externí API.

Pro **nové provedení všech MCMC běhů**:

```bash
python scripts/run_analysis.py --force
python scripts/execute_notebook.py
```

Případná prodloužení diagnosticky problematických běhů se provádějí z deklarovaného nastavení `run_config.json`, které používají skript i notebook. Kompletní výpočet má desítky skutečných řetězců; počítejte s řádem desítek minut podle počítače. `results/mcmc_run_summary.csv` obsahuje přesně naměřené runtime. Výchozí paralelizace je čtyřřetězcová. `OPENBLAS_NUM_THREADS=1` a `OMP_NUM_THREADS=1` zabraňují přebytku numerických vláken.

Diagnostický souhrn uvádí `diagnostic_stride`: 1 znamená všechny iterace po zahřátí, 5 každou pátou. Distribuované vzorky používají krok 25, aby ZIP nebyl zbytečně velký. Diagnostiky byly spočteny před tímto zmenšením; nejde o zlepšování ESS pomocí thinning.

Volitelné ověření HTML v prohlížeči: `pip install -r requirements-qa.txt`, `playwright install chromium`, `python scripts/ui_smoke.py`. Výsledkem je záznam a snímky v `results/ui_*`. Playwright není nutný pro notebook ani samotné prohlížení HTML.

Pro živé úpravy je možné notebook otevřít v JupyterLab nebo VS Code s Python kernelem z tohoto prostředí. JupyterLab sám není podmínkou batch spuštění. Samostatný notebook potřebuje pro nové spuštění okolní soubory tohoto ZIP projektu; uložené výstupy lze číst i bez nich.

## Struktura

| Soubor / složka | Obsah |
|---|---|
| `revnice_2026_bayesian_analysis.ipynb` | Český hlavní notebook se spuštěnými výstupy |
| `methodology.md` | Rovnice, likelihood, priory, přesná normalizace omezení, důkazy, literatura |
| `findings.md` | Běžnou češtinou psané závěry s označením typu tvrzení |
| `requirements.txt`, `environment_record.json` | Připnuté závislosti a zaznamenané provedení |
| `run_config.json` | Autoritativní délky běhů a seedy |
| `src/model.py` | Celočíselný FFBS/Gibbs/Metropolis sampler a generátor |
| `src/bounds.py` | Silnější mez, přesný síťový test a konstrukce lístků |
| `src/experiments.py` | Řízení běhů a syntetické experimenty |
| `src/report.py`, `src/visuals.py` | Výsledná CSV, kontroly, PNG/SVG a HTML |
| `scripts/` | Příprava dat, spuštění modelů, sestavení a spuštění notebooku |
| `tests/` | Sampler proti úplnému výčtu, meze, platnost konstrukce |
| `data/raw/` | Původní exporty a historické podklady, původní benchmark |
| `data/processed/` | 480 okrskových a 120 městských řádků |
| `results/candidate_estimates.csv` | Všichni kandidáti, 50/90/95% CI, očištěný efekt, pořadí a robustnost |
| `results/candidate_precinct_estimates.csv` | Rozklad všech 480 kombinací |
| `results/party_estimates.csv`, `precinct_estimates.csv` | Stranické a okrskové souhrny |
| `results/diagnostics_*.csv`, `mcmc_run_summary.csv` | R-hat, ESS, MCSE, běhy a jejich případná selhání |
| `results/chains/` | Skutečné posteriorové vzorky a metadata/fingerprinty |
| `results/synthetic_*`, `ppc_*`, `prior_*`, `out_of_precinct_*` | Validace a citlivost |
| `figures/` | Statické PNG i SVG všech hlavních grafů |
| `interactive/` | Tři samostatně otevřitelné offline Plotly HTML |
| `context/` | Původní zadání a podklady, nikoli autoritativní nový výsledek |
| `DATA_SOURCES.md`, `manifest_sha256.json` | Původ dat, podmínky využití, kontrolní otisky |

CSV používají UTF-8 s BOM a `;`. Podíly s příponou `_pct` jsou v procentech; `personal_share_median`, pravděpodobnosti a `coverage_95` jsou v 0–1. `q025`/`q975` je 95% centrální posteriorový interval; `q05`/`q95` je 90%; `q25`/`q75` je 50%. `scenario_*` jsou rozdíly mezi samostatnými modely, nikoli další credible interval. `position_adjusted_effect_*` je relativní efekt **uvnitř** strany, se středem podle geometrického průměru. `r_hat`, ESS a gate v kandidátském CSV se vztahují k osobnímu počtu, nikoli automaticky ke všem modelovým parametrům.

## GitHub a licence

Repozitář je připraven pro `git init`, není nikam automaticky publikován. `.gitignore` vynechává prostředí, cache, pracovní logy a velké binární posteriorové soubory. Ty jsou v dodaném ZIP pro rychlé ověření; v otevřeném GitHubu je lze dát do release assets nebo regenerovat. HTML se v běžném pohledu GitHubu nemusí spustit: stáhněte je a otevřete lokálně; případné GitHub Pages jsou volitelné. Notebook vždy obsahuje statický fallback.

ČSÚ je původcem volebních dat. Podmínky a atribuce jsou v `DATA_SOURCES.md`. Modelové výstupy jsou odvozené a musí být tak označeny i při dalším použití. Uživatelská okrsková mapa s neověřenými právy není součástí tohoto repozitáře. Žádné volební lístky konkrétních osob nebyly k dispozici a žádné osobě nepřipisujeme individuální volební chování. Syntetické konstrukce nepopisují skutečné voliče.
