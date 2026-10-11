#!/usr/bin/env python3
"""Prepare and cross-check 2026 precinct candidate CSVs, using only Python stdlib.

Usage (from repository root): python scripts/prepare_and_validate.py
No network access; inputs are preserved unmodified under data/raw/.
"""
from pathlib import Path
import csv
import io
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'processed'
OUT.mkdir(parents=True,exist_ok=True)

PARTIES = {
 1:'ŠANCE Řevnice',
 2:'TOP 09 a nezávislí kandidáti',
 3:'DOBŘE - Dialog o budoucnosti Řevnic',
 4:'Hnutí Srdce Řevnic',
 5:'PRO Řevnice',
 6:'ODS a nezávislí',
 7:'Perspektiva pro město',
 8:'Naše Řevnice',
}

def clean(s):
    return re.sub(r'\s+', ' ', s.replace('\u200b','').replace('\u2060','').replace('\ufeff','')).strip()

def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f,delimiter=';'))

def write_csv(path,fields,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=fields,delimiter=';')
        wr.writeheader(); wr.writerows(rows)

precinct=[]
raw_sources=[]
with zipfile.ZipFile(RAW/'okrsky_2026_csu_exports.zip') as z:
    names=[n for n in z.namelist() if n.endswith('.csv')]
    assert len(names)==32, f'Expected 32 precinct CSVs, found {len(names)}'
    for filename in sorted(names):
        m=re.fullmatch(r'([1-4])/data-export \(([1-8])\)\.csv', filename)
        assert m, f'Unexpected filename {filename!r}'
        precinct_id,party_id=map(int,m.groups())
        with io.StringIO(z.read(filename).decode('utf-8-sig')) as f:
            records=list(csv.DictReader(f,delimiter=';'))
        assert len(records)==15, (filename,len(records))
        for expect,r in enumerate(records,1):
            pos=int(r['Kandidát.číslo'])
            assert pos==expect, (filename,pos,expect)
            v=int(r['Počet hlasů.abs.'])
            pct=float(r['Počet hlasů.v %'].replace(',','.'))
            precinct.append({'year':2026,'precinct':precinct_id,'party_id':party_id,'party':PARTIES[party_id],
                             'position':pos,'name':clean(r['Kandidát.příjmení, jméno, tituly']),
                             'age':int(r['Kandidát.věk']),'votes':v,'pct_of_party_precinct':pct,
                             'source_file':filename})
        raw_sources.append(filename)
assert len(precinct)==480

old_city=read_csv(RAW/'candidates_2026_city_original_analysis.csv')
assert len(old_city)==120, len(old_city)
city=[]
for r in old_city:
    p = next(k for k,v in PARTIES.items() if {'ŠANCE':'ŠANCE Řevnice','TOP 09':'TOP 09 a nezávislí kandidáti','DOBŘE':'DOBŘE - Dialog o budoucnosti Řevnic','Srdce':'Hnutí Srdce Řevnic','PRO':'PRO Řevnice','ODS':'ODS a nezávislí','Perspektiva':'Perspektiva pro město','Naše Řevnice':'Naše Řevnice'}[r['party']]==v)
    city.append({'year':2026,'party_id':p,'party':PARTIES[p],'position':int(r['position']),
                 'name':clean(r['name']),'age':int(r['Kandidát.věk']),'votes':int(r['votes']),
                 'elected_2026':r['Mandát'],'elected_order':r['Pořadí']})

lookup={(r['party_id'],r['position']):r for r in city}
assert len(lookup)==120
from collections import defaultdict
sums=defaultdict(int)
for r in precinct:
    reference=lookup[(r['party_id'],r['position'])]
    assert (r['name'],r['age'])==(reference['name'],reference['age']), (r,reference)
    sums[(r['party_id'],r['position'])]+=r['votes']
for pair,sumvotes in sums.items():
    assert sumvotes==lookup[pair]['votes'], (pair,sumvotes,lookup[pair]['votes'])

official_parties=read_csv(RAW/'strany_2022_2026.csv')
expected={r['strana']:int(r['hlasy_2026']) for r in official_parties if int(r['hlasy_2026'])>0}
party_totals={k:sum(sums[k,i] for i in range(1,16)) for k in PARTIES}
for k,tot in party_totals.items():
    assert tot==expected[PARTIES[k]], (PARTIES[k],tot,expected[PARTIES[k]])
assert sum(party_totals.values())==23939

old_precinct=read_csv(RAW/'okrsky_2026_party.csv')
expected_precinct={(int(r['okrsek']),r['strana']):int(r['hlasy']) for r in old_precinct}
precinct_party_totals=defaultdict(int)
for r in precinct: precinct_party_totals[(r['precinct'],r['party'])]+=r['votes']
assert len(precinct_party_totals)==32
for key,v in precinct_party_totals.items():
    assert v==expected_precinct[key], (key,v,expected_precinct[key])

# Recompute model-free (exact) lower bound candidate personal votes.
# If list-derived votes are non-increasing with candidate position,
# personal_i >= max(0, votes_i - min(votes_1...votes_i)).
precinct_out=[]
for p in range(1,5):
    for party_id in PARTIES:
        runmin=None
        block=sorted((r for r in precinct if r['precinct']==p and r['party_id']==party_id),key=lambda r:r['position'])
        for r in block:
            runmin=r['votes'] if runmin is None else min(runmin,r['votes'])
            precinct_out.append(dict(r, rigorous_min_personal_marks=max(0,r['votes']-runmin)))

city_out=[]
for party_id in PARTIES:
    runmin=None
    block=sorted((r for r in city if r['party_id']==party_id),key=lambda r:r['position'])
    for r in block:
        runmin=r['votes'] if runmin is None else min(runmin,r['votes'])
        precinct_lb=sum(x['rigorous_min_personal_marks'] for x in precinct_out if x['party_id']==party_id and x['position']==r['position'])
        city_out.append(dict(r,rigorous_min_personal_marks_city=max(0,r['votes']-runmin),
                             rigorous_min_personal_marks_sum_precincts=precinct_lb))

write_csv(OUT/'precinct_candidates_2026.csv',list(precinct_out[0]),precinct_out)
write_csv(OUT/'city_candidates_2026.csv',list(city_out[0]),city_out)
print('VALIDATION PASSED')
print(f'Files: {len(raw_sources)}, precinct candidate observations: {len(precinct_out)}, candidates: {len(city_out)}, total votes: {sum(party_totals.values())}')
print('Party totals:')
for k,tot in party_totals.items(): print(f' {k} {PARTIES[k]}: {tot}')
print('Precinct candidate vote totals:',{p:sum(r['votes'] for r in precinct if r['precinct']==p) for p in range(1,5)})
print('Exact minimum city-only:',sum(r['rigorous_min_personal_marks_city'] for r in city_out))
print('Exact minimum with precinct observations:',sum(r['rigorous_min_personal_marks_sum_precincts'] for r in city_out))
print('Terezie Červená:')
for r in precinct_out:
 if 'Červená Terezie' in r['name']:
  print(' precinct',r['precinct'],'votes',r['votes'],'minimum',r['rigorous_min_personal_marks'])

with (OUT/'validation_summary.json').open('w',encoding='utf-8') as f:
    json.dump({'n_precinct_csv':len(raw_sources),'n_precinct_records':len(precinct_out),'n_candidates':len(city_out),'total_votes':sum(party_totals.values()),
     'party_totals':{PARTIES[k]:v for k,v in party_totals.items()},
     'precinct_totals':{str(p):sum(r['votes'] for r in precinct if r['precinct']==p) for p in range(1,5)},
     'rigorous_city_min':sum(r['rigorous_min_personal_marks_city'] for r in city_out),
     'rigorous_precinct_min':sum(r['rigorous_min_personal_marks_sum_precincts'] for r in city_out)},f,indent=2,ensure_ascii=False)
