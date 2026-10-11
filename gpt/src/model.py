"""Integer Bayesian aggregate model; exact FFBS within a ballot-budget relaxation.
Gamma distributions use shape/rate in the documentation, shape/scale in numpy.
No user data enter the priors. See methodology.md for the joint truncation.
"""
from __future__ import annotations
import json, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy.special import gammaln
from numba import njit

SCENARIOS = {
 'reference': dict(p0=.60, tail=.12, concentration=24., beta_sd=.7, a_logmean=np.log(4.), a_logsd=.6, phi_logmean=np.log(12.), phi_logsd=.7),
 'party_first': dict(p0=.85, tail=.03, concentration=40., beta_sd=.35, a_logmean=np.log(2.), a_logsd=.5, phi_logmean=np.log(12.), phi_logsd=.7),
 'personal_long_tail': dict(p0=.30, tail=.45, concentration=24., beta_sd=1.1, a_logmean=np.log(12.), a_logsd=.5, phi_logmean=np.log(12.), phi_logsd=.7),
 'weak_position': dict(p0=.60, tail=.12, concentration=24., beta_sd=.15, a_logmean=np.log(4.), a_logsd=.6, phi_logmean=np.log(12.), phi_logsd=.7),
 'heterogeneous': dict(p0=.60, tail=.12, concentration=24., beta_sd=.7, a_logmean=np.log(1.), a_logsd=.5, phi_logmean=np.log(12.), phi_logsd=.7),
 'strong_pooling': dict(p0=.60, tail=.12, concentration=24., beta_sd=.7, a_logmean=np.log(16.), a_logsd=.5, phi_logmean=np.log(12.), phi_logsd=.7),
 'poisson_like': dict(p0=.60, tail=.12, concentration=24., beta_sd=.7, a_logmean=np.log(4.), a_logsd=.6, phi_logmean=np.log(1000.), phi_logsd=.1),
}

def pi_alpha(cfg):
    short = .6 ** np.arange(5); short /= short.sum()
    long = .9 ** np.arange(9); long /= long.sum()
    return cfg['concentration'] * np.r_[cfg['p0'], (1-cfg['p0'])*(1-cfg['tail'])*short, (1-cfg['p0'])*cfg['tail']*long]

@njit(cache=True)
def categorical(w):
    t = np.random.random()*w.sum(); acc=0.
    for j in range(len(w)):
        acc+=w[j]
        if acc>=t: return j
    return len(w)-1

@njit(cache=True)
def ffbs(h, lam, pi, mu, phi):
    """Sample S exactly from p(S|h,lambda,pi,mu,phi), before budget indicator.
    Bottom-to-top filtering of independent Poisson increments; NB emissions.
    Returns path and marginal log likelihood for unit tests.
    """
    n=len(h); M=int(h.max())+1
    F=np.zeros((n,M)); K=np.zeros((n,M)); logz=0.
    for t in range(n):
        rate=max(1e-12,lam*pi[t])
        lp=np.empty(M);lp[0]=-rate
        for v in range(1,M):lp[v]=lp[v-1]+np.log(rate)-np.log(v)
        mx=lp.max();K[t]=np.exp(lp-mx);logz+=mx
        i=n-1-t
        le=np.empty(h[i]+1)
        le[0]=phi*np.log(phi/(phi+mu[i]))
        for c in range(1,h[i]+1):
            le[c]=le[c-1]+np.log(c-1+phi)-np.log(c)+np.log(mu[i]/(phi+mu[i]))
        em=le.max();logz+=em
        for v in range(h[i]+1):
            val=K[t,v] if t==0 else 0.
            if t>0:
                for u in range(v+1):val+=F[t-1,u]*K[t,v-u]
            F[t,v]=val*np.exp(le[h[i]-v]-em)
        sm=F[t].sum()
        if sm<=0: raise ValueError('FFBS underflow')
        F[t]/=sm;logz+=np.log(sm)
    path=np.zeros(n,np.int64)
    v=categorical(F[n-1]);path[0]=v
    for t in range(n-1,0,-1):
        w=np.empty(v+1)
        for u in range(v+1):w[u]=F[t-1,u]*K[t,v-u]
        v=categorical(w);path[n-t]=v
    return path,logz

@njit(cache=True)
def seed_numba(seed): np.random.seed(seed)

def increments(S):
    # k=0 produces the full list; k=14 produces only the first candidate.
    return np.concatenate((S[..., -1:], np.diff(S[..., ::-1],axis=-1)),axis=-1)

@njit(cache=True)
def budget_ok(H,S):
    for p in range(H.shape[0]):
        total=0;B=0;Cp=np.zeros(H.shape[1]);L=np.zeros(H.shape[1])
        for s in range(H.shape[1]):
            B+=S[p,s,0];ss=0
            for i in range(H.shape[2]):
                if S[p,s,i]<0 or S[p,s,i]>H[p,s,i]:return False
                if i>0 and S[p,s,i]>S[p,s,i-1]:return False
                total+=H[p,s,i];ss+=S[p,s,i];Cp[s]+=H[p,s,i]-S[p,s,i]
            L[s]=15*S[p,s,0]-ss
        if 15*B>total:return False
        for s in range(H.shape[1]):
            if L[s]>Cp.sum()-Cp[s]:return False
    return True

def _gamma_log(a,x):
    return x.size*(a*np.log(a)-gammaln(a))+(a-1)*np.log(x).sum()-a*x.sum()

def _chain(args):
    H,cfg,seed,tune,draws,exposure,no_candidate=args
    t0=time.monotonic();rng=np.random.default_rng(seed);seed_numba(seed)
    P,J,I=H.shape;x=np.linspace(.5,-.5,I);e=np.asarray(exposure)[:,None,None]
    # Dispersed but feasible starting paths (S=0 itself is always feasible).
    frac=rng.uniform(.15,.85)
    S=np.floor(np.minimum.accumulate(H,axis=-1)*frac).astype(np.int64)
    while not budget_ok(H,S): S=(S*.9).astype(np.int64)
    a=np.exp(rng.normal(cfg['a_logmean'],.3));phi=np.exp(rng.normal(cfg['phi_logmean'],.2))
    b=rng.gamma(2,25,J);A=rng.gamma(2,7.5,J)
    theta=np.ones((J,I));g=np.ones((P,J));v=np.ones((P,J));beta=rng.normal(0,.3)
    pi=rng.dirichlet(pi_alpha(cfg));alpha=pi_alpha(cfg)
    output={
      'C':np.empty((draws,P,J,I),np.int16), 'S':np.empty((draws,P,J,I),np.int16),
      'theta':np.empty((draws,J,I)), 'pi':np.empty((draws,I)),
      'b':np.empty((draws,J)), 'A':np.empty((draws,J)),
      'g':np.empty((draws,P,J)), 'v':np.empty((draws,P,J)),
      'beta':np.empty(draws), 'a':np.empty(draws),'phi':np.empty(draws),
    }
    accept=np.zeros(6); step=np.array([.06,.08,.12,.10])
    for it in range(tune+draws):
        mu=e*A[None,:,None]*g[:,:,None]*theta[None,:,:]*np.exp(beta*x)[None,None,:]
        for p in range(P):
          for s in rng.permutation(J):
            proposal,_=ffbs(H[p,s],exposure[p]*b[s]*v[p,s],pi,mu[p,s],phi)
            old=S[p,s].copy();S[p,s]=proposal
            if budget_ok(H[p:p+1],S[p:p+1]):accept[0]+=1
            else:S[p,s]=old
        # Symmetric integer ridge proposal: move a common full-prefix count for one
        # party and translate candidate intensities. Unit Jacobian, explicit NB/Poisson
        # and Gamma prior ratios. This is before delta is redrawn (collapsed kernel).
        if not no_candidate:
          for s in rng.permutation(J):
            d=int(rng.integers(-6,7))
            if d==0:continue
            old=S[:,s].copy();S[:,s]-=d
            tp=theta[s]+d/(A[s]*np.mean(np.asarray(exposure)*g[:,s])*np.exp(beta*x))
            if np.any(tp<=0) or not budget_ok(H,S):S[:,s]=old;continue
            co=H[:,s]-old;cn=co+d
            mo=mu[:,s];mn=e[:,0,:]*A[s]*g[:,s,None]*tp[None,:]*np.exp(beta*x)
            def nblog(c,m):
                return gammaln(c+phi)-gammaln(c+1)+phi*np.log(phi/(phi+m))+c*np.log(m/(phi+m))
            rate=np.asarray(exposure)*b[s]*v[:,s]*pi[0]
            no=old[:,-1];nn=no-d
            lr=np.sum(nblog(cn,mn)-nblog(co,mo))+np.sum(-d*np.log(rate)-gammaln(nn+1)+gammaln(no+1))
            lr+=_gamma_log(a,tp)-_gamma_log(a,theta[s])
            if np.log(rng.random())<lr:theta[s]=tp;mu[:,s]=mn;accept[5]+=1
            else:S[:,s]=old
        C=H-S;N=increments(S)
        # Partially collapsed update: S used marginal NB; redraw delta before conditional moves.
        delta=rng.gamma(phi+C,1/(phi+mu))
        rate_base=e*g[:,:,None]*theta[None,:,:]*np.exp(beta*x)[None,None,:]*delta
        A=rng.gamma(2+C.sum(axis=(0,2)),1/(2/15+rate_base.sum(axis=(0,2))))
        rate_base=e*A[None,:,None]*theta[None,:,:]*np.exp(beta*x)[None,None,:]*delta
        g=rng.gamma(8+C.sum(axis=-1),1/(8+rate_base.sum(axis=-1)))
        if not no_candidate:
            rate_base=e*A[None,:,None]*g[:,:,None]*np.exp(beta*x)[None,None,:]*delta
            theta=rng.gamma(a+C.sum(axis=0),1/(a+rate_base.sum(axis=0)))
        # Poisson component conjugate updates.
        b=rng.gamma(2+N.sum(axis=(0,2)),1/(2/50+(np.asarray(exposure)[:,None]*v).sum(axis=0)))
        v=rng.gamma(8+N.sum(axis=-1),1/(8+np.asarray(exposure)[:,None]*b[None,:]))
        pi=rng.dirichlet(alpha+N.sum(axis=(0,1)))
        # Position MH; all proposal scales become fixed after warmup.
        base=e*A[None,:,None]*g[:,:,None]*theta[None,:,:]*delta
        bp=beta+rng.normal(0,step[0]); db=bp-beta
        lr=db*np.sum(C*x)-np.sum(base*(np.exp(bp*x)-np.exp(beta*x)))-(bp*bp-beta*beta)/(2*cfg['beta_sd']**2)
        if np.log(rng.random())<lr:beta=bp;accept[1]+=1
        # Ridge move beta,theta leaving likelihood unchanged; Jacobian=exp(-db sum x)=1.
        if not no_candidate:
            bp=beta+rng.normal(0,step[1]);db=bp-beta;tp=theta*np.exp(-db*x)
            lr=_gamma_log(a,tp)-_gamma_log(a,theta)-(bp*bp-beta*beta)/(2*cfg['beta_sd']**2)-db*J*x.sum()
            if np.log(rng.random())<lr:beta=bp;theta=tp;accept[2]+=1
            la=np.log(a);lap=la+rng.normal(0,step[2]);ap=np.exp(lap)
            lr=_gamma_log(ap,theta)-_gamma_log(a,theta)-((lap-cfg['a_logmean'])**2-(la-cfg['a_logmean'])**2)/(2*cfg['a_logsd']**2)
            if np.log(rng.random())<lr:a=ap;accept[3]+=1
        lf=np.log(phi);lfp=lf+rng.normal(0,step[3]);fp=np.exp(lfp)
        lr=_gamma_log(fp,delta)-_gamma_log(phi,delta)-((lfp-cfg['phi_logmean'])**2-(lf-cfg['phi_logmean'])**2)/(2*cfg['phi_logsd']**2)
        if np.log(rng.random())<lr:phi=fp;accept[4]+=1
        if it<tune and (it+1)%100==0:
            rates=accept[1:5]/100
            step*=np.exp(np.clip(rates-.35,-.25,.25));accept[:]=0
        if it>=tune:
            j=it-tune
            for key,val in [('C',C),('S',S),('theta',theta),('pi',pi),('b',b),('A',A),('g',g),('v',v),('beta',beta),('a',a),('phi',phi)]:output[key][j]=val
    output['acceptance']=accept/np.array([draws*P*J,draws,draws,draws,draws,draws*J])
    output['runtime']=np.array(time.monotonic()-t0)
    return output

def fit(H,scenario='reference',tune=3000,draws=3000,chains=4,seed=20261010,exposure=None,no_candidate=False,parallel=True):
    H=np.asarray(H,dtype=np.int64);exposure=np.ones(H.shape[0]) if exposure is None else np.asarray(exposure)
    cfg=SCENARIOS[scenario].copy() if isinstance(scenario,str) else scenario
    args=[(H,cfg,seed+1009*c,tune,draws,exposure,no_candidate) for c in range(chains)]
    t0=time.monotonic()
    if parallel:
        with ProcessPoolExecutor(max_workers=chains) as pool:r=list(pool.map(_chain,args))
    else:r=[_chain(a) for a in args]
    out={k:np.stack([d[k] for d in r]) for k in r[0]}
    out['wall_seconds']=np.array(time.monotonic()-t0)
    return out

def predictive(draw, rng, exposure=None, new_precinct=False, max_tries=10000):
    """Draw from p(H_rep,N_rep,C_rep|theta,F=1). Redraw all precinct blocks on rejection.
    Conditioning here does not refit/reuse observed H, S, C, or delta.
    """
    g=draw['g'];v=draw['v'];P,J=g.shape;I=draw['theta'].shape[-1]
    exposure=np.ones(P) if exposure is None else np.asarray(exposure);x=np.linspace(.5,-.5,I)
    for tries in range(max_tries):
        gg=rng.gamma(8,1/8,(P,J)) if new_precinct else g
        vv=rng.gamma(8,1/8,(P,J)) if new_precinct else v
        N=rng.poisson(exposure[:,None,None]*draw['b'][None,:,None]*vv[:,:,None]*draw['pi'][None,None,:])
        S=np.cumsum(N,axis=-1)[...,::-1]
        mu=exposure[:,None,None]*draw['A'][None,:,None]*gg[:,:,None]*draw['theta'][None,:,:]*np.exp(draw['beta']*x)
        C=rng.negative_binomial(draw['phi'],draw['phi']/(draw['phi']+mu))
        H=S+C
        if budget_ok(H,S):return H,S,C,tries+1
    raise RuntimeError('Predictive rejection limit; inspect incompatible priors.')

def prior_draw(rng,cfg,P=4,J=8,I=15):
    a=np.exp(rng.normal(cfg['a_logmean'],cfg['a_logsd']));phi=np.exp(rng.normal(cfg['phi_logmean'],cfg['phi_logsd']))
    return dict(a=a,phi=phi,b=rng.gamma(2,25,J),A=rng.gamma(2,7.5,J),g=rng.gamma(8,1/8,(P,J)),v=rng.gamma(8,1/8,(P,J)),theta=rng.gamma(a,1/a,(J,I)),beta=rng.normal(0,cfg['beta_sd']),pi=rng.dirichlet(pi_alpha(cfg)))

def sample_prior(n=400,scenario='reference',seed=411):
    """Jointly condition parameter and data draws on F; do NOT fix theta while rejecting."""
    rng=np.random.default_rng(seed);cfg=SCENARIOS[scenario];hs=[];cs=[];pars=[];attempts=0
    while len(hs)<n:
        d=prior_draw(rng,cfg);attempts+=1
        try:H,S,C,_=predictive(d,rng,max_tries=1)
        except RuntimeError:continue
        hs.append(H);cs.append(C);pars.append([d['pi'][0],d['pi'][6:].sum(),d['beta'],d['a'],d['phi']])
    return dict(H=np.array(hs),C=np.array(cs),parameters=np.array(pars),attempts=np.array(attempts))

def to_arviz(out):
    import arviz as az
    C=out['C'];S=out['S'];pi=out['pi']
    pars={k:out[k] for k in ['beta','a','phi','b','A','theta','g','v','pi']}
    pars.update(C_candidate=C.sum(axis=2).reshape(*C.shape[:2],-1), C_total=C.sum(axis=(2,3,4)),B_total=S[...,0].sum(axis=(2,3)),tail_mass=pi[...,6:].sum(axis=-1))
    return az.from_dict(posterior=pars)

def save_fit(path,out,meta):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,**out)
    path.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
