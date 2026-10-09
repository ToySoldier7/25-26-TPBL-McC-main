"""Reproducible CPU/NumPy relational GNN and conservative graph-transfer analysis.
Run with Python 3.12, numpy, pandas. No downloaded model or season outcome features.
"""
from pathlib import Path
import json, hashlib, sys, math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
BASE = ROOT/'GNN' if (ROOT/'GNN').is_dir() else ROOT/'25-26-TPBL-McC-main/GNN'
DATA = BASE/'output_data/gnn_dataset'
SEED=20261004
MCC='10860'
def read(path):
    return pd.read_csv(path, dtype={'player_id':str,'game_id':str,'team_id':str})
nodes=read(DATA/'nodes.csv').sort_values('node_idx').reset_index(drop=True)
logs=read(BASE/'input_data/player_game_logs.csv')
logs=logs[(logs.competition_phase=='regular_season') & (logs.minutes>0)].copy()
games=read(BASE/'input_data/games.csv')
dates=games.set_index('game_id').game_date.to_dict()
raw=read(DATA/'stint_graphs.csv')
eligible=raw[(raw.competition_phase=='regular_season') & raw.use & raw.mcc_on].copy()
s=eligible[(eligible.duration_sec>=30)&~eligible.garbage_time].copy().reset_index(drop=True)
ids=nodes.player_id.tolist(); lookup={p:i for i,p in enumerate(ids)}
name=dict(zip(ids,nodes.player_name_english.fillna(nodes.player_name_original)))
SIDS=np.array([[lookup[p] for p in (a+'|'+b).split('|')] for a,b in zip(s.leo_ids,s.opp_ids)])
MID=np.array([list(x[:5]).index(lookup[MCC]) for x in SIDS])
CTX=s[['leo_is_home','margin_at_start','sec_remaining_regulation','is_ot']].astype(float).values
CTX=CTX/np.array([1,20,2880,1])
Y=np.c_[s.margin.values,s.mcc_PTS.values]*2160/s.duration_sec.values[:,None]
W=s.duration_sec.values/60
SCALE=np.array([40.,25.])
AT=np.zeros((10,10)); AO=np.zeros((10,10))
for i in range(10):
    for j in range(10):
        if i!=j and (i<5)==(j<5): AT[i,j]=.25
        elif (i<5)!=(j<5): AO[i,j]=.2
POOL=np.zeros((len(s),3,10))
for k,m in enumerate(MID):
    POOL[k,0,m]=1; POOL[k,1,:5]=.25; POOL[k,1,m]=0; POOL[k,2,5:]=.2

STAT=['points','FGA','three_PA','FTA','OREB','DREB','AST','STL','BLK','TOV']
FEATURES=STAT+['three_pct','TS','height','pos_PG','pos_SG','pos_SF','pos_PF','pos_C','is_imported']
def features(excluded=(), before=None):
    """Aggregate only allowed box scores; holdout games cannot affect features/prior."""
    g=logs[~logs.game_id.isin(excluded)]
    if before is not None: g=g[g.game_date<before]
    agg=g.groupby('player_id')[['minutes']+STAT+['three_PM']].sum().reindex(ids).fillna(0)
    prior=g[STAT].sum().values/max(g.minutes.sum(),1)*36
    x=(agg[STAT].values*36+200*prior)/(agg.minutes.values[:,None]+200)
    p3=g.three_PM.sum()/max(g.three_PA.sum(),1)
    ts=g.points.sum()/max(2*(g.FGA.sum()+.44*g.FTA.sum()),1)
    x=np.c_[x,(agg.three_PM+50*p3)/(agg.three_PA+50),
            (agg.points+100*ts)/(2*(agg.FGA+.44*agg.FTA)+100),
            nodes.height_cm.fillna(nodes.height_cm.median()),nodes[['pos_PG','pos_SG','pos_SF','pos_PF','pos_C','is_imported']].fillna(0)]
    mu=x.mean(0); sd=x.std(0); sd[sd<1e-8]=1
    return (x-mu)/sd,x,agg.minutes.values

def design(x, idx=SIDS, edges=True):
    z=x[idx]
    if edges: return np.concatenate([z,np.einsum('ij,sjf->sif',AT,z),np.einsum('ij,sjf->sif',AO,z)],axis=2)
    return np.concatenate([z,np.zeros_like(z),np.zeros_like(z)],axis=2)

class GNN:
    """One trainable relational message-passing layer + role readout, tanh, Adam.
    H=tanh(X Wself + AT X Wteam + AO X Wopp + b).
    Readout concatenates target, teammate mean, opponent mean and start context.
    """
    def __init__(self,d,seed=SEED,h=8):
        r=np.random.default_rng(seed)
        self.p={'a':r.normal(0,.12,(d,h)),'b':np.zeros(h),'v':r.normal(0,.08,(3*h+4,2)),'c':np.zeros(2)}
    def forward(self,z,pool,ctx):
        h=np.tanh(z@self.p['a']+self.p['b'])
        q=np.c_[np.einsum('sri,sih->srh',pool,h).reshape(len(z),-1),ctx]
        return q@self.p['v']+self.p['c'],(h,q)
    def loss_grad(self,z,pool,ctx,y,w,reg=.02):
        pred,(h,q)=self.forward(z,pool,ctx)
        diff=pred-y; wn=w/w.sum(); loss=np.sum(wn[:,None]*diff**2)/2
        dy=diff*wn[:,None]
        dq=(dy@self.p['v'][:-4].T).reshape(len(z),3,-1)
        dh=np.einsum('sri,srh->sih',pool,dq)*(1-h*h)
        grad={'a':np.einsum('sif,sih->fh',z,dh),'b':dh.sum((0,1)),'v':q.T@dy,'c':dy.sum(0)}
        for k in ('a','v'):
            loss+=reg*np.sum(self.p[k]**2)/2; grad[k]+=reg*self.p[k]
        return loss,grad
    def fit(self,z,pool,ctx,y,w,epochs=220):
        m={k:np.zeros_like(v) for k,v in self.p.items()}; v={k:a.copy() for k,a in m.items()}
        for t in range(1,epochs+1):
            loss,g=self.loss_grad(z,pool,ctx,y,w)
            for k in self.p:
                m[k]=.9*m[k]+.1*g[k]; v[k]=.999*v[k]+.001*g[k]**2
                self.p[k]-=.008*(m[k]/(1-.9**t))/(np.sqrt(v[k]/(1-.999**t))+1e-8)
        return self

def flat(x):
    z=x[SIDS]
    return np.c_[np.einsum('sri,sif->srf',POOL,z).reshape(len(s),-1),CTX]
def ridge_fit(x,y,w,lam=1):
    x=np.c_[np.ones(len(x)),x]; w=w/w.sum()
    pen=np.eye(x.shape[1])*lam; pen[0,0]=0
    return np.linalg.solve(x.T@(w[:,None]*x)+pen,x.T@(w[:,None]*y))
def ridge_predict(x,b):return np.c_[np.ones(len(x)),x]@b
def metric(y,p,w): return np.sqrt(np.average((y-p)**2,axis=0,weights=w))

def gradient_check():
    x,_,_=features(); z=design(x)[:4]; model=GNN(z.shape[-1]); y=Y[:4]/SCALE
    _,g=model.loss_grad(z,POOL[:4],CTX[:4],y,W[:4]); errors=[]
    for k in model.p:
        for j in [0,model.p[k].size-1]:
            old=model.p[k].flat[j]; eps=1e-5
            model.p[k].flat[j]=old+eps; a=model.loss_grad(z,POOL[:4],CTX[:4],y,W[:4])[0]
            model.p[k].flat[j]=old-eps; b=model.loss_grad(z,POOL[:4],CTX[:4],y,W[:4])[0]
            model.p[k].flat[j]=old
            errors.append(abs((a-b)/(2*eps)-g[k].flat[j]))
    assert max(errors)<1e-6,errors
    # Node ordering has no analytical meaning: permute within each side.
    perm=np.array([4,2,0,3,1,7,9,5,8,6])
    assert np.allclose(model.forward(z,POOL[:4],CTX[:4])[0],model.forward(z[:,perm],POOL[:4,:,perm],CTX[:4])[0])
    return max(errors)

def evaluate():
    gids=sorted(s.game_id.unique(),key=lambda g:dates[g]); shuffled=np.array(gids)[np.random.default_rng(SEED).permutation(len(gids))]
    splits=[('group_cv',i,list(v),None) for i,v in enumerate(np.array_split(shuffled,5))]
    splits += [('temporal',0,gids[-8:],dates[gids[-8:][0]])]
    predictions=[]; metrics=[]; splitrows=[]
    for typ,fold,testg,cut in splits:
        te=np.flatnonzero(s.game_id.isin(testg)); tr=np.flatnonzero(~s.game_id.isin(testg))
        if cut: tr=np.array([i for i in tr if dates[s.game_id.iloc[i]]<cut])
        excluded=testg if cut is None else []
        x,_,_=features(excluded,before=cut); d=design(x); f=flat(x)
        assert not set(s.game_id.iloc[tr])&set(s.game_id.iloc[te])
        pred={'Mean':np.tile(np.average(Y[tr],axis=0,weights=W[tr]),(len(te),1))}
        # Fixed hyperparameters, not selected on these test folds.
        b=ridge_fit(f[tr],Y[tr]/SCALE,W[tr]); pred['Ridge']=ridge_predict(f[te],b)*SCALE
        for label,edge in [('GNN',True),('No-edge NN',False)]:
            d=design(x,edges=edge); vals=[]
            for seed in range(3):
                m=GNN(d.shape[-1],SEED+seed).fit(d[tr],POOL[tr],CTX[tr],Y[tr]/SCALE,W[tr])
                vals.append(m.forward(d[te],POOL[te],CTX[te])[0]*SCALE)
            pred[label]=np.mean(vals,axis=0)
        for label,p in pred.items():
            rmse=metric(Y[te],p,W[te]); metrics.append(dict(split=typ,fold=fold,model=label,net_rmse36=rmse[0],mcc_rmse36=rmse[1]))
            for j,i in enumerate(te):
                predictions.append(dict(split=typ,fold=fold,model=label,stint_id=s.stint_id.iloc[i],game_id=s.game_id.iloc[i],weight=W[i],net_actual=Y[i,0],mcc_actual=Y[i,1],net_pred=p[j,0],mcc_pred=p[j,1]))
        for i in tr: splitrows.append(dict(split=typ,fold=fold,game_id=s.game_id.iloc[i],role='train'))
        for i in te: splitrows.append(dict(split=typ,fold=fold,game_id=s.game_id.iloc[i],role='test'))
        print('Completed',typ,fold,flush=True)
    p=pd.DataFrame(predictions); p.to_csv(OUT/'predictions.csv',index=False)
    pd.DataFrame(metrics).to_csv(OUT/'fold_metrics.csv',index=False)
    pd.DataFrame(splitrows).drop_duplicates().to_csv(OUT/'split_manifest.csv',index=False)
    summary=[]
    for (typ,label),g in p.groupby(['split','model']):
        a=metric(g[['net_actual','mcc_actual']].values,g[['net_pred','mcc_pred']].values,g.weight)
        summary.append(dict(split=typ,model=label,net_rmse36=a[0],mcc_rmse36=a[1],games=g.game_id.nunique()))
    result=pd.DataFrame(summary); result.to_csv(OUT/'model_metrics.csv',index=False)
    # Paired game bootstrap on squared-error differences: negative favours GNN.
    ci=[]; rng=np.random.default_rng(SEED)
    for typ in ['group_cv','temporal']:
        gp=p[(p.split==typ)&(p.model=='GNN')].set_index('stint_id')
        for other in ['Mean','Ridge','No-edge NN']:
            op=p[(p.split==typ)&(p.model==other)].set_index('stint_id').loc[gp.index]
            d=(gp.net_pred-gp.net_actual)**2-(op.net_pred-op.net_actual)**2
            temp=pd.DataFrame({'game':gp.game_id,'num':d*gp.weight,'den':gp.weight}).groupby('game')[['num','den']].sum().values
            draw=rng.integers(len(temp),size=(2000,len(temp))); boot=temp[draw].sum(1); vals=boot[:,0]/boot[:,1]
            ci.append(dict(split=typ,comparison='GNN minus '+other,mse_difference=temp[:,0].sum()/temp[:,1].sum(),lo=np.quantile(vals,.025),hi=np.quantile(vals,.975)))
    pd.DataFrame(ci).to_csv(OUT/'model_difference_bootstrap.csv',index=False)
    return result,ci

def graph_analysis():
    """Observed star graph with game-bootstrap; transfer is an explicitly heuristic kernel."""
    partners=sorted(set('|'.join(s.leo_ids).split('|'))-{MCC})
    masks=np.array([[p in a.split('|') for a in s.leo_ids] for p in partners]).T
    gids=s.game_id.unique(); ng=len(gids); rows=[]
    # game × partner × [minutes, margin, mcc points, poss, FGM assisted, FGM, TSA]
    cols=np.c_[W,s.margin,s.mcc_PTS,s.poss_avg,s.mcc_FGM_assisted,s.mcc_FGM,s.mcc_TSA]
    tensor=np.array([masks[s.game_id==g].T@cols[s.game_id==g] for g in gids])
    totals=tensor.sum(0); overall=cols.sum(0); prior=120.
    rng=np.random.default_rng(SEED); draws=rng.integers(ng,size=(2000,ng)); bt=tensor[draws].sum(1)
    gt=np.array([cols[s.game_id==g].sum(0) for g in gids]); bg=gt[draws].sum(1)
    rates=(totals[:,1]*36+prior*overall[1]*36/overall[0])/(totals[:,0]+prior)
    br=(bt[:,:,1]*36+prior*(bg[:,1]*36/bg[:,0])[:,None])/(bt[:,:,0]+prior)
    for j,p in enumerate(partners):
        t=totals[j]; off=overall-t
        bootraw=np.divide(bt[:,j,1]*36,bt[:,j,0],out=np.full(len(bt),np.nan),where=bt[:,j,0]>0)
        rows.append(dict(player_id=p,name=name[p],imported=int(nodes.iloc[lookup[p]].is_imported),minutes=t[0],games=int((tensor[:,j,0]>0).sum()),net36=t[1]*36/t[0],net100=t[1]*100/t[3] if t[3]>0 else np.nan,mcc_points36=t[2]*36/t[0],mcc_TS=t[2]/(2*t[6]) if t[6]>0 else np.nan,assisted_share=t[4]/t[5] if t[5]>0 else np.nan,raw_lo=np.nanquantile(bootraw,.025),raw_hi=np.nanquantile(bootraw,.975),shrunk_net36=rates[j],shrunk_lo=np.quantile(br[:,j],.025),shrunk_hi=np.quantile(br[:,j],.975),on_off_net36=t[1]*36/t[0]-off[1]*36/off[0] if off[0]>0 else np.nan))
    obs=pd.DataFrame(rows).sort_values('shrunk_net36',ascending=False); obs.to_csv(OUT/'observed_partners.csv',index=False)
    x,rawx,mins=features(); fi=[FEATURES.index(a) for a in ['three_PA','OREB','DREB','AST','BLK','TOV','three_pct','TS']]
    imp=np.flatnonzero((nodes.is_imported.values==1)&(mins>=200)&(nodes.player_id.values!=MCC))
    anchors=[j for j,p in enumerate(partners) if nodes.iloc[lookup[p]].is_imported==1 and totals[j,0]>=30]
    anchoridx=[lookup[partners[j]] for j in anchors]
    dist=np.sqrt(np.mean((x[imp,None,:][:,:,fi]-x[anchoridx,:][None,:,fi])**2,axis=2))
    # Gaussian edges in bipartite graph: candidate -> 3 observed import anchors.
    kernel=np.exp(-.5*(dist/1.)**2); kernel/=kernel.sum(1,keepdims=True)
    estimates=kernel@rates[anchors]; btrans=br[:,anchors]@kernel.T
    mccrate=(totals[:,2]*36+prior*overall[2]*36/overall[0])/(totals[:,0]+prior)
    mcc_transfer=kernel@mccrate[anchors]
    ranks=np.argsort(np.argsort(-btrans,axis=1),axis=1)+1
    transfers=[]; edges=[]
    for j,i in enumerate(imp):
        transfers.append(dict(player_id=ids[i],name=name[ids[i]],team=nodes.iloc[i].team_name_english,minutes=mins[i],observed_partner=ids[i] in partners,transfer_score=estimates[j],mcc_points_transfer=mcc_transfer[j],lo=np.quantile(btrans[:,j],.025),hi=np.quantile(btrans[:,j],.975),p_top5=np.mean(ranks[:,j]<=5),nearest_anchor=name[partners[anchors[np.argmin(dist[j])]]],distance=dist[j].min(),max_anchor_weight=kernel[j].max()))
        for a,k,d in zip(anchors,kernel[j],dist[j]):edges.append(dict(candidate=ids[i],anchor=partners[a],weight=k,distance=d))
    trans=pd.DataFrame(transfers).sort_values('transfer_score',ascending=False); trans.to_csv(OUT/'candidate_transfer.csv',index=False)
    pd.DataFrame(edges).to_csv(OUT/'transfer_edges.csv',index=False)
    # Sensitivity to graph edge bandwidth and shrinkage prior.
    sens=[]
    for prior in [60,120,240]:
        rr=(totals[:,1]*36+prior*overall[1]*36/overall[0])/(totals[:,0]+prior)
        for bw in [.5,1,2]:
            kk=np.exp(-.5*(dist/bw)**2); kk/=kk.sum(1,keepdims=True); score=kk@rr[anchors]
            rank=np.argsort(np.argsort(-score))+1
            for j,i in enumerate(imp):sens.append(dict(player_id=ids[i],prior_minutes=prior,bandwidth=bw,score=score[j],rank=rank[j]))
    pd.DataFrame(sens).to_csv(OUT/'transfer_sensitivity.csv',index=False)
    # Include vs exclude very short / garbage stints as a separate observed check.
    sensitivity=[]
    for label,df in [('all_valid',eligible),('primary',s)]:
        for p in [partners[a] for a in anchors]:
            a=df[df.leo_ids.str.split('|').apply(lambda v:p in v)]
            sensitivity.append(dict(filter=label,player_id=p,name=name[p],minutes=a.duration_sec.sum()/60,net36=a.margin.sum()*2160/a.duration_sec.sum(),mcc_points36=a.mcc_PTS.sum()*2160/a.duration_sec.sum()))
    pd.DataFrame(sensitivity).to_csv(OUT/'filter_sensitivity.csv',index=False)
    # Direct import anchor contrasts; not adjusted causal effects.
    contrasts=[]
    for ai,a in enumerate(anchors):
        for b in anchors[ai+1:]:
            v=br[:,a]-br[:,b]
            contrasts.append(dict(a=name[partners[a]],b=name[partners[b]],difference=rates[a]-rates[b],lo=np.quantile(v,.025),hi=np.quantile(v,.975)))
    pd.DataFrame(contrasts).to_csv(OUT/'partner_contrasts.csv',index=False)
    return obs,trans,overall

def gnn_hypotheses():
    """Counterfactual replacement illustration, not a validated player-ranking target."""
    x,rx,mins=features(); imp=np.flatnonzero((nodes.is_imported.values==1)&(mins>=200)&(nodes.player_id.values!=MCC))
    slots=[]; keep=[]
    for i,line in enumerate(SIDS):
        slot=[j for j,n in enumerate(line[:5]) if ids[n]!=MCC and nodes.iloc[n].is_imported==1]
        if len(slot)==1:keep.append(i); slots.append(slot[0])
    keep=np.array(keep); slots=np.array(slots); z=design(x)
    models=[]; rng=np.random.default_rng(SEED); gs=s.game_id.unique()
    for k in range(5):
        sampled=rng.choice(gs,len(gs),replace=True); counts=pd.Series(sampled).value_counts()
        w=W*s.game_id.map(counts).fillna(0).values
        m=GNN(z.shape[-1],SEED+100+k).fit(z,POOL,CTX,Y/SCALE,w)
        models.append(m); np.savez(OUT/f'gnn_model_{k}.npz',**m.p)
    rows=[]
    for c in imp:
        ok=np.array([c not in SIDS[i,5:] for i in keep]); ix=keep[ok]; sl=slots[ok]
        ixnew=SIDS[ix].copy(); ixnew[np.arange(len(ix)),sl]=c
        zz=design(x,ixnew); base=z[ix]; estimates=[]
        for m in models:
            diff=(m.forward(zz,POOL[ix],CTX[ix])[0]-m.forward(base,POOL[ix],CTX[ix])[0])*SCALE
            estimates.append(np.average(diff,axis=0,weights=W[ix]))
        a=np.array(estimates)
        rows.append(dict(player_id=ids[c],name=name[ids[c]],net_delta36=a[:,0].mean(),net_min=a[:,0].min(),net_max=a[:,0].max(),mcc_points_delta36=a[:,1].mean(),contexts=len(ix),note='exploratory bootstrap-model range; not confidence interval or causal effect'))
    pd.DataFrame(rows).sort_values('net_delta36',ascending=False).to_csv(OUT/'gnn_hypotheses.csv',index=False)
    np.savez(OUT/'final_feature_state.npz',x=x,raw_features=rx,player_ids=np.array(ids),features=np.array(FEATURES))

def main():
    assert nodes.player_id.is_unique and nodes.node_idx.is_unique
    assert s.stint_id.is_unique and len(s)==len(SIDS)
    assert all(len(set(row))==10 for row in SIDS)
    assert np.isfinite(Y).all() and np.isfinite(CTX).all()
    assert np.allclose(s.margin,s.leo_pts-s.opp_pts)
    assert not logs.duplicated(['game_id','player_id']).any()
    err=gradient_check(); print('Gradient and permutation checks passed',err,flush=True)
    metrics,ci=evaluate(); obs,trans,overall=graph_analysis(); gnn_hypotheses()
    audit={'seed':SEED,'nodes':len(nodes),'regular_mcc_games':eligible.game_id.nunique(),'regular_stints':len(eligible),'regular_minutes':eligible.duration_sec.sum()/60,'analysis_stints':len(s),'analysis_minutes':W.sum(),'candidate_imports_min200':len(trans),'game_dates':[min(dates[g] for g in s.game_id),max(dates[g] for g in s.game_id)],'gradient_max_abs_error':err,'primary_target':'team net points per36','secondary_target':'McCullough points per36','overall_net36':overall[1]*36/overall[0],'bootstrap_replicates':2000,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [DATA/'stint_graphs.csv',DATA/'nodes.csv',BASE/'input_data/player_game_logs.csv']}}
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf-8')
    s.to_csv(OUT/'analysis_stints.csv',index=False)
    print(metrics.to_string(index=False)); print(obs[['name','minutes','net36','shrunk_net36','shrunk_lo','shrunk_hi']].to_string(index=False)); print(trans.head(8).to_string(index=False))
if __name__=='__main__':main()
