import itertools
import numpy as np
from scipy.stats import poisson,nbinom
from src.model import ffbs,seed_numba,increments,budget_ok
from src.bounds import budget_bound,audit_flow,legal_ballots

def test_ffbs_against_exact_enumeration():
    # Independent, exhaustively computed target; tests normalizer AND sampled states.
    h=np.array([3,2,4]);lam=2.5;pi=np.array([.5,.3,.2]);mu=np.array([1.2,.8,2.]);phi=3.
    paths=[];weights=[]
    for s in itertools.product(*[range(int(v)+1) for v in h]):
        s=np.array(s)
        if np.any(np.diff(s)>0):continue
        n=increments(s)
        w=np.prod(poisson.pmf(n,lam*pi))*np.prod(nbinom.pmf(h-s,phi,phi/(phi+mu)))
        paths.append(s);weights.append(w)
    weights=np.array(weights);z=weights.sum();weights/=z
    truth=np.average(np.array(paths),axis=0,weights=weights)
    seed_numba(123)
    draws=[]
    for _ in range(15000):
        s,logz=ffbs(h,lam,pi,mu,phi);draws.append(s)
    assert np.isclose(np.exp(logz),z,rtol=1e-11)
    assert np.allclose(np.mean(draws,axis=0),truth,atol=.035)

def test_integer_budget_bound_small_exhaustive():
    h=np.array([[3,1,2],[2,2,1]])
    lower,S=budget_bound(h)
    feasible=[]
    for b0 in range(4):
        for b1 in range(3):
            if b0+b1<=h.sum()//3:
                ss=np.minimum(np.minimum.accumulate(h,axis=1),np.array([b0,b1])[:,None]);feasible.append((h-ss).sum())
    assert lower==min(feasible)

def test_legal_ballot_witness():
    S=np.zeros((8,15),dtype=int);S[0,:13]=2;S[0,13:]=1
    C=np.zeros_like(S);C[1,:2]=1
    H=S+C
    assert audit_flow(H,S)['feasible']
    ss,cc,records=legal_ballots(H,S)
    assert np.array_equal(S,ss) and np.array_equal(C,cc)
    for party,ids,auto in records:
        assert len(set(ids))==len(ids)
        assert len(ids)+auto<=15
        assert all(i//15!=party for i in ids)

def test_infeasible_split_budget():
    S=np.zeros((8,15),dtype=int);S[0,0]=5
    assert not budget_ok(S[None],S[None])
    assert not audit_flow(S,S)['feasible']
