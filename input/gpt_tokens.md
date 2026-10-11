# Spotřeba tokenů a hypotetické náklady — analýza Řevnice 2026

Datum kontroly: 11. října 2026.

## Výsledek

**Skutečný počet spotřebovaných tokenů, přesné názvy použitých jazykových modelů ani odpovídající cenu nemohu z dostupných záznamů spolehlivě doložit.** Číselný součet nebo částka by byly vymyšlené. „Nedostupné“ níže neznamená nulu.

Rozsah zahrnuje pouze práci na výzkumné analýze komunálních voleb v Řevnicích 2026: od původního zadání přes pokračování po obnovení limitu až po odevzdání projektu a notebooku. Nezahrnuje jiné konverzace ani zpracování tohoto přehledu.

| Část práce | Použitý jazykový model | Vstupní tokeny | Výstupní tokeny včetně uvažování | Hypotetická cena za tokeny |
| --- | --- | ---: | ---: | ---: |
| Původní zpracování analýzy | Přesný model nelze ověřit | Nedostupné | Nedostupné | Nelze spočítat |
| Pokračování po obnovení limitu a dokončení | Přesný model či případné změny modelu nelze ověřit | Nedostupné | Nedostupné | Nelze spočítat |
| **Celá analýza** | **Rozpis podle modelů není dostupný** | **Nedostupné** | **Nedostupné** | **Nelze spočítat** |

## Co jsem ověřil

- Dostupné lokální záznamy neobsahují historii volání jazykového modelu s počty tokenů pro tuto analýzu. Lokální databáze vláken je prázdná a dostupný provozní log neobsahuje záznamy spotřeby tokenů ani identifikaci modelu k této relaci.
- Dostupné nástroje neposkytují vyúčtování tokenů této konverzace.
- Výzkumné výstupy a výpočetní logy nejsou účetním záznamem spotřeby jazykového modelu. Délka notebooku, počet grafů, délka práce ani počet obnovení limitu neumožňují zpětně určit spotřebu.
- Označení asistenta „Codex“ samo o sobě neurčuje konkrétní model a sazbu. Seznam modelů, které prostředí umožňuje použít, rovněž nedokládá, které byly skutečně použity.

## Jak by se cena správně dopočítala

Byl by potřeba export jednotlivých volání patřících k této analýze, obsahující přesný model, čas volání, počty vstupních a výstupních tokenů, podíl vstupu obslouženého z cache a případně zápisy do cache. Dále je nutné znát režim zpracování a příslušnou cenovou kategorii délky kontextu.

Pro každé volání by se použil odpovídající ceník konkrétního modelu a následně by se částky sečetly podle modelu. Při oddělených kategoriích je vzorec:

```text
cena v USD = (běžný vstup × sazba vstupu
              + vstup z cache × sazba cache
              + zápisy do cache × sazba zápisu
              + výstup × sazba výstupu) / 1 000 000
```

Sazby jsou za milion tokenů. Kategorie vstupu se nesmějí započítat dvakrát. Tokeny uvažování jsou součástí výstupních tokenů; nepřičítají se k nim znovu. Výpočet musí zahrnout také opakované zpracování kontextu při jednotlivých voláních. Pouhé spočítání slov ve viditelných odpovědích nestačí.

Tento přepočet by vyjadřoval hypotetickou cenu při účtování přes API. Nejde o vyúčtování předplatného. Samostatné poplatky za nástroje, výpočetní prostředí nebo jiné služby by do požadované ceny **za tokeny** nepatřily.

## Zdroje pro metodiku výpočtu

Oficiální dokumentace ověřená 11. října 2026:

- [OpenAI — API Pricing](https://developers.openai.com/api/docs/pricing): sazby podle modelu, kategorií tokenů a režimu zpracování.
- [OpenAI — Observability and usage](https://developers.openai.com/api/docs/guides/agents-api/observability): interpretace spotřeby, zahrnutí cache a tokenů uvažování, omezení dostupných údajů.

**Závěr:** spotřeba proběhla, ale její velikost a rozdělení podle modelů nejsou doložitelné z údajů, které mám k dispozici. Proto neuvádím ani zdánlivě přesný odhad ceny.
