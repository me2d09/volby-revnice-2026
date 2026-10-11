# Volby Řevnice 2026

Neoficiální, interaktivní analýza komunálních voleb v Řevnicích (9.–10. 10. 2026) – web pro GitHub Pages.

Analýzy vytvořily jazykové modely **Claude** (Anthropic) a **GPT** (OpenAI), zadání a prompty připravil **Petr Čermák**.
Zdroj dat: ČSÚ / volby.cz.

## Co je na webu

| stránka | obsah |
|---|---|
| `index.html` – Úvod | rychlá čísla, rozdělení mandátů, výsledky kandidátek 2026/2022, rozcestník |
| `vysledky.html` – Výsledky v kostce | interaktivní verze infografiky: kandidátky, změna proti 2022, okrsky (schéma + „co kdyby“), zvolení, kandidáti a přednostní hlasy, osobní změny, těsné momenty, d’Hondt, mandátová kalkulačka, infografika ke stažení |
| `krizky.html` – Osobní křížky | výcuc bayesovské analýzy Claude: simulátor lístku, dokazatelné meze, přínos kandidátů pro stranu, žebříček, osobnosti, kandidátky a okrsky, vyhledání kandidáta, citlivost a simulační test |
| `gpt.html` – Analýza GPT | připravujeme |
| `souhrn.html` – Souhrn | už teď jisté závěry; srovnání Claude × GPT připravujeme |
| `notebooky.html` – Pro fajnšmekry | notebooky v prohlížeči (s funkčními Plotly grafy), data, reprodukce, slovníček |

Všechny grafy jsou v Plotly (plotly.js 4.1.1 přibalený v `docs/vendor/`), web funguje ve světlém i tmavém režimu a na mobilu.

## Struktura repozitáře

```text
input/      společná vstupní data a zadání pro oba modely (beze změn)
claude/     analýza Claude – notebook, zdrojáky, výsledky (web ji jen čte)
basic/      jednoduché statistiky bez modelu: prepare_basic.py → zakladni_data.json + CSV
scripts/    build_site.py – sestaví data a notebooky pro web
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

## Jak doplnit analýzu GPT

1. Výstup GPT uložte do složky `gpt/` (notebook + tabulky výsledků).
2. V `scripts/build_site.py` doplňte cestu k notebooku v `ANALYSES["gpt"]` – notebook se převede do `docs/notebooky/gpt.html`
   (Plotly výstupy se převádějí automaticky).
3. Přidejte funkci obdobnou `build_claude()`, která z výsledků GPT vytáhne data do `docs/data/gpt.json`.
4. Naplňte `docs/gpt.html` (lze vyjít z `krizky.html`) a srovnání v `docs/souhrn.html`; v `docs/assets/js/common.js`
   odstraňte u položek menu příznak `soon`.

## Upozornění

Modelové odhady nejsou změřená data – na webu jsou vždy odlišené značkami *fakt*, *jisté minimum* a *model*.
Schéma okrsků na webu je zjednodušené a není přesnou mapou.
