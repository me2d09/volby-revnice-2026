"""Proven integer lower bound and exact feasibility audit by bipartite max-flow."""
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.csgraph import maximum_flow
from .model import increments

def budget_bound(H):
    """Maximum relaxed automatic total via integer concave resource allocation.
    Budget floor(T/15). Each effective party ballot uses all 15 candidate votes.
    Greedy selects largest marginal gains of min(prefix-min(H),B_s).
    Ignoring donor destinations relaxes the problem, so the resulting bound is valid.
    """
    H=np.asarray(H);M=np.minimum.accumulate(H,axis=-1);J,I=H.shape
    B=np.zeros(J,dtype=int)
    for _ in range(int(H.sum()//I)):
        gains=np.sum(M>B[:,None],axis=1)
        s=int(np.argmax(gains))
        if gains[s]==0:break
        B[s]+=1
    S=np.minimum(M,B[:,None])
    return int((H-S).sum()),S

def audit_flow(H,S,return_flow=False):
    """Can all truncated party ballots receive k DISTINCT outside-party candidates?
    Edges from (source party,k) to candidate have cap N_s,k; source demand=k*N_s,k.
    Uniform row degree k permits decomposition of group flows into N legal ballots.
    Remaining C can always be individual-only ballots when ballot count is unknown.
    """
    H=np.asarray(H);S=np.asarray(S);C=H-S;J,I=H.shape;N=increments(S)
    if np.any(C<0) or np.any(N<0):return {'feasible':False,'deficit':-1}
    groups=[(s,k,int(N[s,k])) for s in range(J) for k in range(1,I) if N[s,k]>0]
    G=len(groups);source=0;dest0=1+G;sink=dest0+J*I
    cap=lil_matrix((sink+1,sink+1),dtype=np.int64);demand=0
    for g,(s,k,n) in enumerate(groups):
        cap[source,1+g]=k*n;demand+=k*n
        for t in range(J):
            if t!=s:cap[1+g,dest0+t*I:dest0+(t+1)*I]=n
    for i,c in enumerate(C.ravel()):cap[dest0+i,sink]=int(c)
    result=maximum_flow(cap.tocsr(),source,sink)
    out={'feasible':result.flow_value==demand,'deficit':int(demand-result.flow_value),'foreign_required':demand,'personal_total':int(C.sum())}
    if return_flow:
        out['groups']=groups;out['allocation']=result.flow[1:1+G,dest0:dest0+J*I].toarray()
    return out

def legal_ballots(H,S):
    """Construct ONE anonymous witness, not a reconstruction of actual voters.
    Pure residuals are one-candidate ballots: voter count is intentionally unconstrained.
    Returns automatic counts, individual counts, and ballot records.
    """
    audit=audit_flow(H,S,True)
    if not audit['feasible']:raise ValueError('No matching witness for this S')
    H=np.asarray(H);J,I=H.shape;N=increments(S);records=[]
    reconstructed_S=np.zeros_like(H);reconstructed_C=np.zeros_like(H)
    for s in range(J):
        for _ in range(N[s,0]):
            reconstructed_S[s]+=1;records.append((s,[],I))
    for (s,k,n),alloc in zip(audit['groups'],audit['allocation']):
        d=alloc.copy()
        # Bipartite graph with n equal row degrees k; greedily take k largest columns.
        for _ in range(n):
            ids=np.argsort(-d,kind='stable')[:k]
            if np.any(d[ids]<=0):raise AssertionError('Decomposition failed')
            d[ids]-=1
            reconstructed_C.ravel()[ids]+=1
            reconstructed_S[s,:I-k]+=1
            records.append((s,ids.tolist(),I-k))
        assert d.sum()==0
    residual=H-reconstructed_S-reconstructed_C
    for i,n in enumerate(residual.ravel()):
        for _ in range(n):
            reconstructed_C.ravel()[i]+=1;records.append((-1,[i],0))
    assert np.array_equal(H,reconstructed_S+reconstructed_C)
    return reconstructed_S,reconstructed_C,records
