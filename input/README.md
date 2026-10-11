# Řevnice 2026 — předávací balíček pro bayesovskou analýzu křížkování

**Datum přípravy:** 10. 10. 2026  
**Cíl:** dodat ChatGPT Work i Claude totožná data a totožné zadání k vytvoření vědecky korektního, reprodukovatelného Jupyter notebooku (`.ipynb`) pro GitHub. **Notebook v tomto balíčku zatím není** — jeho vytvoření je předmětem zadání oběma modelům.

## Začít zde

1. Přečti [`PROMPT_ZKOPIROVAT.md`](PROMPT_ZKOPIROVAT.md) — to je úplné a pro oba systémy stejné zadání.
2. Přečti [`context/METODIKA_A_IDENTIFIKOVATELNOST.md`](context/METODIKA_A_IDENTIFIKOVATELNOST.md) a [`context/CO_UZ_VIME.md`](context/CO_UZ_VIME.md).
3. Hlavní vstupy jsou **480 pozorování** v [`data/processed/precinct_candidates_2026.csv`](data/processed/precinct_candidates_2026.csv) a **120 kandidátů** v [`data/processed/city_candidates_2026.csv`](data/processed/city_candidates_2026.csv).
4. Původních 32 CSV je beze změny v [`data/raw/okrsky_2026_csu_exports.zip`](data/raw/okrsky_2026_csu_exports.zip); lze vše přepočítat skriptem `python scripts/prepare_and_validate.py` (bez závislostí).
5. Pro porovnání 2022–2026 použij [`data/raw/strany_2022_2026.csv`](data/raw/strany_2022_2026.csv) a další historické podklady ve složce `data/raw/`.

## Kontrolní součty — výsledek ověřeného skriptu

- 4 okrsky × 8 kandidátek × 15 kandidátů = **480 řádků**.
- Městské kandidátské výsledky: **120 osob**, **23 939 hlasů**.
- Okrsky postupně: **5 778, 6 012, 5 818, 6 331** hlasů.
- Kandidátky podle čísel: `1 ŠANCE`, `2 TOP 09`, `3 DOBŘE`, `4 Srdce`, `5 PRO`, `6 ODS`, `7 Perspektiva`, `8 Naše Řevnice`.
- Součet čtyř okrsků pro **každého kandidáta** přesně souhlasí s městským exportem.
- Totéž platí pro hlasy každé kandidátky v každém okrsku.
- Model-free dolní mez individuálních křížků: **1 096**, pokud jsou použity jen městské součty, a **1 493** při samostatné aplikaci po okrscích. U Terezie Červené **83 → 88**. To **nejsou** odhady skutečného počtu individuálních hlasů.

## Co je obsahem

```text
PROMPT_ZKOPIROVAT.md              společné zadání pro Work i Claude
README.md                         tento rozcestník
context/
  CO_UZ_VIME.md                   dosavadní závěry včetně oprav metodiky
  METODIKA_A_IDENTIFIKOVATELNOST.md přesná mechanika hlasování, rovnice, meze a doporučení
  LITERATURA_A_ZDROJE.md          základní ověřitelné odkazy
  predchozi_scenarovy_model_POUZE_BASELINE.zip  starý, NEbayesovský model pro porovnání (NEbrat jako ground truth)
data/raw/
  okrsky_2026_csu_exports.zip     32 CSV ve složkách 1/ .. 4/
  okrsky_reference_map.png        uživatelská mapka okrsků (není georeferencovaná)
  candidates_2026_city_original_analysis.csv
  okrsky_2026_party.csv           kontrolní stranické součty za 4 okrsky
  okrsky_2022.csv                 pozor: tehdy byly jen 2 okrsky
  strany_2022_2026.csv
  zvoleni_2026_a_srovnani_2022.csv
data/processed/
  precinct_candidates_2026.csv    480 očištěných řádků
  city_candidates_2026.csv        120 osob a ověřené dolní meze
  validation_summary.json
scripts/
  prepare_and_validate.py        spustitelná regenerace a 100% kontrola součtů
```

## Formát zpracovaných CSV

CSV je UTF-8 s BOM, oddělovač `;` (snazší použití v českém Excelu). V `precinct_candidates_2026.csv` jsou sloupce `year`, `precinct`, `party_id`, `party`, `position`, `name`, `age`, `votes`, `pct_of_party_precinct`, `source_file`, `rigorous_min_personal_marks`. V `city_candidates_2026.csv`: `year`, `party_id`, `party`, `position`, `name`, `age`, `votes`, `elected_2026`, `elected_order`, `rigorous_min_personal_marks_city`, `rigorous_min_personal_marks_sum_precincts`.

**Pozor:** `rigorous_min_personal_marks` není počet křížků, jen dolní matematická mez. Získání 480 agregátů neznamená získání anonymních lístků.

## Citlivost závěrů

Starší scénářový model s 45 kombinacemi předpokladů vytvořil číslo „6 884 osobních křížků“ (28,8 %); jde o **medián arbitrárních citlivostních scénářů, nikoli bayesovský posterior ani pozorovanou statistiku**. Nový model se musí vyvinout nezávisle; uvedená hodnota nesmí být cílem fitování ani datově pojatým priorem.

## Licence / provenience

Zdroj volebních údajů: **ČSÚ / volby.gov.cz**, uživatelské CSV exporty. Autor zpracování dat nemůže za ČSÚ udělovat licenci, proto před zveřejněním na GitHubu ověř podmínky opětovného užití zdrojů a uveď jejich původ. Okrsková referenční mapka byla dodána uživatelem; práva k jejímu veřejnému šíření nejsou ověřena — je označena jako volitelná a neměla by se bez další kontroly publikovat v otevřeném repozitáři.
