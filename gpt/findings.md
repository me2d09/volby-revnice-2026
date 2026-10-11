# Co jsme zjistili: Řevnice 2026

Každý bod rozlišuje pozorovaný fakt, matematickou mez nebo výsledek modelu. Úzký interval modelu není důkaz, že známe skutečné lístky.

1. **Pozorovaný fakt — vyhrálo DOBŘE.** Získalo 5 553 kandidátských hlasů a čtyři mandáty. ŠANCE má 4 840 hlasů a tři mandáty, Perspektiva 4 683 a tři. Dohromady bylo odevzdáno 23 939 kandidátských hlasů. To není počet lidí, kteří přišli volit.

2. **Rigorózní dolní mez — osobních křížků muselo být nejméně 2 897.** To je 12,10 % všech hlasů. Původní součet bodových minim 1 493 je správný, ale nezohledňuje, že jeden účinně označený plný stranický lístek vydá celkem 15 hlasů. Nová mez tento rozpočet používá. Kód navíc sestavil platné syntetické lístky dosahující minima a zkontroloval součty. Dosažitelnost zde nepodmiňuje na neznámém počtu platných lístků; nejde o rekonstrukci skutečných voličů.

3. **Rigorózní dolní mez — Terezie Červená má zaručeno alespoň 88 osobních křížků.** Po okrscích 17 + 21 + 28 + 22. Její pozorovaný výsledek je 383 hlasů z desátého místa ŠANCE. Z čistě městského součtu by šlo dokázat jen 83. Okrsky tedy přinesly skutečnou informaci, i když neodhalily lístky.

4. **Modelový odhad — referenční rozklad dává zhruba 5 825 osobních křížků.** Jeho 95% posteriorový interval je 5 100–6 762, medián 24,3 % všech hlasů. Platí podmíněně na konkrétním agregovaném modelu. Napříč sedmi variantami se mediány pohybují mezi 5 542 a 6 789. Toto rozpětí není další credible interval a nezahrnuje všechny možné chyby. Starých 6 884 bylo mediánem nebayesovských scénářů, nikoli naměřeným počtem.

5. **Modelový odhad — mezi nejvýraznějšími osobnostmi jsou Pavel Hartmann, Libor Kvasnička, Petr Kozák.** Referenční mediány osobních počtů jsou postupně 154, 149, 136. Jde o žebříček skryté složky podle modelu. Odhad efektu po očištění o pozici je relativní uvnitř dané strany, nikoli univerzální měřítko popularity.

6. **Modelový odhad — Terezie je výrazná i po zohlednění pořadí.** Referenčně 117 osobních křížků, 95% interval 103–134. Její mediány v alternativách jsou 114–126. Modelový 95% interval celoměstského pořadí je přibližně 3.–12. místo. Číslo 88 je jistá dolní mez; ostatní čísla v tomto bodě jsou podmíněná modelem.

7. **Pozorovaný fakt a modelový odhad — nejvíce celkových hlasů není totéž jako nejvíce osobních křížků.** Martina Štěpánková má pozorovaných 512 hlasů, nejvíce ve městě. Referenční model její osobní složky dává medián 113, s 95% intervalem 72–157. Vedoucí pozice na silné listině přináší mnoho automatických hlasů; přesné oddělení z agregátů přímo nezměříme. Není to tvrzení, že její reálná osobní podpora byla slabá.

8. **Pozorovaný fakt — čtvrtý okrsek zásadně mění aritmetické pořadí stran.** DOBŘE v něm dostalo 1 847 hlasů, 29,17 %. Součet ostatních tří okrsků je ŠANCE 3 838, DOBŘE 3 706 a Perspektiva 3 647. Jde o porovnání součtů, nikoli o příčinné vysvětlení výsledku nebo chování jednotlivých obyvatel.

9. **Pozorovaný fakt — ODS byla velmi blízko pětiprocentní hranici.** Její podíl je 1 182 / 23 939 = 4,9375 %, Srdce má 4,6034 %. Ani jedna listina mandát nezískala. Při neměnném jmenovateli je nejnižší počet dosahující 5 % 1 197, tedy o 15 více. U nově přidaných hlasů, které současně zvyšují jmenovatel, by bylo potřeba 16: 1 198 / 23 955. Samotné překročení hranice není totéž co výpočet konkrétního mandátu.

10. **Pozorovaný fakt — růst absolutních hlasů nemusí znamenat růst podílu.** ŠANCE získala proti 2022 o 12 hlasů více a TOP 09 o 79 více, ale podílem obě klesly. Celkový počet hlasů vzrostl z 21 773 na 23 939, o 9,95 %. Největší pokles podílu mezi opakovaně kandidujícími listinami má Perspektiva, přibližně sedm procentních bodů. DOBŘE je nová listina; z toho nevyčteme, od koho k ní přišli voliči.

11. **Pozorovaný fakt — některým zastupitelům přibyly hlasy výrazně.** Pavel Hartmann za TOP 09 stoupl ze 157 na 223 (+66). Markéta Sedláčková Davidová ze 167 na 238 (+71), přičemž změnila kandidátku z ODS na Naše Řevnice. Tomáš Smrčka klesl ze 485 na 397. Jde o celkové kandidátské hlasy. Historické údaje jsou neúplné a chybějící záznam neznamená nulu.

12. **Pozorovaný fakt — vyšší kandidátský počet automaticky nezaručil zvolení.** Renata Dudová získala 405 hlasů a nebyla zvolena, Vladimír Bobek se 393 zvolen byl. Rozhoduje rozdělení mandátů straně, původní pořadí a splnění podmínky pro přednostní posun. Ani 405 ani 393 není údaj o samostatných osobních křížcích.

13. **Modelový odhad — pořadí je potřeba číst jako nejisté.** Pravidlu „pravděpodobnost top 10 alespoň 0,8 a splněná kandidátská MCMC diagnostika ve všech sedmi variantách“ vyhovuje tento počet kandidátů: 3 — Pavel Hartmann, Libor Kvasnička, Petr Kozák. Ostatní mohou být výrazní, ale jejich přesné zařazení je méně stabilní. Kategorie robustnosti není důkaz správnosti celé modelové rodiny; CSV ukazuje i intervaly pořadí.

14. **Modelový odhad (predikční ověření) — okrskový model není automaticky lepší.** Průměrná RMSE ve čtyřech vynechaných okrscích je 5,32 hlasu pro hierarchický model, 5,38 pro sloučené kandidátské podíly a 7,19 pro profil podle pořadí. Hierarchický model v tomto testu vyšel lépe než jednoduché sloučení. Test všem metodám poskytuje stranický součet v testovacím okrsku a ověřuje rozdělení mezi lidmi. Modelové losy se na známé součty přepočítávají; nejde o přesné podmíněné vzorkování původního modelu. Čtyři foldy neprokazují obecné pořadí metod ani přesnost rozkladu osobních hlasů.

15. **Modelový odhad (zkouška se známou pravdou) — dobrá predikce hlasů může skrývat chybu rozkladu.** Ve vzorku ze stejného agregovaného modelu je pravda 5 229, posteriorový medián 5 641, interval 5 020–6 507. V odlišném generátoru platných lístků je pravda 5 779, medián 6 030, interval 5 281–6 966; kandidátské 95% intervaly obsahují pravdu u 97,5 % osob. Celková pravda je zde uvnitř intervalu, ale jeden úspěšný stress test není plošná validace modelu. Dva experimenty nejsou formální SBC kalibrace.

16. **Modelový odhad (numerická kontrola) — MCMC a volební realizovatelnost jsou různé kontroly.** Referenční běh má čtyři řetězce, maximum R-hat 1,0088, minimum bulk ESS 521 a tail ESS 478. U těchto běhů zůstává alespoň jeden parametr mimo orientační diagnostický gate: cv_1, cv_2, cv_3, heterogeneous, no_candidate, party_first, poisson_like, strong_pooling, weak_position. Přesné veličiny, ESS a R-hat uvádí diagnostic_flags.csv. Jejich výsledky je nutné číst s dodatečnou numerickou rezervou. Z 2800 předem vybraných kontrol posteriorových rozkladů prošlo přesným testem přiřazení na platné lístky 2800. To prokazuje realizovatelnost testovaných rozkladů, nikoli skutečný způsob volby lidí.

17. **Modelový odhad (neidentifikované parametry) — označení strany současně s 15 cizími kandidáty nelze odlišit od stejné čistě jmenné volby.** Stranický křížek už nevytvoří automatický hlas. Ani využití všech 15 možností na čistě jmenných lístcích zde samostatně neurčujeme. Pomocné priory těchto veličin zůstávají v této aproximaci beze změny; nejsou vydávány za odhady z dat.

18. **Pozorovaný fakt — rok 2022 měl dva okrsky, rok 2026 čtyři.** Srovnání let proto provádíme za město a dostupné osoby. Stejné číslo okrsku není dokladem stejného území. Pro ověření individuálních podílů by byla nejcennější anonymizovaná informace o způsobu vyplnění lístků, případně alespoň četnosti stranické/kombinované/jmenné volby a využitých hlasů.
