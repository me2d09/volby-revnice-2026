# Spotřeba tokenů a hypotetická cena – analýza křížkování Řevnice 2026

**Model:** Claude Fable 5.1 (API ID `claude-fable-5-1`, Anthropic) – všech 225 volání v této relaci běželo na tomto modelu, žádný jiný model (ani subagent) se nepoužil.
**Relace:** 10. 10. 2026 22:23 – 11. 10. 2026 13:38 (CEST), 225 kol s voláním modelu; zahrnuje celou analýzu (data, model, MCMC, notebook, dokumentace, balení) i závěrečný rozbor spotřeby. Čísla jsou odečtena z transkriptu relace; časté čekání na dlouhé MCMC běhy (celkem ~4 h) se počítá jako běžná kola.

## Kolik tokenů se spotřebovalo

| Druh tokenů (model Claude Fable 5.1) | Počet | Poznámka |
|---|---:|---|
| Vstup bez cache | 450 | téměř vše šlo přes cache |
| Čtení z prompt cache | 76 615 412 | systémový prompt, seznam nástrojů a rostoucí historie rozhovoru, načítané každé kolo |
| Zápis do prompt cache (1h TTL) | 1 351 922 | nový obsah každého kola (výpisy, soubory, výsledky) |
| Výstup (text, kód, úvahy) | 280 258 | vlastní „psaní“ modelu |
| **Celkem zpracováno** | **78 248 042** | z toho 99,6 % je opakované čtení kontextu z cache |

Pro srovnání: celý notebook, kód, metodika a README mají dohromady řádově 100 tisíc tokenů – naprostou většinu spotřeby tvoří opakované načítání kontextu (až ~530 tisíc tokenů na kolo ke konci relace), nikoli samotný text.

## Kolik by to stálo, kdyby se platilo za tokeny

Ceník API pro Claude Fable 5.1 (oficiální dokumentace, stav k 11. 10. 2026): vstup 10 USD / 1 M tokenů, výstup 50 USD / 1 M, zápis do cache 12,50 USD (5 min) resp. 20 USD (1 h) / 1 M, čtení z cache 0,25 USD / 1 M; Batch API má 50% slevu.

| Položka (Claude Fable 5.1) | Tokeny | Sazba (USD / 1 M) | Cena (USD) |
|---|---:|---:|---:|
| Vstup bez cache | 450 | 10,00 | 0,00 |
| Čtení z cache | 76 615 412 | 0,25 | 19,15 |
| Zápis do cache (1 h) | 1 351 922 | 20,00 | 27,04 |
| Výstup | 280 258 | 50,00 | 14,01 |
| **Celkem** | 78 248 042 | | **≈ 60,2 USD** |

Orientačně v korunách (kurz 21–25 CZK/USD): **≈ 1 260–1 510 Kč**, při 23 CZK/USD cca 1 385 Kč.

Co to znamená v praxi:

* **Bez prompt cache** by stejná práce stála ≈ 794 USD (celý kontext každé kolo za plnou cenu vstupu); cache tedy ušetřila zhruba 92 % nákladů.
* V dávkovém režimu (Batch API, 50% sleva) by to bylo ≈ 30 USD – ale dávkový režim nejde použít pro interaktivní agentní práci tohoto typu.
* Nejdražší dvě položky jsou zápisy do cache (27 USD) a čtení kontextu (19 USD), tj. náklad na to, že model „vidí“ celý dosavadní průběh práce včetně dlouhých výpisů z MCMC fitů. Samotné generování textu a kódu vyšlo na 14 USD.
* Kde by se dalo ušetřit: méně častá kontrola dlouhých výpočtů (čekací smyčky každých 10 minut byly cca 40 kol), kratší výpisy testovacích fitů a včasnější kompaktní shrnutí mezivýsledků.

## Zdroje

* Transkript relace (`~/.claude/projects/.../a2850007-….jsonl`), pole `message.usage` a `message.model` u všech odpovědí modelu (225 záznamů, deduplikováno podle ID zprávy).
* Ceník: Claude Platform docs – Claude Fable 5.1, https://platform.claude.com/docs/models/fable-5-1 (vydání 1. 9. 2026; ceny v USD za 1 milion tokenů).
