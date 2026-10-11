"""Derived CSVs and scientific checks. All intervals use equal-tailed quantiles."""
from pathlib import Path
import json,hashlib,platform,sys
import numpy as np,pandas as pd
from scipy.stats import rankdata,spearmanr
from .experiments import ROOT,load_data,write_csv,ppc
from .model import SCENARIOS,sample_prior,increments
from .bounds import budget_bound,audit_flow,legal_ballots

Q=[.025,.05,.25,.5,.75,.95,.975]
QN=['q025','q05','q25','median','q75','q95','q975']

def load_fit(label,H):
    d=dict(np.load(ROOT/'results/chains'/f'{label}.npz'));d['S']=H[None,None]-d['C'];return d

def flatten(v):return v.reshape((-1,)+v.shape[2:])

def intervals(v,prefix='personal_'):
    # First dimension is Monte Carlo draws, remaining dimensions are output units.
    out={prefix+'mean':v.mean(axis=0)}
    out.update({prefix+n:a for n,a in zip(QN,np.quantile(v,Q,axis=0))})
    return out

def add_intervals(df,v,prefix='personal_'):
    for k,vv in intervals(v,prefix).items():df[k]=np.asarray(vv).ravel()
    return df

def compile_results():
    H,obs,city=load_data();out=load_fit('reference',H);C=flatten(out['C']);S=H[None]-C;Cc=C.sum(axis=1).reshape(-1,120)
    cand=city.copy();cand['candidate_id']=[f'{s:02d}-{i:02d}' for s,i in zip(city.party_id,city.position)]
    for p in range(4):cand[f'votes_p{p+1}']=H[p].ravel()
    add_intervals(cand,Cc)
    effect=flatten(out['theta']).reshape(-1,120)
    # Within-party geometric normalization, making the amplitude convention explicit.
    effect=effect.reshape(-1,8,15);effect=np.exp(np.log(effect)-np.log(effect).mean(axis=-1,keepdims=True)).reshape(-1,120)
    add_intervals(cand,effect,'position_adjusted_effect_');cand['p_effect_above_party_center']=(effect>1).mean(0)
    ranks=rankdata(-Cc,method='average',axis=1)
    add_intervals(cand,ranks,'rank_');cand['p_top10']=(ranks<=10).mean(0)
    candidate_sens=[];sens=[];runrows=[];priorrows=[];priors={};scenario_c=[];scenario_r=[];scenario_top=[];scenario_gate=[]
    for label in SCENARIOS:
        z=load_fit(label,H);c=flatten(z['C']).sum(axis=1).reshape(-1,120);total=c.sum(axis=1)
        p0=flatten(z['pi'])[:,0];tail=flatten(z['pi'])[:,6:].sum(axis=1)
        dd=pd.read_csv(ROOT/'results'/f'diagnostics_{label}.csv',sep=';')
        ddc=dd[dd.parameter.str.startswith('C_candidate[')].copy();ddc['ix']=ddc.parameter.str.extract(r'\[(\d+)\]').astype(int);ddc=ddc.sort_values('ix')
        scenario_gate.append(((ddc.r_hat<=1.01)&(ddc.ess_bulk>=400)&(ddc.ess_tail>=400)).to_numpy())
        row={'scenario':label,'personal_total_mean':total.mean(),'personal_total_median':np.median(total),'personal_total_q025':np.quantile(total,.025),'personal_total_q975':np.quantile(total,.975),'personal_share_median':np.median(total)/H.sum(),'p0_median':np.median(p0),'tail_6_14_median':np.median(tail),'beta_median':np.median(z['beta']),'a_median':np.median(z['a'])};row.update(mcmc_max_rhat=dd.r_hat.max(),mcmc_min_ess_bulk=dd.ess_bulk.min(),mcmc_min_ess_tail=dd.ess_tail.min(),mcmc_gate_pass=bool((dd.r_hat<=1.01).all() and (dd.ess_bulk>=400).all() and (dd.ess_tail>=400).all()));sens.append(row)
        med=np.median(c,axis=0);r=rankdata(-med,method='average');rt=rankdata(-c,axis=1);top=(rt<=10).mean(0)
        scenario_c.append(med);scenario_r.append(r);scenario_top.append(top)
        q=np.quantile(c,[.025,.975],axis=0)
        candidate_sens.extend(dict(scenario=label,candidate_id=cand.candidate_id.iloc[i],personal_median=med[i],q025=q[0,i],q975=q[1,i],median_rank=r[i],p_top10=top[i]) for i in range(120))
        pr=sample_prior(500,label,seed=640+list(SCENARIOS).index(label));priors[label]=pr
        np.savez_compressed(ROOT/'results'/f'prior_{label}.npz',**pr)
        priorrows.append(dict(scenario=label,accepted=500,attempts=int(pr['attempts']),acceptance=500/int(pr['attempts']),prior_votes_q025=np.quantile(pr['H'].sum(axis=(1,2,3)),.025),prior_votes_median=np.median(pr['H'].sum(axis=(1,2,3))),prior_votes_q975=np.quantile(pr['H'].sum(axis=(1,2,3)),.975),observed_votes=int(H.sum())))
    cand['scenario_median_min']=np.min(scenario_c,axis=0);cand['scenario_median_max']=np.max(scenario_c,axis=0)
    cand['scenario_rank_min']=np.min(scenario_r,axis=0);cand['scenario_rank_max']=np.max(scenario_r,axis=0);cand['min_scenario_p_top10']=np.min(scenario_top,axis=0)
    cand['all_scenarios_candidate_mcmc_gate_pass']=np.all(scenario_gate,axis=0)
    cand['rank_robustness']=np.where(cand.min_scenario_p_top10>=.8,'top10_p_ge_0.8_all_models',np.where(cand.scenario_rank_max-cand.scenario_rank_min<=10,'scenario_rank_span_le_10','scenario_rank_unstable'))
    diag=pd.read_csv(ROOT/'results/diagnostics_reference.csv',sep=';')
    dc=diag[diag.parameter.str.startswith('C_candidate[')].copy()
    dc['ix']=dc.parameter.str.extract(r'\[(\d+)\]').astype(int);dc=dc.sort_values('ix')
    cand['r_hat']=dc.r_hat.to_numpy();cand['ess_bulk']=dc.ess_bulk.to_numpy();cand['ess_tail']=dc.ess_tail.to_numpy()
    cand['mcmc_gate_pass']=(cand.r_hat<=1.01)&(cand.ess_bulk>=400)&(cand.ess_tail>=400)
    cand['interval_type']='equal_tailed_posterior_conditional_on_reference_aggregate_model'
    write_csv(cand,ROOT/'results/candidate_estimates.csv')
    pc=obs.copy();add_intervals(pc,C.reshape(-1,480));pc['automatic_mean']=H.ravel()-pc.personal_mean
    write_csv(pc,ROOT/'results/candidate_precinct_estimates.csv')
    party=city.groupby(['party_id','party'],sort=True).agg(votes=('votes','sum'),seats=('elected_2026',lambda s:(s=='ANO').sum()),rigorous_min_sum=('rigorous_min_personal_marks_sum_precincts','sum')).reset_index()
    party['vote_share_pct']=party.votes/H.sum()*100;party['passed_5pct']=party.vote_share_pct>=5
    add_intervals(party,C.sum(axis=(1,3)));party['automatic_mean']=party.votes-party.personal_mean
    add_intervals(party,S[...,0].sum(axis=1),'effective_party_ballots_')
    for p in range(4):party[f'votes_p{p+1}']=H[p].sum(axis=-1)
    write_csv(party,ROOT/'results/party_estimates.csv')
    precinct=pd.DataFrame({'precinct':np.arange(1,5),'votes':H.sum(axis=(1,2)),'monotonic_minimum':(H-np.minimum.accumulate(H,axis=-1)).sum(axis=(1,2))})
    add_intervals(precinct,C.sum(axis=(2,3)));bounds=[];witness=[]
    for p in range(4):
        low,ss=budget_bound(H[p]);a=audit_flow(H[p],ss)
        sw,cw,ballots=legal_ballots(H[p],ss)
        bounds.append(low)
        for s in range(8):
            for i in range(15):witness.append(dict(precinct=p+1,party_id=s+1,position=i+1,votes=int(H[p,s,i]),automatic_witness=int(sw[s,i]),personal_witness=int(cw[s,i])))
    precinct['budget_lower_bound']=bounds
    write_csv(precinct,ROOT/'results/precinct_estimates.csv');write_csv(pd.DataFrame(witness),ROOT/'results/constructive_minimum_witness.csv')
    write_csv(pd.DataFrame(sens),ROOT/'results/prior_sensitivity.csv');write_csv(pd.DataFrame(candidate_sens),ROOT/'results/candidate_sensitivity.csv');write_csv(pd.DataFrame(priorrows),ROOT/'results/prior_predictive_checks.csv')
    # Each metadata file states the actual diagnostic stride; there is no HMC.
    flagrows=[]
    for f in sorted((ROOT/'results/chains').glob('*.json')):
        meta=json.loads(f.read_text());dg=pd.read_csv(ROOT/'results'/f'diagnostics_{meta["label"]}.csv',sep=';')
        bad=dg[(dg.r_hat>1.01)|(dg.ess_bulk<400)|(dg.ess_tail<400)].copy();bad.insert(0,'run',meta['label']);flagrows.append(bad)
        runrows.append(dict(label=meta['label'],mcmc_gate_pass=bool(len(bad)==0),chains=4,warmup_per_chain=meta['tune'],draws_per_chain=meta['draws'],storage_stride=meta['storage_stride'],diagnostic_stride=1 if meta['diagnostics_on_unthinned'] else meta.get('diagnostic_stride',meta['storage_stride']),wall_seconds=meta['wall_seconds'],max_rhat=dg.r_hat.max(),min_ess_bulk=dg.ess_bulk.min(),min_ess_tail=dg.ess_tail.min(),n_rhat_gt_1_01=int((dg.r_hat>1.01).sum()),n_ess_bulk_lt_400=int((dg.ess_bulk<400).sum()),n_ess_tail_lt_400=int((dg.ess_tail<400).sum()),divergences='NA_non_HMC',bfmi='NA_non_HMC'))
    write_csv(pd.DataFrame(runrows),ROOT/'results/mcmc_run_summary.csv')
    write_csv(pd.concat(flagrows,ignore_index=True),ROOT/'results/diagnostic_flags.csv')
    # Predictive checks: redraw prefix AND personal components. Stored S is never reused.
    ppctables=[]
    for label in ['reference','no_candidate','poisson_like']:
        z=load_fit(label,H);rep,tr=ppc(z,n=800,seed=211+len(label));np.savez_compressed(ROOT/'results'/f'ppc_{label}.npz',H_rep=rep,attempts=tr)
        q=np.quantile(rep,[.025,.5,.975],axis=0);sd=rep.std(axis=0,ddof=1)
        r=obs.copy();r['model']=label;r['pred_q025']=q[0].ravel();r['pred_median']=q[1].ravel();r['pred_q975']=q[2].ravel();r['standardized_residual']=((H-rep.mean(0))/sd).ravel();r['inside_95']=(H>=q[0]).ravel()&(H<=q[2]).ravel();ppctables.append(r)
        rows=[]
        for dim,axes in [('precinct',(2,3)),('party',(1,3)),('position',(1,2))]:
            val=rep.sum(axis=axes);observed=H.sum(axis=tuple(a-1 for a in axes))
            for i,vv in enumerate(observed):
                qq=np.quantile(val[:,i],[.025,.5,.975]);rows.append(dict(dimension=dim,unit=i+1,observed=int(vv),pred_q025=qq[0],pred_median=qq[1],pred_q975=qq[2],p_rep_ge_observed=float(np.mean(val[:,i]>=vv))))
        write_csv(pd.DataFrame(rows),ROOT/'results'/f'ppc_grouped_{label}.csv')
    write_csv(pd.concat(ppctables),ROOT/'results/ppc_residuals.csv')
    # Network-flow audits check a deterministic, evenly spaced subset, not selected successes.
    flowrows=[]
    for label in SCENARIOS:
        z=load_fit(label,H);ss=flatten(z['S']);idx=np.linspace(0,len(ss)-1,100,dtype=int)
        for j in idx:
            for p in range(4):flowrows.append(dict(model=label,draw=int(j),precinct=p+1,**audit_flow(H[p],ss[j,p])))
    write_csv(pd.DataFrame(flowrows),ROOT/'results/ballot_feasibility_audit.csv')
    # Recovery: one matched and one legal-ballot misspecification test, NOT calibrated SBC.
    rec=[];recc=[]
    for tag in ['matched','ballot']:
        tr=dict(np.load(ROOT/'results'/f'synthetic_{tag}.npz'));z=load_fit(f'recovery_{tag}',tr['H']);cc=flatten(z['C']).sum(axis=1).reshape(-1,120);truth=tr['C'].sum(0).ravel();qq=np.quantile(cc,[.025,.5,.975],axis=0);total=cc.sum(1)
        rec.append(dict(experiment=tag,true_personal_total=int(truth.sum()),posterior_median=np.median(total),q025=np.quantile(total,.025),q975=np.quantile(total,.975),candidate_95_coverage=np.mean((truth>=qq[0])&(truth<=qq[2])),candidate_MAE=np.mean(np.abs(qq[1]-truth)),candidate_rank_spearman=spearmanr(qq[1],truth).statistic))
        recc.extend(dict(experiment=tag,candidate_id=cand.candidate_id.iloc[i],truth=int(truth[i]),q025=qq[0,i],median=qq[1,i],q975=qq[2,i]) for i in range(120))
    write_csv(pd.DataFrame(rec),ROOT/'results/synthetic_recovery.csv');write_csv(pd.DataFrame(recc),ROOT/'results/synthetic_recovery_candidates.csv')
    # Held-out composition predictor, RESCALED to each known held-out party total.
    # This is not exact conditional sampling from the original NB/Poisson model.
    # Those totals are given equally to all models; all shape fitting excludes the held-out precinct.
    cvrows=[];cvpred=[]
    for p in range(4):
        train=np.delete(H,p,axis=0);z=load_fit(f'cv_{p+1}',train);rep,tr=ppc(z,1000,seed=919+p,new_precinct=True);rep=rep[:,0].astype(float)+.01
        party_total=H[p].sum(axis=1,keepdims=True);pred=rep/rep.sum(axis=2,keepdims=True)*party_total
        pooled=(train.sum(0)+.5)/(train.sum(axis=(0,2))[:,None]+7.5)*party_total
        # Position-only candidate shape shares information across all parties, no candidate identity.
        pos=train.sum(axis=(0,1))+.5;pos=pos/pos.sum();position=party_total*pos[None,:]
        for name,mean,lo,hi in [('hierarchical',pred.mean(0),np.quantile(pred,.025,axis=0),np.quantile(pred,.975,axis=0)),('city_pooled',pooled,np.full_like(pooled,np.nan),np.full_like(pooled,np.nan)),('position_only',position,np.full_like(position,np.nan),np.full_like(position,np.nan))]:
            err=mean-H[p];cvrows.append(dict(held_out_precinct=p+1,model=name,MAE=np.mean(np.abs(err)),RMSE=np.sqrt(np.mean(err**2)),coverage_95=np.mean((H[p]>=lo)&(H[p]<=hi)) if name=='hierarchical' else np.nan,conditional_on_party_totals=True,prediction_method='rescaled_composition_not_exact_conditional_sampling'))
            cvpred.extend(dict(precinct=p+1,model=name,candidate_id=cand.candidate_id.iloc[i],observed=H[p].ravel()[i],pred_mean=mean.ravel()[i],q025=lo.ravel()[i],q975=hi.ravel()[i]) for i in range(120))
    write_csv(pd.DataFrame(cvrows),ROOT/'results/out_of_precinct_validation.csv');write_csv(pd.DataFrame(cvpred),ROOT/'results/out_of_precinct_predictions.csv')
    # Historical baseline is aligned by list ordering and position, not fuzzy person matching.
    base=pd.read_csv(ROOT/'data/raw/baseline_revnice_model_osobnich_krizku_120.csv',sep=';')
    assert len(base)==120 and np.array_equal(base.hlasy_csu,cand.votes)
    bc=cand[['candidate_id','name','party','votes','personal_median','personal_q025','personal_q975']].copy()
    bc['old_scenario_median']=base.model_median_krizku;bc['old_scenario_p10']=base.model_rozpeti_10pct;bc['old_scenario_p90']=base.model_rozpeti_90pct;bc['difference_medians']=bc.personal_median-bc.old_scenario_median
    write_csv(bc,ROOT/'results/old_baseline_comparison.csv')
    hist=pd.read_csv(ROOT/'data/raw/strany_2022_2026.csv',sep=';');write_csv(hist,ROOT/'results/party_changes_2022_2026.csv')
    elected=pd.read_csv(ROOT/'data/raw/zvoleni_2026_a_srovnani_2022.csv',sep=';')
    elected['share_all_votes_2026_pct']=elected.hlasy_2026/H.sum()*100
    elected['share_all_votes_2022_pct']=elected.hlasy_2022_pokud_zvolen_2022/21773*100
    write_csv(elected,ROOT/'results/elected_comparison.csv')
    # Exact nonidentification: under-use and ineffective K=15 bookkeeping have flat likelihood.
    # These are illustrative priors, deliberately not inferred from H.
    rng=np.random.default_rng(427);u=rng.beta(2,2,10000);psi=rng.beta(1,9,10000)
    pdict=dict(utilization_u=u,expected_marks_per_pure_ballot=1+14*u,ineffective_K15_fraction=psi)
    write_csv(pd.DataFrame([dict(parameter=k,prior_q025=np.quantile(v,.025),prior_median=np.median(v),prior_q975=np.quantile(v,.975),posterior_q025=np.quantile(v,.025),posterior_median=np.median(v),posterior_q975=np.quantile(v,.975),status='prior_equals_posterior_by_definition_not_identified') for k,v in pdict.items()]),ROOT/'results/nonidentified_parameters.csv')
    # Shape-level correlations expose confounding. Candidate interval widths are not voter identifiability.
    total=C.sum(axis=(1,2,3));beta=out['beta'].ravel();p0=flatten(out['pi'])[:,0];tail=flatten(out['pi'])[:,6:].sum(1)
    cor=pd.DataFrame(dict(personal_total=total,beta=beta,p0=p0,tail=tail,a=out['a'].ravel(),phi=out['phi'].ravel())).corr().reset_index(names='parameter');write_csv(cor,ROOT/'results/posterior_correlations.csv')
    assert (C>=0).all() and (C<=H[None]).all() and (C>=(H-np.minimum.accumulate(H,axis=-1))[None]).all()
    assert np.all(C.sum(axis=(1,2,3))>=sum(bounds))
    return dict(H=H,obs=obs,city=city,candidates=cand,parties=party,precincts=precinct,sensitivity=pd.DataFrame(sens),out=out)
