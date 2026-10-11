#!/usr/bin/env python3
"""Transparent sensitivity model for 2026 Revnice municipal personal marks.

These results are SCENARIO estimates, NOT identification of actual individual crosses.
No nationally calibrated ballot-splitting distribution available; vary untestable assumptions.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from itertools import product

src='/mnt/data/revnice_pref_candidates.csv'
data=pd.read_csv(src,sep=';')
data=data.sort_values(['party','position']).reset_index(drop=True)
parties=['ŠANCE','TOP 09','DOBŘE','Srdce','PRO','ODS','Perspektiva','Naše Řevnice']
Y=np.vstack([data[data.party==p].sort_values('position')['votes'].values for p in parties]).astype(float)
N=15; POS=np.arange(N)

# Three plausible non-zero cross-count distributions; no empirically measured calibration.
def pos_weights(tail):
 k=np.arange(1,15)
 if tail=='short': w=(0.54)**(k-1)
 elif tail=='medium': w=(0.69)**(k-1)
 elif tail=='long': w=(0.81)**(k-1)
 else: raise ValueError(tail)
 return w/w.sum()

def survival(p0,tail):
 q=np.r_[p0,(1-p0)*pos_weights(tail)]
 # j-th list position is credited whenever number of marks outside its list <=15-j
 return np.array([np.sum(q[:16-j]) for j in range(1,16)])

def loss_for_b(B,y,q,shape,bias):
 # Gaussian quasi-likelihood with candidate-to-candidate overdispersion.
 C=y-B*q
 if C.min() < -1e-6: return 1e12
 mu=C.sum()*shape/shape.sum()
 v=mu+(bias*mu)**2
 return np.sum((C-mu)**2/v + np.log(v))*0.5

def fit_one(y,q,shape,bias):
 hi=np.min(y/q)
 fit=minimize_scalar(loss_for_b,args=(y,q,shape,bias),bounds=(0,hi),method='bounded',options={'xatol':1e-6})
 B=fit.x
 crosses=y-B*q
 return B,crosses,fit.fun

all_runs=[]
# 5x3x3=45 sensitivity runs; each global position profile fitted from the whole dataset.
for p0,tail,bias in product([.30,.45,.60,.75,.85],['short','medium','long'],[.35,.50,.65]):
 q=survival(p0,tail)
 def f(beta):
  shape=np.exp(-beta*POS/14.)
  return sum(fit_one(y,q,shape,bias)[2] for y in Y)
 best=minimize_scalar(f,bounds=(np.log(1.25),np.log(5.0)),method='bounded',options={'xatol':1e-4})
 beta=best.x
 shape=np.exp(-beta*POS/14.)
 for p,y in zip(parties,Y):
  B,c,loss=fit_one(y,q,shape,bias)
  for i,(v,personal) in enumerate(zip(y,c),1):
   all_runs.append({'scenar_p0':p0,'scenar_ocas':tail,'scenar_variabilita':bias,'faktor_pozice':round(float(np.exp(beta)),3),'strana':p,'pozice':i,'celkove_hlasy':int(v),'model_krizky':personal,'model_stranicke_hlasy':B*q[i-1],'model_oznaceni_strany':B,'model_ztrata_listovych_hlasu':B*(1-q[i-1])})
runs=pd.DataFrame(all_runs)

out=[]
for p in parties:
 srcp=data[data.party==p].sort_values('position').reset_index(drop=True)
 arr=Y[parties.index(p)]
 for i in range(1,16):
  sub=runs[(runs.strana==p)&(runs.pozice==i)]
  exactlb=int(max(0,arr[i-1]-arr[:i].min()))
  mm=np.quantile(sub.model_krizky,[0,.1,.5,.9,1])
  out.append({'strana':p,'poradi_na_kandidatce':i,'kandidat':srcp.loc[i-1,'name'], 'hlasy_csu':int(arr[i-1]), 'matematicky_jiste_minimum_krizku':exactlb,
              'model_median_krizku':round(float(mm[2]),1),'model_rozpeti_10pct':round(float(mm[1]),1),'model_rozpeti_90pct':round(float(mm[3]),1),
              'model_min_ve_scenarich':round(float(mm[0]),1),'model_max_ve_scenarich':round(float(mm[-1]),1),'model_median_podil_osobnich_pct':round(float(mm[2]/arr[i-1]*100),1)})
candidates=pd.DataFrame(out)

party_summary=[]
for p in parties:
 sub=runs[runs.strana==p]
 group=sub.groupby(['scenar_p0','scenar_ocas','scenar_variabilita'],sort=False)
 totalcross=group.model_krizky.sum().values
 partyballots=group.model_oznaceni_strany.mean().values
 forwhat={'strana':p,'hlasy_csu':int(Y[parties.index(p)].sum()),'minimum_krizku_prokazatelne':int(candidates[candidates.strana==p].matematicky_jiste_minimum_krizku.sum()),'model_krizky_median':round(float(np.median(totalcross)),1),'model_krizky_10pct':round(float(np.quantile(totalcross,.1)),1),'model_krizky_90pct':round(float(np.quantile(totalcross,.9)),1),'model_podil_krizku_pct_median':round(float(np.median(totalcross)/Y[parties.index(p)].sum()*100),1),'model_oznaceni_strany_median':round(float(np.median(partyballots)),1),'model_oznaceni_strany_10pct':round(float(np.quantile(partyballots,.1)),1),'model_oznaceni_strany_90pct':round(float(np.quantile(partyballots,.9)),1)}
 party_summary.append(forwhat)
partysummary=pd.DataFrame(party_summary)

total_by_scenario=runs.groupby(['scenar_p0','scenar_ocas','scenar_variabilita']).agg({'model_krizky':'sum','model_oznaceni_strany':'sum','faktor_pozice':'first'}).reset_index()
# Model party marking count sum needs /15, since each party's count repeated across all 15 list positions.
total_by_scenario['model_oznaceni_strany']/=15

candidates.to_csv('/mnt/data/revnice_model_osobnich_krizku_120.csv',sep=';',index=False,encoding='utf-8-sig')
partysummary.to_csv('/mnt/data/revnice_model_souhrn_8_stran.csv',sep=';',index=False,encoding='utf-8-sig')
total_by_scenario.to_csv('/mnt/data/revnice_model_45_scenaru.csv',sep=';',index=False,encoding='utf-8-sig')

if __name__=='__main__':
 print('Scenarios:',len(total_by_scenario))
 print('total individual crosses median, 10-90',np.quantile(total_by_scenario.model_krizky,[.1,.5,.9]),'as fraction',np.quantile(total_by_scenario.model_krizky,[.1,.5,.9])/23939)
 print('sum party ballots median, 10-90',np.quantile(total_by_scenario.model_oznaceni_strany,[.1,.5,.9]))
 print('position multiplier top to bottom 10-90',np.quantile(total_by_scenario.faktor_pozice,[.1,.5,.9]))
 print('\nParty summary\n',partysummary.to_string(index=False))
 print('\nHighest estimated personal crosses\n',candidates.sort_values('model_median_krizku',ascending=False).head(24).to_string(index=False))
 print('\nElected focus\n',candidates[candidates.kandidat.str.contains('Červená|Štěpánková|Chabera|Lojda|Smrčka|Hartmann|Masner|Martinec|Kvasnička|Soukupová|Čermák')].to_string(index=False))
