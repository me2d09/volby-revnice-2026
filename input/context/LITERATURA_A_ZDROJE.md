# Zdroje pro notebook

## Pravidla a výstupy

- **Portál veřejné správy (oficiální):** https://portal.gov.cz/rozcestniky/RZC-118 — popis křížkování celé strany, kandidátů a kombinace; nevyužité hlasy u strany se odečítají zdola.
- **ČSÚ – výsledky Řevnice 2026:** https://volby.gov.cz/app/kv2026/cs/20261009/results/!___2100_2110_539643
- **ČSÚ – příklad detailu strany č. 5:** https://volby.gov.cz/app/kv2026/cs/20261009/results/!__1_2100_2110_539643____5
- **2022 Řevnice výsledky:** https://www.seznamzpravy.cz/p/vysledky-voleb/2022/komunalni-volby/obec/539643-revnice
- **Zákon č. 491/2001 Sb.** (zejména § 40–41): právní text ověř v aktuálním znění. Portál veřejné správy je pro zadání přímo použitelný.

## Metodická akademická literatura

- Wendy K. Tam Cho & Brian J. Gaines (2004): *The Limits of Ecological Inference: The Case of Split-Ticket Voting*. American Journal of Political Science 48(1), 152–171. DOI: https://doi.org/10.1111/j.0092-5853.2004.00062.x — klíčový důkaz, že agregátní data nemusí identifikovat hlasování jednotlivců.
- Park, Hanmer & Biggers (2014): *Ecological inference under unfavorable conditions: Straight and split-ticket voting in diverse settings and small samples*. Electoral Studies. DOI https://doi.org/10.1016/j.electstud.2014.08.006 — metodická příbuznost; přesné bibliografické údaje ověř.
- David Kaňok: *Analýza preferenčního hlasování ve volbách do zastupitelstev obcí v letech 2006–2018*, https://theses.cz/id/id9d17/ — odlišit popisné indexy preferencí od skutečného rozkladu hlasů.

## Software

- **PyMC:** https://www.pymc.io/projects/docs/en/stable/ (Bayesian modelling / MCMC)
- **ArviZ:** https://python.arviz.org/en/stable/ (posterior checks a diagnostika)
- **Plotly:** https://plotly.com/python/ (interaktivní grafy; GitHub rendering ověřit)
- **Jupyter notebook GitHub preview:** https://docs.github.com/en/repositories/working-with-files/using-files/working-with-non-code-files (GitHub obvykle zobrazuje statické výstupy uložené v notebooku; dynamické JS grafy Plotly nemusí fungovat; nabídnout statický fallback nebo samostatné HTML přes Pages).

U každé odborné a metodické pasáže v notebooku cituj přímo relevantní zdroj. Dodaná čísla 2026 pocházejí z uživatelem exportovaných CSV ČSÚ. Nepoužívat internetové výsledky jen k odhadu chybějících čísel, všechna primární data jsou v archivu.
