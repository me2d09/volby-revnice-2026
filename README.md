# Volby Řevnice 2026

Neoficiální, interaktivní analýza komunálních voleb v Řevnicích (9.–10. 10. 2026) – web pro GitHub Pages.

Analýzy vytvořily jazykové modely **Claude** (Anthropic) a **GPT** (OpenAI), zadání a prompty připravil **Petr Čermák**.
Zdroj dat: ČSÚ / volby.cz.

## Co je na webu

| stránka | obsah |
|---|---|
| `index.html` – Úvod | rychlá čísla, zastupitelstvo (zasedací pořádek do U), výsledky kandidátek, **jen výsledky potvrzené oběma analýzami** |
| `vysledky.html` – Výsledky v kostce | interaktivní verze infografiky: kandidátky, změna proti 2022, okrsky (schéma + „co kdyby“), zvolení, kandidáti a přednostní hlasy, osobní změny, těsné momenty, d’Hondt, mandátová kalkulačka, infografika ke stažení |
| `souhrn.html` – Souhrn analýz | co potvrdily obě analýzy, srovnání kandidát po kandidátovi, kde a proč se liší, hodnocení Claude × GPT, společný žebříček |
| `krizky.html` – Analýza Claude | výcuc analýzy Claude (simulátor lístku, meze, přínos kandidátů pro stranu, žebříček, osobnosti, kandidátky a okrsky, vyhledání kandidáta, citlivost) |
| `gpt.html` – Analýza GPT | totéž pro analýzu GPT |
| `notebooky.html` – Pro fajnšmekry | oba notebooky v prohlížeči (s funkčními interaktivními grafy), data, reprodukce, slovníček |

Stránky `krizky.html` a `gpt.html` mají stejnou strukturu a vykresluje je společný `docs/assets/js/analyza.js`
(analýzu určuje `<body data-analysis="claude|gpt">`). Při úpravě šablony je potřeba upravit oba soubory.

Všechny grafy jsou v Plotly (plotly.js 4.1.1 přibalený v `docs/vendor/`), web funguje ve světlém i tmavém režimu a na mobilu.

## Struktura repozitáře

```text
input/      společná vstupní data a zadání pro oba modely (beze změn)
claude/     analýza Claude – notebook, zdrojáky, výsledky (web ji jen čte)
gpt/        analýza GPT – notebook, zdrojáky, výsledky (web ji jen čte)
basic/      jednoduché statistiky bez modelu: prepare_basic.py → zakladni_data.json + CSV
scripts/    build_site.py – sestaví data, srovnání a notebooky pro web
            derived/ – 90% intervaly součtů GPT spočtené z posteriorových vzorků (vzorky jsou v .gitignore)
docs/       hotový statický web (GitHub Pages)
  assets/     CSS, JS stránek, infografika
  data/       data pro web (JSON ke stažení + JS pro načtení i z file://)
  notebooky/  notebooky převedené do HTML + originální .ipynb ke stažení
  vendor/     plotly.js
infografika-v1.png   infografika (GPT)
```

## Sestavení

```bash
python basic/prepare_basic.py      # jen základní statistiky (stdlib)
python scripts/build_site.py       # vše pro web: data, notebooky → HTML, infografika
python scripts/build_site.py --skip-notebooks   # rychlé přegenerování dat
```

`build_site.py` potřebuje `nbformat` a `nbconvert` (jen pro převod notebooků). Náhled lokálně: otevřete `docs/index.html`
v prohlížeči, nebo `python -m http.server -d docs`.

## Zveřejnění na GitHub Pages

Settings → Pages → *Build and deployment*: **Deploy from a branch**, branch `main`, složka **`/docs`**.
Web pak poběží na `https://me2d09.github.io/volby-revnice-2026/`.

## Jak se obě analýzy porovnávají

`build_site.py` převede výsledky obou analýz na společný formát (`docs/data/claude.json`, `gpt.json`): medián osobních
křížků, **90% intervaly** (u GPT dopočtené z posteriorových vzorků) a osobní efekt jako násobek. `docs/data/srovnani.json`
obsahuje srovnání kandidát po kandidátovi, shody a nezávislé ověření dolní meze: přesné celočíselné minimum je
**2 897** (GPT), spojitá relaxace dává 2 889,3 (Claude uvádí 2 890). Ověření je ve funkci `exact_budget_bound()`.

## Upozornění

Modelové odhady nejsou změřená data – na webu jsou vždy odlišené značkami *fakt*, *jisté minimum* a *model*.
Schéma okrsků na webu je zjednodušené a není přesnou mapou.
