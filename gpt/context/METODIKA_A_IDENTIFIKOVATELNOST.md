# Mechanika hlasování a identifikovatelnost

## Co ČSÚ v tabulkách udává

`votes_{p,s,i}` je **součet všech platných hlasů připsaných kandidátu**, ne čistý počet jeho osobních křížků. `p` = okrsek 1..4; `s` = kandidátka 1..8; `i` = pořadí na listině 1..15.

V komunálních volbách do 15členného zastupitelstva může volič označit celou jednu stranu, jednotlivé kandidáty (max 15), nebo stranu společně s kandidáty **jiných** stran. Je-li zvolena strana a `k` kandidátů jinde, přidělí se jejím kandidátům ze začátku listiny nejvýše `15-k` hlasů (jeden každému); ostatní kandidáti stranické hlasy nedostanou. Osobní označení kandidáta na téže označené listině se **nepřičítá podruhé**.

Stranicky přidělené hlasy `S_{p,s,i}` jsou proto **nerostoucí** s pořadím kandidáta `i`:

```math
H_{p,s,i}=S_{p,s,i}+C_{p,s,i},\qquad
S_{p,s,1}\ge S_{p,s,2}\ge\dots\ge S_{p,s,15}\ge0,\qquad C_{p,s,i}\ge0.
```

`C` je počet **efektivních individuálních označení kandidáta**, který skutečně vytvořil hlas; není pozorován. Pro libovolného kandidáta a okrsek tedy platí přesná nerovnost

```math
C_{p,s,i}\ge\max\left(0,\;H_{p,s,i}-\min_{j\le i}H_{p,s,j}\right).
```

Sčítání těchto mezí přes všechny okrsky je silnější než výpočet až z celoměstského součtu. Na dodaných datech to dává **1 493 vs. 1 096** hlasů celkem a Terezii Červené **88 vs. 83**. Jde o **matematické dolní meze, nikoli počty hlasovacích lístků**. Lepší dolní mez při dalších omezeních je vítaná, ale musí být dokázána, ne dodána apriorním předpokladem.

## Možná generativní formulace (výchozí návrh, ne povinné řešení)

Pro okrsek p a stranu s latentně definuj `N_{p,s,k}`, počet (nebo při aproximaci intenzitu) lístků označujících tuto stranu a `k` kandidátů jinde, k = 0..15. Pak:

```math
S_{p,s,i}=\sum_{k=0}^{15-i}N_{p,s,k}.
```

Pokud je `k=15`, označení strany už nepřidává její kandidátce žádný hlas a **nelze je z agregátů odlišit od voliče, který označil pouze 15 jednotlivců**. Je možné explicitně zvolit identifikační konvenci `k=0..14` pro *efektivně* zakřížkované strany, ale musí být popsána.

Druhá složka `C_{p,s,i}` pochází z voličů individuálně označujících kandidáty: z lístků označujících *jinou* stranu i z čistě jmenných lístků. Kandidát může dostat na jednom lístku nejvýše jeden hlas. Přirozený model by měl alespoň přibližně respektovat omezení počtu křížků na lístek a konzervaci hlasů v okrsku.

Hierarchická parametrizace může modelovat například:

- sdílené priory tvaru rozdělení počtu dodatečných křížků `k`, ale **bez tvrdého useknutí na 5**;
- různé počty zakřížkování strany podle okrsku/strany, s částečným poolingem;
- individuální popularitu kandidáta konzistentní napříč okrsky + odchylky po okrscích;
- pozici na listině jako systematický prediktor u individuálních křížků, odděleně od mechanického přiřazení hlasů;
- overdisperzi, aby nešlo jen o uměle přesný Poisson;
- případně alternativní flexibilní distribuce `K`: zero-inflated geometrická/negativně binomická, Dirichlet/mix, heavy-tail citlivost.

Všechny předpoklady musejí být explicitní. Posterior je podmíněný modelem a priory; `4 okrsky × 8 stran × 15 kandidátů = 480 pozorování` **neznamená**, že máme 480 nezávislých ballot-level pozorování.

## Co je nutné testovat

1. Před fitováním **prior predictive checks** a simulace známé pravdy; ověř, zda lze rozklad vůbec zpětně identifikovat.
2. Následně posterior predictive checks (po stranách, pozicích a okrscích), residuals a odhad overdisperze.
3. MCMC diagnostiky: R-hat, effective sample size, divergences, trace plots, případně BFMI.
4. Citlivost na priory (zejména P(K=0), ocas K=6..15, rozptyl individuálních popularit, sílu pooling).
5. Srovnání s baseline: pouze strana/pozice bez náhodné individuální popularity, model s osobní popularitou, a pokud možno alternativa v likelihood. Ověřit out-of-precinct generalizaci s velkou výhradou n=4.
6. U všech odhadů dodrž `0 ≤ C_{p,s,i} ≤ H_{p,s,i}` a soulad s matematickými dolními mezemi. Jestli se používá aproximace očekávaných hodnot, nevydávat zlomkový posterior průměr za skutečný počet křížků.

## Limity

Klíčové rozdělení hlasů podle **způsobu vyplnění lístku** ČSÚ nepublikuje, publikují se agregáty kandidátů. Různé hlasovací mechanismy mohou dávat totožná pozorovaná data, i na úrovni okrsků. Užší credible interval bez podložených priorů nemusí znamenat bližší pravdu. Pokud se ukáže, že data parametry nerozlišují, je dobrým vědeckým výsledkem **přiznaná slabá identifikovatelnost**, robustní dolní meze a scénářová analýza.
