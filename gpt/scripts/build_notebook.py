from pathlib import Path
import nbformat as nbf
root=Path(__file__).resolve().parents[1]
nb=nbf.v4.new_notebook();cells=[]
def md(s):cells.append(nbf.v4.new_markdown_cell(s))
def code(s):cells.append(nbf.v4.new_code_cell(s))
method=(root/'methodology.md').read_text()
def section(a,b):return method.split(a,1)[1].split(b,1)[0]
md('''# Řevnice 2026\n## Co lze zjistit o osobních křížcích\n\n**4 okrsky · 8 kandidátek · 120 osob · 23 939 kandidátských hlasů**\n\nVýzkumná analýza s celočíselným hierarchickým bayesovským modelem. Rozlišujeme **pozorované výsledky**, **rigorózní dolní meze** a **modelové odhady**. Neznáme individuální lístky. Modelové intervaly nepokrývají automaticky chybu předpokladů.\n\nTento skutečně spuštěný notebook doprovázejí CSV, MCMC vzorky, PNG/SVG a offline Plotly průzkumníci. Batch ověření používá čisté skutečné jádro ipykernel v novém Python procesu, v režimu in-process bez socketů. Standardní TCP/IPC spojení kernelu bylo v tomto prostředí blokováno; podrobnosti a volitelný TCP režim jsou v README. Pro nové spuštění ponechte notebook vedle `src/` a `data/`. Samostatný náhled zachovává uložené výsledky.\n\n**Čtenářská trasa:** data a pravidla → meze → model → diagnostika → kandidáti → citlivost a recovery → okrsky a historie → závěry. [Metodika](methodology.md) · [Původ dat](DATA_SOURCES.md) · [Spuštění](README.md)''')
code('''from pathlib import Path
import os,sys,json,subprocess,time
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")
os.environ.setdefault("OMP_NUM_THREADS","1")
ROOT=Path.cwd()
assert (ROOT/"src/model.py").exists(), "Spusťte v kořeni rozbaleného projektu."
import numpy as np,pandas as pd
from IPython.display import display,Image,Markdown,IFrame
from src.experiments import load_data,execute_suite
from src.report import compile_results
from src.visuals import make_figures,make_interactive
from src.findings import write_findings
pd.set_option("display.max_columns",18)
pd.set_option("display.max_rows",25)
def table(name):return pd.read_csv(ROOT/"results"/name,sep=";")
def figure(name,width=1000):display(Image(filename=str(ROOT/"figures"/(name+".png")),width=width))
print("Python",sys.version.split()[0],"NumPy",np.__version__)
''')
md('## 1. Data a jejich ověření\n'+section('## 1. Úloha a význam čísel','## 2. Ověřená pravidla'))
code('''result=subprocess.run([sys.executable,"scripts/prepare_and_validate.py"],text=True,capture_output=True,check=True)
print(result.stdout)
H,observations,city=load_data()
display(city[["party","position","name","votes","rigorous_min_personal_marks_sum_precincts"]].head(12))
''')
md('## 2. Pravidla a přesné matematické meze\n'+section('## 2. Ověřená pravidla a rozsah ověření','## 4. Generativní model'))
code('''from src.bounds import budget_bound,audit_flow,legal_ballots
bounds=[]
for p in range(4):
    low,S_witness=budget_bound(H[p])
    S_check,C_check,synthetic_ballots=legal_ballots(H[p],S_witness)
    assert np.array_equal(H[p],S_check+C_check)
    bounds.append({"okrsek":p+1,"bodové minimum":int((H[p]-np.minimum.accumulate(H[p],axis=-1)).sum()),"silnější minimum":low,"síťový test":bool(audit_flow(H[p],S_witness)["feasible"])})
display(pd.DataFrame(bounds))
assert sum(r["silnější minimum"] for r in bounds)==2897
print("Nejméně 2 897 osobních křížků =",round(2897/H.sum()*100,2),"% hlasů")
''')
md('## 3. Generativní model a priory\n'+section('## 4. Generativní model agregovaných příspěvků','## 5. Výpočet posterioru'))
code('''from src.model import SCENARIOS
prior_table=pd.DataFrame(SCENARIOS).T
prior_table["prior_typical_candidate_sd"]=np.exp(-prior_table.a_logmean/2)
display(prior_table)
''')
md('## 4. Skutečné MCMC a nezávislé kontroly\n'+section('## 5. Výpočet posterioru a kontrola implementace','## 6. Predikce, identifikovatelnost'))
md('''Následující buňka ověří fingerprinty dat, modelu a nastavení a doplní chybějící výpočty. Přiložené vzorky byly skutečně vygenerovány. Pro nové spuštění všech řetězců změňte `REFIT=True`. Délky běhů i případná prodloužení jsou v `run_config.json`. Celý výpočet funguje bez externích API; cache šetří čekání při znovuotevření projektu.''')
code('''test=subprocess.run([sys.executable,"-m","pytest","-q","tests"],text=True,capture_output=True,check=True)
print(test.stdout)
REFIT=False
started=time.perf_counter()
fits=execute_suite(force=REFIT)
print("Řízení MCMC/cachí:",round(time.perf_counter()-started,1),"s")
del fits
''')
md('''## 5. Přepočet výsledků\n\nZ posteriorových vzorků znovu vytváříme CSV, prior predictive, PPC, síťové audity, vyhodnocení recovery a všechny grafy. 50/90/95% intervaly jsou centrální. Součty počítáme v každém losu zvlášť; nesčítáme mediány ani konce intervalů.''')
code('''results=compile_results()
make_figures()
make_interactive()
findings_text=write_findings()
print("Vytvořena výsledná CSV, statické PNG/SVG a tři offline interaktivní HTML.")
''')
md('''## 6. Pozorované výsledky a okrsky\n\nNásledující grafy zobrazují data. Stranické součty zahrnují všechny hlasy připsané kandidátům bez ohledu na způsob označení lístku. Čísla okrsků nelze geograficky párovat s rokem 2022.''')
code('''figure("01_party_results")
figure("02_precinct_heatmap")
figure("03_position_profiles")
''')
md('''## 7. Prior predictive a diagnostika řetězců\n\nPrvní graf je simulace před daty, po společném rozpočtovém omezení. Dále uvádíme všechny skutečné běhy včetně případných neprošlých diagnostických hranic. Divergence a BFMI jsou NA pro nehamiltonovský sampler, nikoli domnělá nula.''')
code('''figure("08_prior_predictive")
display(table("prior_predictive_checks.csv"))
display(table("mcmc_run_summary.csv")[["label","draws_per_chain","diagnostic_stride","wall_seconds","max_rhat","min_ess_bulk","min_ess_tail","mcmc_gate_pass","divergences"]])
display(table("diagnostic_flags.csv")[["run","parameter","r_hat","ess_bulk","ess_tail"]])
figure("09_mcmc_traces")
''')
md('''## 8. Všech 120 kandidátů a složení hlasů\n\nBarevné intervaly jsou modelové; černé značky jsou rigorózní bodová minima. Pozičně očištěný efekt je relativní uvnitř strany. Samotný vysoký součet na čele silné listiny neurčuje její osobní složku. Intervaly pořadí vyjadřují další nejistotu.''')
code('''candidates=table("candidate_estimates.csv")
display(candidates.nlargest(20,"personal_median")[["name","party","position","votes","rigorous_min_personal_marks_sum_precincts","personal_median","personal_q025","personal_q975","rank_q025","rank_q975","min_scenario_p_top10"]])
figure("04_candidate_intervals",width=1200)
figure("05_decomposition")
figure("06_precinct_contributions")
''')
md('''### Interaktivní průzkumníci\n\nŽivý Jupyter zobrazí lokální HTML níže. Lze filtrovat stranu, vyhledat jméno a projít všechny osoby. Na GitHubu použijte statické grafy nebo stáhněte `interactive/candidates.html` a `interactive/candidate_detail.html` a otevřete v prohlížeči. Soubory obsahují Plotly přímo a nepotřebují připojení.''')
code('''SHOW_INTERACTIVE=True
if SHOW_INTERACTIVE:
    display(IFrame("interactive/candidates.html",width="100%",height=1000))
    display(IFrame("interactive/candidate_detail.html",width="100%",height=1000))
''')
md('''## 9. Citlivost a identifikovatelnost\n\nKaždá priorová nebo likelihood varianta má vlastní posterior. Rozpětí mezi nimi není další credible interval. Starý scénářový medián 6 884 není kalibrační cíl. Pomocné veličiny K=15 a využití hlasů nejsou tímto likelihoodem odhadovány.''')
code('''display(table("prior_sensitivity.csv"))
figure("07_prior_sensitivity")
figure("15_identifiability")
display(table("nonidentified_parameters.csv"))
display(table("old_baseline_comparison.csv").nlargest(12,"difference_medians"))
''')
md('''## 10. Predikční kontroly a známá pravda\n\nPPC losuje znovu automatickou i osobní složku. Recovery testuje jeden vzorek z téhož agregovaného modelu a jeden z odlišného generátoru platných lístků, s výběrem bez opakování, K=0..15 a nevyužitými hlasy. Dva experimenty nejsou formální SBC kalibrace. Jejich selhání je relevantní i při dobrém in-sample fitu.''')
code('''figure("10_posterior_predictive")
figure("11_residuals")
display(table("ppc_grouped_reference.csv"))
display(table("synthetic_recovery.csv"))
figure("12_recovery")
audit=table("ballot_feasibility_audit.csv")
display(audit.groupby("model").agg(tested=("feasible","size"),passed=("feasible","sum"),maximum_deficit=("deficit","max")))
''')
md('''## 11. Predikce vynechaného okrsku\n\nKaždý okrsek je jednou celý vynechán z trénování. Všechny metody dostávají stejný známý stranický součet v testovacím okrsku; odhadují jeho rozdělení mezi lidi. Srovnání s městským sloučením a profilem pouze podle pozice proto není předpověď účasti ani důkaz správnosti skrytého osobního rozkladu. Losy nového okrsku se normalizují na známé stranické součty; nejde o přesné podmíněné vzorkování původního NB/Poissonova modelu. Máme jen čtyři foldy.''')
code('''display(table("out_of_precinct_validation.csv"))
figure("13_out_of_precinct")
''')
md('''## 12. Změny proti 2022\n\nPorovnáváme městské údaje a osoby s dostupným historickým záznamem. DOBŘE je nová listina; chybějící kandidátský údaj je NA, nikoli nula. Změny procent nejsou přesuny identifikovaných voličů.''')
code('''figure("14_changes_2022_2026")
display(table("elected_comparison.csv"))
''')
md('''## 13. Kontrola výsledných rozkladů\n\nNásledující assertions ověřují support všech uložených referenčních losů. Nejsou náhradou za konvergenci, recovery nebo posouzení modelových předpokladů.''')
code('''from src.report import load_fit,flatten
posterior=load_fit("reference",H)
C=flatten(posterior["C"])
assert np.issubdtype(C.dtype,np.integer)
assert np.all((C>=0)&(C<=H))
assert np.all(C>=H-np.minimum.accumulate(H,axis=-1))
assert np.all(np.diff(H-C,axis=-1)<=0)
assert np.all(C.sum(axis=(1,2,3))>=2897)
assert len(candidates)==120
assert (ROOT/"interactive/candidate_detail.html").stat().st_size>1000000
print("PASS: celočíselné rozklady, přesné součty, monotonicita, meze, 120 kandidátů a offline HTML.")
''')
md('## 14. Zjištění běžnou češtinou\n\nVygenerováno ze skutečně spočtených výsledků; typ tvrzení je vždy uveden.')
code('display(Markdown(findings_text))')
md('## Přesný rozsah validačních tvrzení\n'+section('## 6. Predikce, identifikovatelnost a citlivost','## Bibliografie a provenience'))
md('## Bibliografie a dostupnost zdrojů\n'+method.split('## Bibliografie a provenience',1)[1])
nb['cells']=cells;nb['metadata']={'kernelspec':{'display_name':'Python 3 (Řevnice)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12.14'}}
nbf.write(nb,root/'revnice_2026_bayesian_analysis.ipynb');print('Notebook created:',len(cells),'cells')
