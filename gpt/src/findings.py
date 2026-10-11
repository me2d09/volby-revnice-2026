"""Czech findings generated from actual outputs, including unfavorable diagnostics."""
import pandas as pd
from .experiments import ROOT,load_data

def human(name):return {'Hartmann Pavel Ing.':'Pavel Hartmann','Kvasnička Libor':'Libor Kvasnička','Kozák Petr Ing.':'Petr Kozák'}.get(name,name)
def n(x):return f'{x:,.0f}'.replace(',',' ')
def f(x,d=1):return f'{x:.{d}f}'.replace('.',',')
def csv(name):return pd.read_csv(ROOT/'results'/name,sep=';')

def write_findings():
 H,obs,city=load_data();c=csv('candidate_estimates.csv');ss=csv('prior_sensitivity.csv');cv=csv('out_of_precinct_validation.csv');rec=csv('synthetic_recovery.csv');diag=csv('mcmc_run_summary.csv')
 total=ss[ss.scenario=='reference'].iloc[0];t=c[c.name.str.contains('Červená Terezie')].iloc[0];top=c.nlargest(3,'personal_median');m=c[c.name.str.contains('Štěpánková Martina')].iloc[0];cvmeans=cv.groupby('model').RMSE.mean();audit=csv('ballot_feasibility_audit.csv');good=audit.feasible.astype(str).str.lower().eq('true')
 rf=rec[rec.experiment=='ballot'].iloc[0];rm=rec[rec.experiment=='matched'].iloc[0];run=diag[diag.label=='reference'].iloc[0];stable=c[(c.min_scenario_p_top10>=.8)&c.all_scenarios_candidate_mcmc_gate_pass];failed=diag[~diag.mcmc_gate_pass].label.tolist()
 text=f'''# Co jsme zjistili: Řevnice 2026

Každý bod rozlišuje pozorovaný fakt, matematickou mez nebo výsledek modelu. Úzký interval modelu není důkaz, že známe skutečné lístky.

1. **Pozorovaný fakt — vyhrálo DOBŘE.** Získalo 5 553 kandidátských hlasů a čtyři mandáty. ŠANCE má 4 840 hlasů a tři mandáty, Perspektiva 4 683 a tři. Dohromady bylo odevzdáno 23 939 kandidátských hlasů. To není počet lidí, kteří přišli volit.

2. **Rigorózní dolní mez — osobních křížků muselo být nejméně 2 897.** To je {f(2897/23939*100,2)} % všech hlasů. Původní součet bodových minim 1 493 je správný, ale nezohledňuje, že jeden účinně označený plný stranický lístek vydá celkem 15 hlasů. Nová mez tento rozpočet používá. Kód navíc sestavil platné syntetické lístky dosahující minima a zkontroloval součty. Dosažitelnost zde nepodmiňuje na neznámém počtu platných lístků; nejde o rekonstrukci skutečných voličů.

3. **Rigorózní dolní mez — Terezie Červená má zaručeno alespoň 88 osobních křížků.** Po okrscích 17 + 21 + 28 + 22. Její pozorovaný výsledek je 383 hlasů z desátého místa ŠANCE. Z čistě městského součtu by šlo dokázat jen 83. Okrsky tedy přinesly skutečnou informaci, i když neodhalily lístky.

4. **Modelový odhad — referenční rozklad dává zhruba {n(total.personal_total_median)} osobních křížků.** Jeho 95% posteriorový interval je {n(total.personal_total_q025)}–{n(total.personal_total_q975)}, medián {f(total.personal_share_median*100)} % všech hlasů. Platí podmíněně na konkrétním agregovaném modelu. Napříč sedmi variantami se mediány pohybují mezi {n(ss.personal_total_median.min())} a {n(ss.personal_total_median.max())}. Toto rozpětí není další credible interval a nezahrnuje všechny možné chyby. Starých 6 884 bylo mediánem nebayesovských scénářů, nikoli naměřeným počtem.

5. **Modelový odhad — mezi nejvýraznějšími osobnostmi jsou {', '.join(human(x) for x in top.name)}.** Referenční mediány osobních počtů jsou postupně {', '.join(n(x) for x in top.personal_median)}. Jde o žebříček skryté složky podle modelu. Odhad efektu po očištění o pozici je relativní uvnitř dané strany, nikoli univerzální měřítko popularity.

6. **Modelový odhad — Terezie je výrazná i po zohlednění pořadí.** Referenčně {n(t.personal_median)} osobních křížků, 95% interval {n(t.personal_q025)}–{n(t.personal_q975)}. Její mediány v alternativách jsou {n(t.scenario_median_min)}–{n(t.scenario_median_max)}. Modelový 95% interval celoměstského pořadí je přibližně {n(t.rank_q025)}.–{n(t.rank_q975)}. místo. Číslo 88 je jistá dolní mez; ostatní čísla v tomto bodě jsou podmíněná modelem.

7. **Pozorovaný fakt a modelový odhad — nejvíce celkových hlasů není totéž jako nejvíce osobních křížků.** Martina Štěpánková má pozorovaných 512 hlasů, nejvíce ve městě. Referenční model její osobní složky dává medián {n(m.personal_median)}, s 95% intervalem {n(m.personal_q025)}–{n(m.personal_q975)}. Vedoucí pozice na silné listině přináší mnoho automatických hlasů; přesné oddělení z agregátů přímo nezměříme. Není to tvrzení, že její reálná osobní podpora byla slabá.

8. **Pozorovaný fakt — čtvrtý okrsek zásadně mění aritmetické pořadí stran.** DOBŘE v něm dostalo 1 847 hlasů, 29,17 %. Součet ostatních tří okrsků je ŠANCE 3 838, DOBŘE 3 706 a Perspektiva 3 647. Jde o porovnání součtů, nikoli o příčinné vysvětlení výsledku nebo chování jednotlivých obyvatel.

9. **Pozorovaný fakt — ODS byla velmi blízko pětiprocentní hranici.** Její podíl je 1 182 / 23 939 = {f(1182/23939*100,4)} %, Srdce má {f(1102/23939*100,4)} %. Ani jedna listina mandát nezískala. Při neměnném jmenovateli je nejnižší počet dosahující 5 % 1 197, tedy o 15 více. U nově přidaných hlasů, které současně zvyšují jmenovatel, by bylo potřeba 16: 1 198 / 23 955. Samotné překročení hranice není totéž co výpočet konkrétního mandátu.

10. **Pozorovaný fakt — růst absolutních hlasů nemusí znamenat růst podílu.** ŠANCE získala proti 2022 o 12 hlasů více a TOP 09 o 79 více, ale podílem obě klesly. Celkový počet hlasů vzrostl z 21 773 na 23 939, o 9,95 %. Největší pokles podílu mezi opakovaně kandidujícími listinami má Perspektiva, přibližně sedm procentních bodů. DOBŘE je nová listina; z toho nevyčteme, od koho k ní přišli voliči.

11. **Pozorovaný fakt — některým zastupitelům přibyly hlasy výrazně.** Pavel Hartmann za TOP 09 stoupl ze 157 na 223 (+66). Markéta Sedláčková Davidová ze 167 na 238 (+71), přičemž změnila kandidátku z ODS na Naše Řevnice. Tomáš Smrčka klesl ze 485 na 397. Jde o celkové kandidátské hlasy. Historické údaje jsou neúplné a chybějící záznam neznamená nulu.

12. **Pozorovaný fakt — vyšší kandidátský počet automaticky nezaručil zvolení.** Renata Dudová získala 405 hlasů a nebyla zvolena, Vladimír Bobek se 393 zvolen byl. Rozhoduje rozdělení mandátů straně, původní pořadí a splnění podmínky pro přednostní posun. Ani 405 ani 393 není údaj o samostatných osobních křížcích.

13. **Modelový odhad — pořadí je potřeba číst jako nejisté.** Pravidlu „pravděpodobnost top 10 alespoň 0,8 a splněná kandidátská MCMC diagnostika ve všech sedmi variantách“ vyhovuje tento počet kandidátů: {len(stable)} — {', '.join(human(x) for x in stable.name) if len(stable) else 'nikdo'}. Ostatní mohou být výrazní, ale jejich přesné zařazení je méně stabilní. Kategorie robustnosti není důkaz správnosti celé modelové rodiny; CSV ukazuje i intervaly pořadí.

14. **Modelový odhad (predikční ověření) — okrskový model není automaticky lepší.** Průměrná RMSE ve čtyřech vynechaných okrscích je {f(cvmeans['hierarchical'],2)} hlasu pro hierarchický model, {f(cvmeans['city_pooled'],2)} pro sloučené kandidátské podíly a {f(cvmeans['position_only'],2)} pro profil podle pořadí. {'Hierarchický model v tomto testu vyšel lépe než jednoduché sloučení.' if cvmeans['hierarchical']<cvmeans['city_pooled'] else 'Jednoduché sloučené podíly v tomto testu vycházejí lépe než hierarchický model.'} Test všem metodám poskytuje stranický součet v testovacím okrsku a ověřuje rozdělení mezi lidmi. Modelové losy se na známé součty přepočítávají; nejde o přesné podmíněné vzorkování původního modelu. Čtyři foldy neprokazují obecné pořadí metod ani přesnost rozkladu osobních hlasů.

15. **Modelový odhad (zkouška se známou pravdou) — dobrá predikce hlasů může skrývat chybu rozkladu.** Ve vzorku ze stejného agregovaného modelu je pravda {n(rm.true_personal_total)}, posteriorový medián {n(rm.posterior_median)}, interval {n(rm.q025)}–{n(rm.q975)}. V odlišném generátoru platných lístků je pravda {n(rf.true_personal_total)}, medián {n(rf.posterior_median)}, interval {n(rf.q025)}–{n(rf.q975)}; kandidátské 95% intervaly obsahují pravdu u {f(rf.candidate_95_coverage*100)} % osob. {'Skutečný celkový počet ve stress testu neleží v 95% intervalu. To je konkrétní důvod, proč intervaly reálných dat nepředstavují úplnou nejistotu o pravdě.' if not rf.q025<=rf.true_personal_total<=rf.q975 else 'Celková pravda je zde uvnitř intervalu, ale jeden úspěšný stress test není plošná validace modelu.'} Dva experimenty nejsou formální SBC kalibrace.

16. **Modelový odhad (numerická kontrola) — MCMC a volební realizovatelnost jsou různé kontroly.** Referenční běh má čtyři řetězce, maximum R-hat {f(run.max_rhat,4)}, minimum bulk ESS {n(run.min_ess_bulk)} a tail ESS {n(run.min_ess_tail)}. {'Všechny sledované parametry prošly zvoleným diagnostickým gate ve všech bězích.' if not failed else 'U těchto běhů zůstává alespoň jeden parametr mimo orientační diagnostický gate: '+', '.join(failed)+'. Přesné veličiny, ESS a R-hat uvádí diagnostic_flags.csv. Jejich výsledky je nutné číst s dodatečnou numerickou rezervou.'} Z {len(audit)} předem vybraných kontrol posteriorových rozkladů prošlo přesným testem přiřazení na platné lístky {int(good.sum())}. To prokazuje realizovatelnost testovaných rozkladů, nikoli skutečný způsob volby lidí.

17. **Modelový odhad (neidentifikované parametry) — označení strany současně s 15 cizími kandidáty nelze odlišit od stejné čistě jmenné volby.** Stranický křížek už nevytvoří automatický hlas. Ani využití všech 15 možností na čistě jmenných lístcích zde samostatně neurčujeme. Pomocné priory těchto veličin zůstávají v této aproximaci beze změny; nejsou vydávány za odhady z dat.

18. **Pozorovaný fakt — rok 2022 měl dva okrsky, rok 2026 čtyři.** Srovnání let proto provádíme za město a dostupné osoby. Stejné číslo okrsku není dokladem stejného území. Pro ověření individuálních podílů by byla nejcennější anonymizovaná informace o způsobu vyplnění lístků, případně alespoň četnosti stranické/kombinované/jmenné volby a využitých hlasů.
'''
 (ROOT/'findings.md').write_text(text,encoding='utf8');return text
