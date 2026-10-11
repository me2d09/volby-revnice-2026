# Řevnice 2026: co lze zjistit o individuálních křížcích

## 1. Úloha a význam čísel

Analyzujeme 4 okrsky × 8 plných kandidátek × 15 kandidátů. Pozorování $H_{psi}$ jsou **připsané kandidátské hlasy**, nikoli zaznamenané osobní křížky. Data z dodaných exportů ČSÚ dávají přesně 23 939 hlasů. Jména v tabulkách zachovávají pořadí příjmení/jméno v exportu. Četnost křížkování jedné osoby nelze zaměňovat za procento voličů ani za přechody voličů mezi stranami.

Čtyři okrsky přidávají geografickou informaci, ale neposkytují jednotlivé lístky. V literatuře jde o **ekologickou inferenci**. Cho a Gaines [4] na příkladu split-ticket voting ukazují, že kvalitní agregátní fit sám neospravedlňuje individuální závěry. Park, Hanmer a Biggers [5] ověřují metody proti skutečným ballot-image datům, včetně vlivu počtu agregovaných jednotek. Jejich podmínky ani výsledky o desítkách jednotek nepřenášíme na čtyři české okrsky. V této práci nejde o aplikaci jejich konkrétního estimátoru, nýbrž o samostatný model s explicitním volebním mechanismem.

## 2. Ověřená pravidla a rozsah ověření

Portál veřejné správy [1] uvádí: „Křížků může volič udělit tolik, kolik je voleno členů zastupitelstva.“ Aktuální informace Ministerstva vnitra pro rok 2026 [2] potvrzují označení jedné strany, jednotlivců, nebo kombinace; při kombinaci mají přednost jednotlivci na **jiných** listinách. Označení lidí na současně označené straně další hlas nepřidá. Materiál MV o kandidatuře výslovně potvrzuje, že způsob hlasování se od roku 2022 nezměnil.

Právní opora: zákon č. 491/2001 Sb., zejména § 34, § 40–41 a § 45 [3], ve znění účinném od 27. 5. 2026. Ministerstvo na něj přímo odkazuje. e-Sbírka se při přímém čtení načetla bez textového těla; dostupný indexovaný úryvek potvrzuje přednost jednotlivě označených kandidátů, ale **celý aktuální právní text nebyl strojově přečten**. Detail mechanismu byl proto ověřen ze dvou přímo čitelných oficiálních vysvětlení [1,2]. To není tvrzení o úplném právním auditu všech novel. Údaje 2026 samotné pocházejí z uživatelského datového balíčku, nikoli z nové internetové synchronizace výsledků.

Všech osm analyzovaných listin má 15 platných kandidátů. Pro lístek označující listinu $s$ a $k$ jednotlivců jinde vznikne automatický prefix délky $15-k$. Zbytek tvoří $k$ individuálních hlasů. Počet hlasů z takového lístku je přesně 15. Lístek s pouhými individuálními označeními může využít 1 až 15 hlasů. Neplatné a prázdné lístky nejsou předmětem modelu.

## 3. Přesné meze bez statistického modelu

Rozklad je

$$H_{psi}=S_{psi}+C_{psi},\qquad S_{ps1}\ge\cdots\ge S_{ps15}\ge0.$$

Proto $S_{psi}\le M_{psi}=\min_{j\le i}H_{psj}$, a tedy

$$C_{psi}\ge H_{psi}-M_{psi}.$$

Součet bodových mezí je 1 493 po okrscích a 1 096 po městské agregaci. U Terezie Červené je to 88 = 17 + 21 + 28 + 22 proti městským 83. **Nulová mez u lídra neříká, že neměl osobní podporu.**

### Nové, silnější omezení: rozpočet hlasů na lístku

Označme $B_{ps}=S_{ps1}$ počet *účinně* označených listin, tedy případů $k<15$, a $T_p=\sum_{si}H_{psi}$. Každý takový lístek vydá 15 hlasů. I při neznámém počtu všech platných lístků proto nutně platí

$$\sum_s B_{ps}\le\lfloor T_p/15\rfloor.$$

Pro fixované $B_{ps}$ největší možná automatická složka splňuje

$$S_{psi}\le\min(M_{psi},B_{ps}).$$

Maximalizujeme součet pravé strany při uvedeném celočíselném rozpočtu. Přírůstek při zvýšení $B_s$ z $b$ na $b+1$ je počet pozic s $M_{si}>b$. Tyto přírůstky jsou nerostoucí. Optimální řešení proto vznikne postupným výběrem největšího dostupného přírůstku. Je to přesná diskrétní konkávní alokace, nikoli numerická relaxace s nejistým zaokrouhlováním.

| Okrsek | Bodová mez z monotonicity | Mez s rozpočtem lístků |
|---|---:|---:|
| 1 | 343 | 646 |
| 2 | 352 | 779 |
| 3 | 377 | 711 |
| 4 | 421 | 761 |
| **Celkem** | **1 493** | **2 897** |

Z toho plyne **nejméně 2 897 individuálních křížků, 12,10 % všech hlasů**. Součet individuálních minim a minimum celkového součtu nejsou totéž: všech individuálních minim obvykle nelze dosáhnout současně.

Ověřujeme také, zda lze chybějící hlasy každého zkráceného stranického prefixu přiřadit různým kandidátům jiných stran. Používáme celočíselný maximální tok: skupina $(s,k)$ s $N_{sk}$ lístky má požadavek $kN_{sk}$ a hrana ke každému cizímu kandidátu kapacitu $N_{sk}$. Kapacita kandidáta je $C_{si}$. Každý lístek tedy smí označit daného kandidáta nejvýše jednou. Tok lze rozložit do lístků se stejným stupněm $k$; kód tuto konstrukci skutečně provádí a znovu sčítá všech 480 hodnot. Zbylé osobní hlasy lze umístit na čistě jmenné lístky.

U výše uvedených minim tento test i konstrukce procházejí ve všech okrscích. Mez je tedy **dosažitelná při použití pouze dodaných kandidátských agregátů a bez fixace skutečného počtu platných lístků**. Z druhé strany je s týmiž agregáty slučitelné i $S=0,C=H$. Nejde o pravděpodobné alternativy, ale o konstruktivní důkaz nejednoznačnosti. Znalost počtu platných neprázdných lístků by mohla prostor dále omezit; z pouhých procent účasti jej neodhadujeme. Výsledná tabulka `constructive_minimum_witness.csv` není rekonstrukce skutečných voličů.

## 4. Generativní model agregovaných příspěvků

Používáme řádný hierarchický bayesovský model s **celočíselnými latentními počty**. Je to aproximace distribuce agregovaných příspěvků, nikoli tvrzení, že jsme zrekonstruovali pravou pravděpodobnostní distribuci celých lístků.

### Automatická složka

$$N_{psk}\mid b_s,v_{ps},\pi\sim\operatorname{Poisson}(e_p b_s v_{ps}\pi_k),\quad k=0,\ldots,14,$$
$$S_{psi}=\sum_{k=0}^{15-i}N_{psk}.$$

V hlavním modelu $e_p=1$. Všechny okrsky mají samostatné náhodné amplitudy, takže nestejné velikosti či preference nejsou násilně vyrovnány. Náhodný multiplikátor $v_{ps}$ umožňuje overdisperzi počtu stranických lístků. Podmíněně nezávislé přírůstky vytvářejí **korelované** automatické hlasy napříč pořadím; nefitujeme 480 nezávislých Poissonových součtů $H$.

### Individuální složka

$$x_i=(8-i)/14,$$
$$\mu_{psi}=e_p A_s g_{ps}\theta_{si}\exp(\beta x_i),$$
$$\delta_{psi}\sim\operatorname{Gamma}(\phi,\phi),\quad C_{psi}\mid\delta,\mu\sim\operatorname{Poisson}(\mu_{psi}\delta_{psi}).$$

Po integraci $\delta$ dostáváme negativně binomickou distribuci s průměrem $\mu$ a rozptylem $\mu+\mu^2/\phi$ **před omezením společného rozpočtu**. $A_s$ je základ osobních hlasů kandidátky; $g_{ps}$ její okrsková odchylka; $\theta_{si}$ stabilní individuální efekt sdílený mezi okrsky; $\beta$ popisuje asociaci pořadí s osobním označováním. Náhodné $\delta$ zahrnuje lokální popularitu i zbytkovou variabilitu. Z jedné hodnoty na kombinaci kandidát–okrsek tyto dva zdroje nerozlišíme, proto jim nevytváříme dvě zdánlivě identifikované variance.

$\beta$ není kauzální efekt přesunu jména na jiný řádek. Strany řadí kandidáty podle očekávané podpory a dalších nepozorovaných vlastností. Popularita a pozice se proto mohou zaměňovat. Ve výstupu používáme geometricky normalizované $\theta_{si}/\exp(15^{-1}\sum_j\log\theta_{sj})$ jako relativní osobní efekt uvnitř strany. To není standardizovaná celoměstská popularita.

### Priory před omezením

Všude uvádíme Gamma(shape, **rate**):

$$b_s\sim\Gamma(2,2/50),\quad A_s\sim\Gamma(2,2/15),\quad v_{ps},g_{ps}\sim\Gamma(8,8),$$
$$\theta_{si}\mid a\sim\Gamma(a,a),\quad\log a\sim N(\log4,0.6^2),$$
$$\beta\sim N(0,0.7^2),\quad\log\phi\sim N(\log12,0.7^2).$$

$\pi\sim\operatorname{Dirichlet}(\alpha)$ s koncentrací 24. Základní prior průměru má $\pi_0=0.60$; ze zbývající hmoty je 12 % v $k=6,\ldots,14$. V části 1–5 jsou relativní váhy $0.6^{k-1}$, v části 6–14 váhy $0.9^{k-6}$. Všechny kategorie mají kladnou hmotu. Konkrétní tvary a škály jsou **ilustrativní regularizace**, nikoli empiricky změřené chování řevnických voličů. Nebyly nastaveny podle předchozího odhadu 6 884. Proto hlavní výsledek vždy doprovází oddělené alternativní priory. Ani jejich sada nevyčerpává všechny obhajitelné modely.

### Společné omezení: důležitá normalizační poznámka

Pro $L_{ps}=15S_{ps1}-\sum_iS_{psi}$ je nutné

$$15\sum_sS_{ps1}\le T_p,\qquad L_{ps}\le\sum_{t\ne s,i}C_{pti}.$$

Tyto dvě podmínky označíme $F$. Definice celého modelu je

$$q(\Theta,N,C)=Z^{-1}p_0(\Theta)\,p_0(N\mid\Theta)\,p_0(C\mid\Theta)\,\mathbf1_F,$$
$$H=S(N)+C.$$

$Z$ je **jedna globální konstanta**, integrující také parametry. Nejde o model $p_0(\Theta) p_0(N,C\mid\Theta,F)$, který by měl v posterioru navíc parametricky závislý normalizátor. Tato distinkce je zásadní pro správný sampler.

Při prior predictive proto po neúspěchu $F$ losujeme znovu **parametry i počty**. Priory uvedené výše jsou stavební, ne obecně marginální priory po společném omezení. Při posterior predictive držíme posteriorový los parametrů a znovu losujeme počty do splnění $F$. Kód eviduje počet pokusů; posterior predictive nikdy nerecykluje zjištěné $S$ ani pozorované $H$.

Podmínky $F$ jsou nutné, ale samy nejsou kompletním testem realizovatelnosti lístků. Přesný síťový test provádíme dodatečně na předem rovnoměrně vybraných 100 posteriorových losech každého modelu × 4 okrsky a zveřejňujeme i případná selhání. **Úspěch testu realizovatelnosti neznamená správnost pravděpodobnostní váhy daného rozkladu.** Model nepředepisuje distribuci toku jednotlivých voličů mezi listinami. Model je definován pro pevný počet okrsků: společné omezení $F$ může měnit marginální prior parametrů také při změně jejich počtu. Nejde automaticky o projektivní model pro libovolný počet okrsků. Validace níže proto porovnává prediktory znovu naučené na třech okrscích; není prezentována jako přesná LOO log-věrohodnost jednoho čtyřokrskového společného modelu. Rovněž nepodmiňuje na známém počtu platných lístků. Tyto zbývající aproximace zůstávají omezeními i při výborném MCMC a PPC.

### Proč K=15 není zakázáno; nevyužité hlasy

Označení strany při současném označení 15 cizích kandidátů má nulový automatický příspěvek. V datech je totožné s pouhým označením těchto 15 jednotlivců. Proto definujeme $N$ a $\pi$ podmíněně na **účinném** označení strany, $K<15$. Nulově účinná označení nejsou prohlášena za nemožná: jsou součástí nerozlišitelné čistě individuální složky. Tvrzení o $P(K=0)$ nebo ocasu vždy odkazuje na tuto podmíněnou konvenci, nikoli na všechny fyzické křížky v záhlaví lístků.

Samostatná ilustrace nechává podíl těchto nerozlišitelných označení $\psi_{15}\sim\operatorname{Beta}(1,9)$ zcela mimo likelihood. Pak je z definice posterior shodný s priorem; není to odhad jejich reálného počtu. Stejně $u\sim\operatorname{Beta}(2,2)$ pro hypotetické využití čistě osobního lístku, s $E[M]=1+14u$, nemá v této agregované aproximaci identifikující likelihood. Tyto pomocné veličiny **neovlivňují odhady kandidátů**. Netvrdíme, že jsme využití hlasů bayesovsky identifikovali. Jde o explicitně nezodpovězenou část plného modelu lístků. Generátor platných lístků pro stress test přitom skutečně povoluje $K=15$ i čistě osobní lístky s 1–15 hlasy.

## 5. Výpočet posterioru a kontrola implementace

Posterior je úměrný

$$p_0(\Theta)\prod_{psk}\operatorname{Pois}(N_{psk};e_pb_sv_{ps}\pi_k)\prod_{psi}\operatorname{NB}(H_{psi}-S_{psi};\mu_{psi},\phi)\mathbf1_{0\le S\le H}\mathbf1_F.$$

Používáme vlastní **FFBS + Gibbs + Metropolis** sampler, diagnostikovaný v ArviZ. PyMC/NUTS není použit: latentní prefixy jsou diskrétní, mají tvrdou monotonicitu a přesně sdílené hlasy. Spojitá náhrada by neměla stejné celočíselné support a automaticky by nedodržela meze. Vlastní sampler dovoluje přesný blokový tah všech 15 hodnot $S$ při fixovaných parametrech. Volbu nepovažujeme za obecnou výhodu vlastního MCMC: vyžaduje samostatné testy a jejich výsledky dodáváme.

1. Pro každou kombinaci okrsek–strana spočítáme dopředné filtry od posledního kandidáta k prvnímu. Přechody jsou Poissonovy přírůstky a emise NB osobních hlasů. Zpětným vzorkováním získáme společný prefix. Návrh, který poruší $F$, **jednou odmítneme a ponecháme starý stav**; neopakujeme návrhy až do přijetí, což by změnilo invariantní distribuci.
2. Přidáme symetrický celočíselný ridge move: stejné odebrání/přidání plného prefixu u jedné strany v okrscích, kompenzované posunem kandidátských intenzit. Metropolisův poměr zahrnuje Poisson, NB a Gamma prior; translace má jednotkový jakobián.
3. Po těchto marginalizovaných aktualizacích teprve znovu vzorkujeme $\delta$. Podmíněné Gamma/Dirichlet tahy aktualizují amplitudy, efekty a rozdělení $K$.
4. Metropolisovy kroky aktualizují $\beta$, $\log a$, $\log\phi$. Další společný krok $\beta,\theta$ zachovává likelihood a zlepšuje pohyb po konfúzním směru. Protože $\sum_i x_i=0$, odpovídající součin jakobiánů je jedna.
5. Šířky návrhů se adaptují **jen při warmupu**, potom jsou fixní. Každý řetězec má vlastní seed a odlišný přípustný počáteční stav.

Čtyři řetězce jsou skutečně spuštěny. Hlavní běh má 6 000 zahřívacích a 40 000 následných iterací na řetězec; ostatní standardně 6 000 + 20 000, případná prodloužení jsou zapsána v metadatech. Pro kompaktní distribuci ukládáme každou dvacátou pátou iteraci. Sloupec `diagnostic_stride` v souhrnu běhů a metadata určují, zda byla spočtena z plného nebo uloženého řetězce. Thinning není prezentován jako zlepšení efektivní velikosti vzorku.

Sledujeme rank-normalized split $\hat R$, bulk/tail ESS, Monte Carlo standard errors a trace plots [6]. Orientační gate je $\hat R\le1.01$ a obě ESS alespoň 400. Čísla s neprošlým gate jsou označena. **Divergence a BFMI jsou NA**, protože neproběhl Hamiltonovský sampler; nejsou nepravdivě hlášeny jako nula. Základní FFBS test porovnává marginální pravděpodobnost i empirické střední hodnoty s úplným výčtem všech prefixů malého problému.

## 6. Predikce, identifikovatelnost a citlivost

- **Prior predictive:** tabulky i grafy zobrazují rozsah celkových hlasů, osobních podílů a chování pozic před pozorováním. Velké rozsahy jsou vlastností širokých ilustrativních priorů, nikoli údaj o známé účasti.
- **Matched recovery:** jeden syntetický dataset z přesně stejné agregované distribuce se známým $C$. Testuje schopnost zpětného rozkladu v příznivém případě.
- **Ballot stress test:** druhý dataset vzniká ze 4 × 430 skutečně platných syntetických lístků, s výběrem osob bez opakování, lokálními preferencemi, nulovým i patnáctičlenným split-ticket a nevyužitými hlasy. Jde o test modelové nespecifikace.
- **Nejde o SBC kalibraci.** Dva datasety nepostačují k ověření 95% frekvenčního pokrytí. Podíl 120 intervalů obsahujících pravdu v jednom datasetu je popisná diagnostika, s korelovanými kandidáty. Případné selhání se neskrývá ani dodatečně neodstraňuje volbou příznivějšího seedu.
- **Observační ekvivalence:** dva legální mechanismy s přesně stejnými reálnými agregáty a rozdílným $C$ jsou silnější strukturální důkaz nejednoznačnosti než samotná široká posteriorová korelace.
- **Posterior predictive:** nové prefixy a osobní hlasy, zvlášť součty za okrsky, strany, pozice; standardizovaná rezidua a intervaly. In-sample PPC může projít i špatným rozkladem a nenahrazuje recovery.
- **Sedm priorových/likelihood variant:** referenční; důraz na celou stranu; více individuálního hlasování a dlouhý ocas; slabý efekt pořadí; větší individuální heterogenita; silnější pooling; téměř Poissonova osobní složka. Dvě první alternativy mění více předpokladů současně, jejich rozdíl nelze kauzálně připsat jedinému prioru. Ostatní vybrané varianty izolují danou změnu. Každý model má vlastní posterior; jejich mediány ani jejich obálka se neslévají v jeden posterior.
- **Pořadí:** exportujeme posteriorové rozdělení pořadí, pravděpodobnost top 10, rozpětí pořadí mediánů napříč modely a minimum top-10 pravděpodobnosti. „Robustní top 10“ znamená alespoň 0,8 ve všech sedmi variantách; tato hranice je předem zvolený popis, ne statistický test. Slovní závěr o robustní top 10 navíc požaduje kandidátský MCMC gate ve všech variantách; sloupec `all_scenarios_candidate_mcmc_gate_pass` tuto kontrolu zpřístupňuje. Průměrná pořadí řeší shodné celočíselné počty.
- **Out-of-precinct:** postupně vynecháme každý celý okrsek. Tři zbývající trénují model. Předpovídáme rozdělení hlasů mezi 15 lidmi **podmíněně na známém celkovém počtu hlasů dané strany ve vynechaném okrsku**, který je stejně poskytnut všem prediktorům. Prakticky každý prediktivní los vydělíme jeho stranickým součtem a vynásobíme známým testovacím součtem (k buňkám přidáváme 0,01 kvůli případným nulám). Jde o normalizovanou predikci složení, **nikoli přesné podmíněné vzorkování** celého NB/Poissonova modelu při fixovaných součtech. Její 95% intervaly jsou intervaly těchto přepočtených prediktivních losů; jejich empirické pokrytí je kontrola této konkrétní aproximace. Nejde o předpověď účasti ani stranického výsledku. Srovnáváme hierarchické predikce nového okrsku s prostými kandidátskými podíly ve sloučených tréninkových datech a s profilem pouze podle pořadí. Toto je test přidané predikční hodnoty okrskové struktury, nikoli izolovaný experiment o přínosu jediného parametru. Čtyři foldy neopravňují k přesnému odhadu obecné predikční chyby. Výsledek může ukázat i nulový či záporný přínos složitějšího modelu.
- **Starý model:** původní scénářové mediány a 10.–90. percentily jsou importované jen pro srovnání; nebyly použity pro fit. Jejich šířka nemá význam credible interval.

## 7. Interpretace intervalů a omezení

**Pozorovaný fakt:** přesný součet v dodaných volebních datech. **Rigorózní dolní mez:** matematický závěr za uvedených pravidel bez prioru. **Posterior credible interval:** 50 %, 90 % nebo 95 % centrální interval latentních osobních počtů, podmíněný konkrétním modelem a jeho ilustrativními předpoklady. **Predikční interval:** nejistota nově generovaného výsledku. **Rozpětí citlivosti:** rozdíly mezi předem popsanými modely; nemá pravděpodobnostní pokrytí.

Mediány komponent nejsou obecně aditivní. CSV proto obsahuje také posteriorové průměry, u nichž $E[C]+E[S]=H$, a intervaly agregátů počítáme ze součtů v každém losu, nikoli sčítáním konců intervalů kandidátů. Každý uložený los zachovává celočíselnost, $0\le C\le H$, monotonicitu $S$ a oba modelové rozpočty.

Kvalitní MCMC zajišťuje pouze numerickou věrnost zvolenému posterioru. Neprokazuje správnost politologických předpokladů. Ani kvalitní predikce $H$ neprokazuje správný odhad skrytého $C$. Rozptyl popularity, efekt pozice, ocas $K$, amplituda strany a osobních hlasů se mohou kompenzovat. Pořadí je institucionálně zvolené, nikoli randomizované. Kandidátské výsledky 2022 jsou neúplné a dostupné jen pro uvedené srovnávané zastupitele; chybějící hodnoty jsou NA, nikoli nula. Nová kandidátka se graficky označuje jako nová; její 2022 nula znamená neúčast listiny, ne nulovou podporu lidí. Rok 2022 měl dva okrsky: žádné přímé územní párování s čísly čtyř okrsků 2026 neprovádíme. Procenta účasti v podkladových sekundárních souborech nejsou použita jako další nezávislá pozorování; zejména rozpornou účast v okrsku 1 nepoužíváme k výpočtu počtu lístků.

## Bibliografie a provenience

Odkazy ověřovány při zpracování 10. 10. 2026; celý výpočet běží bez sítě.

1. **Portál veřejné správy:** [Volby do zastupitelstev obcí](https://portal.gov.cz/rozcestniky/RZC-118), oddíly úprava lístku a sčítání. Přímo přečteno.
2. **Ministerstvo vnitra:** [Informace v českém znakovém jazyce pro volby do zastupitelstev obcí 2026](https://mv.gov.cz/volby-a-referenda-zakladni/informace-v-ceskem-znakovem-jazyce-pro-volby-do-zastupitelstev-obci-v-roce-2026), text oddílu 04. [Podmínky kandidatury 2026](https://mv.gov.cz/volby-a-referenda-zakladni/kopie-informace-o-podminkach-kandidatury-ve-volbach-do-zastupitelstev-obci-2026), oddíl Hlasovací lístky a způsob hlasování. Přímo přečteno.
3. **Zákon č. 491/2001 Sb.:** [e-Sbírka, znění od 27. 5. 2026](https://e-sbirka.gov.cz/sb/2001/491/2026-05-27?zalozka=text). Aktuální odkaz potvrzen z [přehledu MV](https://mv.gov.cz/volby-referenda/volby-do-zastupitelstev-obci-2); úplné tělo nepřístupné textovému čtení, mechanismus ověřen dle [1,2].
4. **Cho, W. K. T.; Gaines, B. J. (2004).** The Limits of Ecological Inference: The Case of Split-Ticket Voting. *American Journal of Political Science* **48**(1), 152–171. [DOI: 10.1111/j.0092-5853.2004.00062.x](https://doi.org/10.1111/j.0092-5853.2004.00062.x). Ověřena bibliografie a abstrakt na [institucionálním záznamu Illinois](https://experts.illinois.edu/en/publications/the-limits-of-ecological-inference-the-case-of-split-ticket-votin/); přímý DOI resolver se nenačetl. Plný text nebyl dostupný, detailní obsah netvrdíme.
5. **Park, W.-h.; Hanmer, M. J.; Biggers, D. R. (2014).** Ecological inference under unfavorable conditions: Straight and split-ticket voting in diverse settings and small samples. *Electoral Studies* **36**, 192–203. [DOI: 10.1016/j.electstud.2014.08.006](https://doi.org/10.1016/j.electstud.2014.08.006). Ověřen [plný autorský PDF na University of Maryland](https://gvpt.umd.edu/sites/gvpt.umd.edu/files/pubs/Park%20Hanmer%20Biggers%20ES%20Ecological%20Inference%20Under%20Unfavorable%20Conditions.pdf).
6. **Vehtari, A.; Gelman, A.; Simpson, D.; Carpenter, B.; Bürkner, P.-C. (2021).** Rank-normalization, folding, and localization: An improved R-hat for assessing convergence of MCMC. *Bayesian Analysis* **16**(2), 667–718. [DOI: 10.1214/20-BA1221](https://doi.org/10.1214/20-BA1221); [institucionální záznam](https://research.aalto.fi/en/publications/rank-normalization-folding-and-localization-an-improved-r-hat-for/).
7. **Software:** [ArviZ 0.22 dokumentace](https://python.arviz.org/en/v0.22.0/), [negativně binomická parametrizace PyMC](https://www.pymc.io/projects/docs/en/stable/api/distributions/generated/pymc.NegativeBinomial.html), [Plotly Python](https://plotly.com/python/), [GitHub – zobrazení notebooků](https://docs.github.com/en/repositories/working-with-files/using-files/working-with-non-code-files). PyMC je metodický odkaz, nikoli použitý inference backend. Verze skutečně použitých balíčků jsou připnuty v requirements.txt.
8. **ČSÚ:** [Řevnice 2026](https://volby.gov.cz/app/kv2026/cs/20261009/results/!___2100_2110_539643). Primárním vstupem jsou beze změny dodané CSV exporty, jejichž SHA-256 manifest je součástí projektu. [Podmínky použití dat](https://csu.gov.cz/podminky_pro_vyuzivani_a_dalsi_zverejnovani_statistickych_udaju_csu): zveřejněné statistické informace jsou CC BY 4.0, vyžadují atribuci a označení odvozených údajů. Neudělujeme novou licenci jménem ČSÚ.
9. **Kaňok, David:** odkaz z předávacího balíčku na práci *Analýza preferenčního hlasování ve volbách do zastupitelstev obcí v letech 2006–2018*, [theses.cz/id/id9d17](https://theses.cz/id/id9d17/). Cílová stránka neposkytla čitelný obsah; práci ani její závěry jsme nepoužili jako ověřený podklad.
