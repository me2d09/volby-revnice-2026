# Řevnice 2026: model individuálních křížků (citlivostní analýza)

## Data
Vstup: osm uživatelem exportovaných CSV z detailních výsledků ČSÚ, dohromady 120 kandidátů po 15 osobách na kandidátce. Součet 23 939 kandidátských hlasů.

## Přesná mechanika započítávání
Je-li zakřížkována jedna kandidátka a zároveň *k* jednotlivých kandidátů jiných kandidátek, zbývajících `15-k` hlasů se přidělí kandidátům označené kandidátky od jejího prvního místa. Při samostatných křížcích bez označení celé kandidátky dostává každý označený kandidát jeden hlas. Počty výsledných hlasů ČSÚ nerozlišují původ hlasu.

## Identifikovatelnost
Počet automaticky přidělených stranických hlasů S_{s,i} je s pořadím i neklesající? **Nikoli: je nerostoucí.** Z toho plyne matematické minimum pro osobní křížky kandidáta i: `max(0, H_{s,i} - min(H_{s,1},...,H_{s,i}))`. Přesné množství osobních křížků z těchto agregovaných údajů odvodit NELZE. Model je scénářový, nikoli empiricky kalibrovaný průzkumem.

## Struktura modelu
`H_{s,i} = B_s * Pr(K <= 15-i) + I_{s,i}`:
- `B_s` latentní počet hlasovacích lístků se zakřížkovanou kandidátkou s a nejvýše 14 jednotlivými křížky jinde (lístky, kde by strana nedostala vůbec žádný hlas, model nezachycuje).
- `K` počet jednotlivých křížků na kandidátech jiných listin při označené kandidátce.
- `I_{s,i}` latentní počet individuálních křížků pro kandidáta i.
- očekávané individuální křížky po pozici jsou úměrné `exp(-beta * (i-1)/14)`, koeficient `beta` se fituje společně napříč osmi kandidátkami. Neříká to, že všichni voliči preferují první místa; připouští výrazné osobní výjimky.
- Reálné odchylky osobní popularity se aproximují heteroskedastickým Gaussovým kvazilikelihoodem s variancí `mu + (sigma * mu)^2`, `sigma` v rozsahu 0,35–0,65. Počet hlasů kandidátky se zachovává přesně a odhady individuálních křížků jsou nezáporné.

## 45 scénářů (rovnoměrně prezentovaných, ne posterior)
- Podíl `K=0` mezi lístky s označenou kandidátkou: 30 %, 45 %, 60 %, 75 %, 85 %.
- Rozdělení `K=1..14` podmíněné `K>0`: tři geometricky klesající tvary s poměrem sousedních četností `0,54`, `0,69`, `0,81`. To dovoluje i 11–14 křížků. Nejsou zakázány, pouze méně obvyklé podle předpokladu.
- Kandidátská různorodost `sigma`: 0,35, 0,50, 0,65.
- Pro každý scénář fit společného sklonu osobních preferencí dle pořadí `beta` a pro každou kandidátku fit počtu `B_s` s fyzikálním omezením `I_{s,i}>=0`.

Každý scénář má stejnou váhu *pro demonstraci citlivosti*. Výsledný medián a 10.–90. percentil mezi scénáři nejsou věrohodnostní intervaly ani pravděpodobnostní intervaly. Pokud zvolíme jiné předpoklady, odhady se mohou výrazně změnit.

## Dvě odlišné metriky
- `model_median_krizku`: odhad celkového počtu individuálních křížků, zahrnuje výhodu přímého označení osobností z předních míst.
- `nad_ocekavani_median`: odhad osobních křížků *navíc proti průměrnému kandidátovi téhož uskupení na dané pozici*; lépe ukazuje individuální výjimky. Nezaměňovat s matematicky prokazatelným minimem.

## Hlavní výsledky
- Celkem 6 884 modelových individuálních křížků při mediánu 45 scénářů (28,8 % kandidátských hlasů); 10.–90. percentil 5 462–9 935 (22,8–41,5 %).
- Terezie Červená (10., ŠANCE): 383 celkem, jistě nejméně 83 křížků; modelový medián 126 (10.–90. percentil 107–158); přebytek osobní popularity vůči očekávání +68.
- Pavel Hartmann (TOP 09): modelový medián 170; přebytek +85.
- Libor Kvasnička (PRO): modelový medián 168; přebytek +80.
- Martina Štěpánková (DOBŘE): modelový medián 197; přebytek +70.

## Co by pomohlo přesnosti
1. Získat všech 120 kandidátských výsledků zvlášť za každý ze čtyř okrsků (480 řádků), aby se zohlednila prostorová variabilita a částečně ověřilo chování modelu mimo vzorek.
2. Kalibrovat předpoklady o počtu křížků z anonymního povolebního dotazování či zvláštního agregovaného šetření počtu typů hlasovacích lístků v podobně velkých městech.
3. Porovnat robustnost s méně parametrickým modelem, modely bayesovskými s informativními apriorními pravděpodobnostmi a provést simulace s předem známou pravdou.

## Odkazy
- Český statistický úřad: metodika hlasování https://mv.gov.cz/volby/clanek/hlasovani-a-scitani-hlasu-odlisnosti-od-jinych-voleb-736167.aspx
- David Kaňok, diplomová práce: *Analýza preferenčního hlasování ve volbách do zastupitelstev obcí v letech 2006–2018*, https://theses.cz/id/id9d17/
- Tam Cho & Gaines (2004), *The Limits of Ecological Inference: The Case of Split-Ticket Voting*, AJPS, DOI 10.1111/j.0092-5853.2004.00062.x
- Park, Hanmer & Biggers (2014), *Ecological inference under unfavorable conditions: Straight and split-ticket voting in diverse settings and small samples*, Electoral Studies, DOI 10.1016/j.electstud.2014.08.006

## Výstupy
- `revnice_model_osobnich_krizku_120.csv`: 120 kandidátů, přesné hlasy, jisté minimum, modelové odhady a scénářová rozpětí, přebytek proti očekávání.
- `revnice_model_souhrn_8_stran.csv`: agregace osmi kandidátek.
- `revnice_model_45_scenaru.csv`: předpoklady scénářů a souhrn.
- `revnice_model_krizku.py`: kompletní reprodukovatelný výpočet, vyžaduje Python, numpy, pandas, scipy.
