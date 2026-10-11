"""Reproducible fits, simulation experiments and diagnostics, with content-checked caches."""
from pathlib import Path
import hashlib,json,time,platform,sys
import numpy as np,pandas as pd
import arviz as az
from scipy.stats import rankdata
from .model import fit,save_fit,to_arviz,predictive,sample_prior,SCENARIOS,pi_alpha
from .bounds import budget_bound,audit_flow,legal_ballots

ROOT=Path(__file__).resolve().parents[1]

def write_csv(df,path):
    df.to_csv(path,sep=';',encoding='utf-8-sig',index=False,float_format='%.6f')

def load_data(root=ROOT):
    obs=pd.read_csv(root/'data/processed/precinct_candidates_2026.csv',sep=';').sort_values(['precinct','party_id','position']).reset_index(drop=True)
    city=pd.read_csv(root/'data/processed/city_candidates_2026.csv',sep=';').sort_values(['party_id','position']).reset_index(drop=True)
    H=obs.votes.to_numpy().reshape(4,8,15)
    assert H.sum()==23939 and len(city)==120 and np.array_equal(H.sum(0).ravel(),city.votes)
    assert (H-np.minimum.accumulate(H,axis=-1)).sum()==1493
    assert (H.sum(0)-np.minimum.accumulate(H.sum(0),axis=-1)).sum()==1096
    return H,obs,city

def run_fit(H,label,scenario='reference',tune=6000,draws=20000,seed=20261010,no_candidate=False,force=False):
    config_path=ROOT/'run_config.json'
    config=json.loads(config_path.read_text()) if config_path.exists() else {}
    override=config.get('runs',{}).get(label,{})
    tune=override.get('tune',tune);draws=override.get('draws',draws);seed=override.get('seed',seed)
    scenario=override.get('scenario',scenario);no_candidate=override.get('no_candidate',no_candidate)
    settings=dict(label=label,scenario=scenario,tune=tune,draws=draws,chains=4,seed=seed,no_candidate=no_candidate)
    signature=hashlib.sha256(H.tobytes()+json.dumps(settings,sort_keys=True).encode()+(ROOT/'src/model.py').read_bytes()).hexdigest()
    cache=ROOT/'results/chains'/f'{label}.npz';meta=cache.with_suffix('.json')
    if not force and cache.exists() and meta.exists() and json.loads(meta.read_text())['signature']==signature:
        out=dict(np.load(cache));out['S']=H[None,None]-out['C'];print(f'{label}: ověřený uložený výpočet',flush=True);return out
    print(f'{label}: 4 řetězce × ({tune} zahřátí + {draws} iterací po zahřátí)',flush=True)
    out=fit(H,scenario,tune,draws,4,seed,no_candidate=no_candidate)
    idata=to_arviz(out)
    # Constant theta/a in the no-candidate comparator are intentionally omitted.
    if no_candidate:idata.posterior=idata.posterior.drop_vars(['theta','a'])
    diag=az.summary(idata,kind='all',round_to='none',hdi_prob=.95).reset_index(names='parameter')
    write_csv(diag,ROOT/'results'/f'diagnostics_{label}.csv')
    key=diag[diag.parameter.isin(['C_total','beta','a','phi','B_total','tail_mass'])]
    print(key[['parameter','mean','ess_bulk','r_hat']].to_string(index=False),flush=True)
    # Keep a regular stride of iterations to keep the downloadable project manageable.
    # Diagnostics above always use all unthinned draws; thinning is storage only.
    stride=config.get('storage_stride',25)
    stored={k:v[:,::stride].copy() if k not in ['acceptance','runtime','wall_seconds'] else v for k,v in out.items() if k!='S'}
    settings.update(signature=signature,storage_stride=stride,wall_seconds=float(out['wall_seconds']),chain_runtime_seconds=out['runtime'].tolist(),acceptance=out['acceptance'].tolist(),diagnostics_on_unthinned=True,software=dict(python=platform.python_version(),numpy=np.__version__,arviz=az.__version__),max_rhat=float(diag.r_hat.max()),min_ess_bulk=float(diag.ess_bulk.min()),min_ess_tail=float(diag.ess_tail.min()),sampler='FFBS + Gibbs + Metropolis; divergences/BFMI not applicable')
    save_fit(cache,stored,settings);stored['S']=H[None,None]-stored['C'];return stored

def simulate_ballots(seed=742):
    """Legally valid individual ballots with k=0..15 and variable use of personal votes.
    This is deliberately not the aggregate inference model (misspecification test).
    """
    rng=np.random.default_rng(seed);P,J,I=4,8,15;H=np.zeros((P,J,I),int);S=H.copy();C=H.copy()
    theta=rng.lognormal(0,.5,(J,I));x=np.linspace(.5,-.5,I)
    weights=np.array([1.5,.7,1.6,.5,.9,.5,1.4,.8])[:,None]*theta*np.exp(.6*x)
    pk=np.r_[.6,.4*np.exp(-np.arange(15)/3)/np.exp(-np.arange(15)/3).sum()]
    counts=np.zeros(16,int);used=[]
    for p in range(P):
        local=weights*rng.lognormal(0,.15,(J,I));party=np.array([.20,.07,.23,.05,.10,.05,.20,.10])*rng.lognormal(0,.2,J);party/=party.sum()
        for _ in range(430):
            if rng.random()<.78:
                s=int(rng.choice(J,p=party));k=int(rng.choice(16,p=pk));counts[k]+=1
                S[p,s,:15-k]+=1;w=local.copy();w[s]=0;probs=w.ravel()/w.sum()
                ids=rng.choice(120,size=k,replace=False,p=probs)
            else:
                k=int(1+rng.binomial(14,.68));used.append(k)
                ids=rng.choice(120,size=k,replace=False,p=local.ravel()/local.sum())
            C[p].ravel()[ids]+=1
    H=S+C
    return H,S,C,dict(k_counts=counts.tolist(),pure_used=used,theta=theta.tolist(),beta=.6)

def matched_simulation(seed=551):
    rng=np.random.default_rng(seed)
    d=dict(b=np.array([65,22,70,15,33,17,62,33.]),A=np.array([15,8,18,6,10,6,13,8.]),theta=rng.gamma(4,.25,(8,15)),g=rng.gamma(8,1/8,(4,8)),v=rng.gamma(8,1/8,(4,8)),beta=.7,a=4.,phi=16.,pi=pi_alpha(SCENARIOS['reference'])/24)
    H,S,C,_=predictive(d,rng)
    return H,S,C,d

def ppc(out,n=500,seed=954,new_precinct=False):
    rng=np.random.default_rng(seed);Hs=[];tries=[]
    for _ in range(n):
        ch=int(rng.integers(out['C'].shape[0]));it=int(rng.integers(out['C'].shape[1]));d={k:out[k][ch,it] for k in ['b','A','g','v','theta','beta','phi','pi']}
        if new_precinct:d['g']=np.ones((1,8));d['v']=np.ones((1,8))
        h,s,c,t=predictive(d,rng,new_precinct=new_precinct);Hs.append(h);tries.append(t)
    return np.array(Hs),np.array(tries)

def execute_suite(force=False,mode='full'):
    H,obs,city=load_data();(ROOT/'results/chains').mkdir(exist_ok=True,parents=True)
    # Real fits use a long retained run; simulations/CV are separately labelled diagnostics.
    tune,draws=(6000,20000) if mode=='full' else (1000,1500)
    fits={}
    for j,sc in enumerate(SCENARIOS):
        fits[sc]=run_fit(H,sc,sc,tune,draws*2 if sc=='reference' else draws,20261010+j*117,force=force)
    fits['no_candidate']=run_fit(H,'no_candidate','reference',tune,draws,20261800,no_candidate=True,force=force)
    for tag,sim in [('matched',matched_simulation()),('ballot',simulate_ballots())]:
        h,s,c,truth=sim
        np.savez_compressed(ROOT/'results'/f'synthetic_{tag}.npz',H=h,S=s,C=c)
        (ROOT/'results'/f'synthetic_{tag}_truth.json').write_text(json.dumps({k:np.asarray(v).tolist() for k,v in truth.items()},ensure_ascii=False,indent=2))
        run_fit(h,f'recovery_{tag}',tune=tune,draws=draws,seed=71000+(tag=='ballot'),force=force)
    for p in range(4):
        train=np.delete(H,p,axis=0)
        run_fit(train,f'cv_{p+1}',tune=tune,draws=draws,seed=88000+p,force=force)
    return fits
