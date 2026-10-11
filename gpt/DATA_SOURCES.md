# Původ dat a podmínky dalšího použití

Primární volební data: Český statistický úřad (ČSÚ), komunální volby Řevnice, 9.–10. 10. 2026, obec 539643. Podkladem jsou uživatelské exporty v předaném archivu. [Oficiální výsledková aplikace](https://volby.gov.cz/app/kv2026/cs/20261009/results/!___2100_2110_539643).

- `data/raw/okrsky_2026_csu_exports.zip`: 32 původních CSV; nijak neupravováno.
- `data/processed/*.csv`: regenerované čištěné údaje a odvozené matematické meze; 480/120 řádků.
- Historické soubory a přehled zvolených jsou dodané podklady; neobsahují kompletní 2022 kandidátská data. `okrsky_2022.csv` popisuje dvě tehdejší jednotky, nikoli územní páry s 2026.
- Účast v okrscích uvedená v dodaných CSV pochází ze sekundárních zdrojů Novinky/Seznam Zprávy. Není používána pro inferenci počtu hlasovacích lístků. Rozpor u účasti 2026 v okrsku 1 není z těchto podkladů vyřešen.
- `baseline_*.csv`: předchozí uživatelský nebayesovský scénářový model. Není to zdroj naměřených individuálních křížků.
- `results/`, `figures/`, `interactive/`: vlastní analýza a odvozené údaje tohoto projektu. Posterior není oficiální statistika ČSÚ.

[ČSÚ: Podmínky pro využívání a další zveřejňování statistických údajů](https://csu.gov.cz/podminky_pro_vyuzivani_a_dalsi_zverejnovani_statistickych_udaju_csu), ověřeno 10. 10. 2026, uvádí licenci [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), uvedení podmínek licence a jasné označení úprav a odvozených údajů. Doporučená atribuce: „Zdroj původních volebních údajů: ČSÚ, volby.gov.cz, Řevnice 2026. Vlastní zpracování a modelové odhady; nejde o oficiální statistiku individuálních křížků.“

Podmínky původce nenahrazujeme vlastní licencí dat. Tento projekt nerozhoduje o případných právech třetích stran k jiným dodaným podkladům. Uživatelská mapka s neověřeným původem byla ze zveřejnitelné verze vynechána. Nebyly přebírány plné texty akademických článků.
