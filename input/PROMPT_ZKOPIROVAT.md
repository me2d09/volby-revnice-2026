# ZADÁNÍ — překopírovat do ChatGPT Work nebo Claude (stejný text pro oba)

Jsi seniorní statistický výzkumník, odborník na bayesovské modelování a vědeckou komunikaci v Pythonu. V přiloženém ZIP archivu `revnice_bayes_handoff.zip` je úplný, ověřený dataset pro komunální volby v Řevnicích 2026 a výsledky 2022. **Proveď kompletní analýzu a vytvoř skutečně spustitelný, výborně vizualizovaný Jupyter notebook**, nikoli pouze plán či pseudokód.

## Cíl

Chci odhadnout počet **individuálních křížků pro každého ze 120 kandidátů**, oddělený od hlasů automaticky přidělených kandidátům při zakřížkování celé kandidátky. Na rozdíl od předchozí hrubé analýzy teď máme **4 okrsky × 8 kandidátek × 15 lidí = 480 hodnot**. V Řevnicích bylo 15 mandátů a celkem 23 939 kandidátských hlasů. Součástí má být analýza stran, kandidátů, okrsků a změn proti 2022, nikoliv jen jeden agregovaný odhad.

## Jak začít

1. Rozbal ZIP, přečti `README.md`, `context/METODIKA_A_IDENTIFIKOVATELNOST.md`, `context/CO_UZ_VIME.md` a `context/LITERATURA_A_ZDROJE.md`. Data jsou v `data/processed/`, původní soubory v `data/raw/`. Předchozí 45scénářový model je pouze **nebayesovský neověřený benchmark**, nikdy ne ground truth.
2. Spusť `python scripts/prepare_and_validate.py`. Pokud selže některá kontrola, nejprve zjisti proč a nepokračuj s chybnými daty. Zpracované CSV obsahují jména/pozice/okrsky. Zkontroluj kódování UTF-8 BOM a oddělovač `;`.
3. Ověř přesná pravidla hlasování podle oficiálních zdrojů (portál.gov.cz, zákon č. 491/2001 Sb.) a relevantní literaturu *ecological inference* a *split-ticket voting*. Odkazy uveď v notebooku s přímými citacemi a DOI. Pokud nějaký zdroj není dostupný, řekni to; nevymýšlej obsah.

## Metodika — musí být vědecky poctivá

Pro kandidáta `i` na listině `s` v okrsku `p` platí `H[p,s,i] = S[p,s,i] + C[p,s,i]`, kde `S` je podpora pocházející od voličů zakřížkovavších stranu (mechanicky klesá s pořadím) a `C` počet efektivních individuálních označení daného kandidáta. Základní matematické omezení je `S[p,s,1] ≥ ... ≥ S[p,s,15] ≥ 0`. Tedy:

`C[p,s,i] ≥ max(0, H[p,s,i] - min(H[p,s,1], ..., H[p,s,i]))`.

Ověř správný **model-free součet minim po okrscích 1 493 hlasů**, proti 1 096 pouze na agregovaných výsledcích. U Terezie Červené (ŠANCE, 10. místo) vychází minimum **88** po okrscích, proti **83** po agregaci.

Vybuduj **skutečný generativní/hierarchický bayesovský model** (ideálně PyMC + ArviZ, případně Stan, odůvodni volbu) oddělující vliv:
- zakřížkování celé strany v daném okrsku;
- počtu dodatečných individuálních křížků u **jiných** stran (0..15, nikoliv pevné maximum 5; extrémní hodnoty mohou být vzácné, nesmějí však být bezdůvodně zakázané);
- individuality konkrétního kandidáta napříč okrsky (hierarchické efekty kandidátů), případné místní popularity v okrscích;
- výhody pozice pro individuální křížky (odděleně od automatické volební mechaniky);
- případného podhodnocení využití všech 15 hlasů u lístků s čistě osobním označením;
- vhodné overdisperze u agregovaných počtů.

Uveď latexové rovnice, vysvětli identifikovatelnost, vazbu na hlasovací lístky, volbu likelihoodu a priorů, včetně toho, které předpoklady mají jen ilustrativní charakter. **Čtyři okrsky nezaručují řádově přesnější rekonstrukci individuálních lístků.** Pokud parametry nejsou identifikovatelné, ukaž to v diagnostice; raději kvalitní intervaly nejistoty a robustní závěry než falešná přesnost. Posterior odhady nesmějí být prezentovány jako ČSÚ skutečně naměřené individuální křížky.

Proveď:
1. prior predictive checks;
2. synthetic-data recovery / simulation-based identifiability check (vygeneruj data s předem známými křížky a ukaž, zda je algoritmus zpětně určí);
3. posterior predictive checks zvlášť pro okrsky, strany a pozice, včetně reziduí;
4. MCMC diagnostiku: R-hat, ESS, divergences, traceplots, runtime (aspoň 4 řetězce, pokud realizovatelné); řetězce opravdu spusť;
5. citlivost na odlišné rozumné priory (zejména P(k=0), rozdělení dlouhého ocasu k=6..15, efekt pořadí a rozptyl individuálních popularit);
6. přehled robustních / nestabilních pořadí kandidátů a srovnání s nebayesovským výchozím modelem;
7. analýzu, zda okrsková data skutečně zlepšují predikci oproti městským agregátům (např. posterior predictive, jednoduchá out-of-precinct validace s jasnou rezervou n=4).

Je-li úplný mechanismus příliš náročný na přesné generativní vzorkování hlasovacích lístků, vybuduj transparentní a testovatelnou aproximaci, **pojmenuj její nedostatky**, a ukaž omezující matematické meze vedle modelových odhadů. Nestírávej rozdíl mezi posterior credible interval, scénářovým rozpětím, predikčním intervalem a rigorózním minimem.

## Požadované výstupy a grafy

Vytvoř GitHub-ready projekt včetně:
- `revnice_2026_bayesian_analysis.ipynb`: hlavní **česky psaný**, hezky členěný, důkladně odcitovaný notebook s rovnicemi, vysvětlením kroků, spustitelnými výpočty a interpretací;
- `requirements.txt` (nebo `environment.yml`) s připnutými verzemi / kontrolovaným prostředím, `README.md` s rychlým spuštěním, přesnou strukturou projektu a popisem dat, případně `.gitignore` a jednoduchým `make`/skriptem;
- `results/candidate_estimates.csv`: všech 120 kandidátů; pozice, strana, městské a okrskové hlasy, rigorózní dolní mez, posterior medián osobních křížků, 50% a 90/95% credible intervals, osobní efekt po očištění o pozici, robustnost pořadí;
- `results/party_estimates.csv`, `results/precinct_estimates.csv`, alespoň několik diagnostických tabulek;
- `figures/` se **statickými PNG/SVG obrázky**, plus `interactive/` se samostatnými Plotly HTML grafy, pokud je to vhodné;
- `methodology.md` s přesným mechanismem, poznámkami k identifikovatelnosti, bibliografií a omezeními.

Grafy (vymysli skvělý čistý design — profi článek/datová žurnalistika, české popisky a diakritika) musí zahrnovat přinejmenším: všech 8 kandidátek a hlasy/mandáty; heatmapu podpory stran ve 4 okrscích; distribuční graf kandidátů dle pozice a strany; posterior intervalové žebříčky odhadovaných osobních křížků; oddělení stranické vs. individuální složky na příkladech kandidátek; příspěvky jednotlivých okrsků; citlivost na priory; MCMC/PPC diagnostiky; největší změny proti 2022 a osobní srovnání zvolených zastupitelů (2022 ovšem byly jen 2 okrsky, takže **neporovnávej stejná čísla okrsků jako stejné území**).

**Interaktivita vs. GitHub:** v živém Jupyteru chci Plotly hover, filtr strany, možnost procházet kandidáty. Ale GitHub nemusí vykreslit JavaScript interaktivních grafů z `.ipynb`; ulož proto statické grafy v notebooku a na GitHub kompatibilní obrázky do `figures/`. Interaktivní grafy publikuj jako samostatné `interactive/*.html` (případně volitelně GitHub Pages), a výslovně vysvětli, jak je otevřít. Nedělej závislost na externím serveru ani API pro spuštění notebooku.

## Závěr a kontrola kvality

Na konec notebooku napiš delší, **běžnou češtinou psaný souhrn** alespoň 10 zajímavých zjištění (koho model označuje za osobnosti, Terezie Červená, přední kandidáti vs. nižší pořadí, okrsky, překvapení, volby 2022–2026, překročení 5 %, a co stále nelze zjistit). Každý závěr označ jako **pozorovaný fakt / rigorózní dolní mez / modelový odhad**. Žádná falešná kauzalita.

Před odevzdáním opravdu spusť notebook od začátku do konce v čistém kernelu, projdi výpočty a zobrazovací chyby, zkontroluj shodu kontrolních součtů a MCMC diagnostiku. Pokud něco nešlo spustit, **konkrétně přiznej co a proč** místo předstírání hotového výpočtu. Odevzdej ZIP repozitáře + notebook zvlášť a krátké česky psané shrnutí nejzajímavějších výsledků. Preferuji kvalitní skutečně spuštěný model před složitějším modelem, který pouze vypadá odborně.
