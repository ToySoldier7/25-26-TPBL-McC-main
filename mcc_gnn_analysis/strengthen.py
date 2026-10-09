"""V2: nested validated relational graph kernels; no centrality or clustering.
All training features are computed strictly before each game. Temporal test
features are frozen before the first test game. Cleaned events, not raw API.
"""
from pathlib import Path
import json, hashlib, shutil
import numpy as np
import pandas as pd
import analyze as old

P=Path(__file__).resolve().parent
O=P/'v2';O.mkdir(exist_ok=True)
SEED=20261010
N=old.nodes; IDS=old.ids; LOOK=old.lookup; MCC=old.MCC
FEATURES=old.FEATURES
LOG=old.logs.copy()
STAT=old.STAT
EV=old.read(old.BASE/'pbp_tables/events.csv')
lineups={r.stint_id:set((str(r.leo_ids)+'|'+str(r.opp_ids)).split('|')) for r in old.raw.itertuples()}
off=[]
for e in EV[(EV.event_type!='Rotation')&EV.player_id.notna()&EV.stint_id.notna()].itertuples():
    if e.stint_id in lineups and e.player_id not in lineups[e.stint_id]:off.append(e.stint_id)
S=old.s[~old.s.stint_id.isin(off)].copy().reset_index(drop=True)
IDX=np.array([[LOOK[p] for p in (r.leo_ids+'|'+r.opp_ids).split('|')] for r in S.itertuples()])
MID=np.array([list(row[:5]).index(LOOK[MCC]) for row in IDX])
POOL=np.zeros((len(S),3,10))
for i,j in enumerate(MID):POOL[i,0,j]=1;POOL[i,1,:5]=.25;POOL[i,1,j]=0;POOL[i,2,5:]=.2
CTX=S[['leo_is_home','margin_at_start','sec_remaining_regulation','is_ot']].astype(float).values/np.array([1,20,2880,1])
Y=np.c_[S.margin,S.mcc_PTS]*2160/S.duration_sec.values[:,None]
W=S.duration_sec.values/60
GIDS=sorted(S.game_id.unique(),key=lambda g:old.dates[g])
FI=[FEATURES.index(f) for f in ['points','three_PA','OREB','DREB','AST','BLK','TOV','TS']]

def prior_features(cut,logs=None):
    logs=LOG if logs is None else logs
    g=logs[logs.game_date<cut]
    a=g.groupby('player_id')[['minutes']+STAT+['three_PM']].sum().reindex(IDS).fillna(0)
    prior=g[STAT].sum().values/max(g.minutes.sum(),1)*36
    xx=(a[STAT].values*36+200*prior)/(a.minutes.values[:,None]+200)
    p3=g.three_PM.sum()/max(g.three_PA.sum(),1)
    ts=g.points.sum()/max(2*(g.FGA.sum()+.44*g.FTA.sum()),1)
    xx=np.c_[xx,(a.three_PM+50*p3)/(a.three_PA+50),(a.points+100*ts)/(2*(a.FGA+.44*a.FTA)+100),N.height_cm.values,N[['pos_PG','pos_SG','pos_SF','pos_PF','pos_C','is_imported']].values]
    return xx,a.minutes.values

CACHE={d:prior_features(d)[0] for d in sorted(set(old.dates[g] for g in GIDS))}
RAW=np.array([CACHE[old.dates[r.game_id]][idx] for r,idx in zip(S.itertuples(),IDX)])

def scale_nodes(raw,tr):
    a=raw[tr].reshape(-1,raw.shape[-1]);mu=a.mean(0);sd=a.std(0);sd[sd<1e-8]=1
    return (raw-mu)/sd,mu,sd

def representations(z,pool=POOL,ctx=CTX):
    """Permutation invariant explicit graph feature map, with 3 edge relations.
    Existing fully connected team/opponent topology is fixed across stints;
    the varying information is continuous node and edge attributes.
    """
    roles=np.einsum('sri,sif->srf',pool,z)
    base=np.c_[roles.reshape(len(z),-1),ctx]
    u=roles[:,0,FI];t=roles[:,1,FI];v=roles[:,2,FI]
    # target -> teammate outer products; ordered pairs of other teammates.
    target=np.einsum('si,sj->sij',u,t).reshape(len(z),-1)
    p=pool[:,1]*4
    a=z[:,:,FI]
    sumx=np.einsum('si,sif->sf',p,a)
    sumxx=np.einsum('si,sif,sig->sfg',p,a,a)
    pairs=(np.einsum('sf,sg->sfg',sumx,sumx)-sumxx)/12
    # average squared difference across all own/opponent edges.
    sqown=(z[:,:5,FI]**2).mean(1);sqopp=(z[:,5:,FI]**2).mean(1)
    matchup=sqown+sqopp-2*z[:,:5,FI].mean(1)*v
    return {'Node-RBF':base,'Graph-KRR':np.c_[base,target,pairs.reshape(len(z),-1),matchup],
            'Graph-Ridge':np.c_[base,target,pairs.reshape(len(z),-1),matchup],'Ridge':base}

def standard(x,tr):
    mu=x[tr].mean(0);sd=x[tr].std(0);sd[sd<1e-8]=1
    return (x-mu)/sd,mu,sd
def dists(a,b):return np.maximum((a*a).mean(1)[:,None]+(b*b).mean(1)[None,:]-2*a@b.T/a.shape[1],0)
def solve_model(x,y,w,kind,lam,bw=1):
    wn=w/w.sum();ym=wn@y
    if kind in ['Graph-KRR','Node-RBF']:
        k=np.exp(-dists(x,x)/(2*bw*bw));km=k@wn;grand=wn@km
        kc=k-km[:,None]-km[None,:]+grand;sw=np.sqrt(wn)
        eig,u=np.linalg.eigh(sw[:,None]*kc*sw[None,:]);b=u.T@(sw[:,None]*(y-ym))
        alpha=sw[:,None]*(u@(b/(np.maximum(eig,0)+lam)[:,None]))
        return dict(kind=kind,x=x,alpha=alpha,wn=wn,km=km,grand=grand,ym=ym,bw=bw)
    xm=wn@x;xx=x-xm;pen=np.eye(x.shape[1])*lam
    coef=np.linalg.solve(xx.T@(wn[:,None]*xx)+pen,xx.T@(wn[:,None]*(y-ym)))
    return dict(kind=kind,coef=coef,xm=xm,ym=ym)
def predict(m,x):
    if m['kind'] in ['Graph-KRR','Node-RBF']:
        k=np.exp(-dists(x,m['x'])/(2*m['bw']**2));kc=k-(k@m['wn'])[:,None]-m['km'][None,:]+m['grand']
        return kc@m['alpha']+m['ym']
    return (x-m['xm'])@m['coef']+m['ym']
GRID=[(.001,b) for b in [.5,1,2]]+[(l,b) for l in [.01,.1,1,10] for b in [.5,1,2]]
def tune(raw,tr,kind):
    gs=np.array(sorted(S.game_id.iloc[tr].unique()));gs=gs[np.random.default_rng(SEED).permutation(len(gs))]
    options=GRID if kind in ['Graph-KRR','Node-RBF'] else [(l,1) for l in [.01,.1,1,10,100]]
    err=np.zeros(len(options));den=0
    for held in np.array_split(gs,3):
        va=tr[S.game_id.iloc[tr].isin(held)];tt=tr[~S.game_id.iloc[tr].isin(held)]
        z,_,_=scale_nodes(raw,tt);feat=representations(z)[kind];feat,_,_=standard(feat,tt)
        for j,(lam,bw) in enumerate(options):
            m=solve_model(feat[tt],Y[tt],W[tt],kind,lam,bw);pred=predict(m,feat[va])
            err[j]+=np.sum(W[va]*(pred[:,0]-Y[va,0])**2)
        den+=W[va].sum()
    pick=int(np.argmin(err));return options[pick],float(np.sqrt(err[pick]/den))

def evaluate():
    rng=np.random.default_rng(SEED);g=np.array(GIDS)[rng.permutation(len(GIDS))]
    splits=[('group_nested',i,list(v)) for i,v in enumerate(np.array_split(g,5))]+[('temporal_frozen',0,GIDS[-8:])]
    rec=[];configs=[];man=[]
    for typ,fold,held in splits:
        te=np.flatnonzero(S.game_id.isin(held));tr=np.flatnonzero(~S.game_id.isin(held));raw=RAW.copy()
        if typ=='temporal_frozen':
            cut=old.dates[held[0]];xcut,_=prior_features(cut)
            raw[te]=xcut[IDX[te]]
            assert all(old.dates[g]<cut for g in S.game_id.iloc[tr])
        z,mu,sd=scale_nodes(raw,tr);maps=representations(z)
        predictions={'Mean':np.tile(np.average(Y[tr],axis=0,weights=W[tr]),(len(te),1))}
        for kind in ['Ridge','Node-RBF','Graph-Ridge','Graph-KRR']:
            (lam,bw),inner=tune(raw,tr,kind)
            f,_,_=standard(maps[kind],tr);m=solve_model(f[tr],Y[tr],W[tr],kind,lam,bw)
            predictions[kind]=predict(m,f[te]);configs.append(dict(split=typ,fold=fold,model=kind,lambda_=lam,bandwidth=bw,inner_net_rmse=inner))
        # The original architecture and fixed hyperparameters on the same clean,
        # pre-game data; three seeds. It is a historical comparator, not tuned v2.
        dz=np.concatenate([z,np.einsum('ij,sjf->sif',old.AT,z),np.einsum('ij,sjf->sif',old.AO,z)],2)
        pred=[]
        for seed in range(3):
            m=old.GNN(dz.shape[-1],old.SEED+seed).fit(dz[tr],POOL[tr],CTX[tr],Y[tr]/old.SCALE,W[tr])
            pred.append(m.forward(dz[te],POOL[te],CTX[te])[0]*old.SCALE)
        predictions['GNN-v1']=np.mean(pred,axis=0)
        for label,p in predictions.items():
            for j,i in enumerate(te):rec.append(dict(split=typ,fold=fold,model=label,stint_id=S.stint_id.iloc[i],game_id=S.game_id.iloc[i],weight=W[i],net_actual=Y[i,0],mcc_actual=Y[i,1],net_pred=p[j,0],mcc_pred=p[j,1]))
        man.extend([dict(split=typ,fold=fold,game_id=gg,role=role) for role,gs in [('train',S.game_id.iloc[tr].unique()),('test',held)] for gg in gs])
        print('nested validation',typ,fold,flush=True)
    pd.DataFrame(man).to_csv(O/'splits.csv',index=False)
    pd.DataFrame(configs).to_csv(O/'hyperparameters.csv',index=False)
    p=pd.DataFrame(rec);p.to_csv(O/'predictions.csv',index=False);metrics=[]
    for (typ,label),df in p.groupby(['split','model']):
        rm=np.sqrt(np.average((df[['net_actual','mcc_actual']].values-df[['net_pred','mcc_pred']].values)**2,weights=df.weight,axis=0))
        metrics.append(dict(split=typ,model=label,net_rmse=rm[0],mcc_rmse=rm[1],games=df.game_id.nunique()))
    metrics=pd.DataFrame(metrics);metrics.to_csv(O/'metrics.csv',index=False)
    # Paired bootstrap; labels/predictions held fixed, game as resampling unit.
    ci=[]
    for typ in p.split.unique():
        a=p[(p.split==typ)&(p.model=='Graph-KRR')].set_index('stint_id')
        for other in ['GNN-v1','Mean','Ridge','Node-RBF','Graph-Ridge']:
            b=p[(p.split==typ)&(p.model==other)].set_index('stint_id').loc[a.index]
            for target in ['net','mcc']:
                v=(a[target+'_actual']-a[target+'_pred'])**2-(b[target+'_actual']-b[target+'_pred'])**2
                t=pd.DataFrame({'g':a.game_id,'num':v*a.weight,'den':a.weight}).groupby('g')[['num','den']].sum().values
                idx=rng.integers(len(t),size=(2000,len(t)));bt=t[idx].sum(1);dist=bt[:,0]/bt[:,1]
                ci.append(dict(split=typ,target=target,versus=other,mse_delta=t[:,0].sum()/t[:,1].sum(),lo=np.quantile(dist,.025),hi=np.quantile(dist,.975)))
    pd.DataFrame(ci).to_csv(O/'paired_comparisons.csv',index=False)
    return metrics

def final_graph():
    tr=np.arange(len(S));kind='Graph-KRR';(lam,bw),inner=tune(RAW,tr,kind)
    z,mu,sd=scale_nodes(RAW,tr);fm=representations(z)[kind];fm,fmu,fsd=standard(fm,tr)
    model=solve_model(fm,Y,W,kind,lam,bw)
    # Full-season retrospective inference, shared opponent *feature* contexts.
    latest,mins=prior_features('2026-10-10');fullz=(latest[IDX]-mu)/sd
    imp=np.flatnonzero((N.is_imported.values==1)&(mins>=200)&(N.player_id.values!=MCC))
    slots=[];keep=[]
    for i,row in enumerate(IDX):
        sl=[j for j,n in enumerate(row[:5]) if IDS[n]!=MCC and N.iloc[n].is_imported==1]
        if len(sl)==1:keep.append(i);slots.append(sl[0])
    keep=np.array(keep);slots=np.array(slots)
    basez=fullz[keep];pool=POOL[keep];ctx=CTX[keep]
    def fnew(a):return (representations(a,pool,ctx)[kind]-fmu)/fsd
    base=predict(model,fnew(basez))
    # Fixed selected hyperparameters; bootstrap coefficient refit conditional on
    # fixed past-only features/scalers, not bootstrap of the entire selection.
    rng=np.random.default_rng(SEED);bootmodels=[]
    for k in range(100):
        sampled=rng.choice(GIDS,len(GIDS));counts=pd.Series(sampled).value_counts();weights=W*S.game_id.map(counts).fillna(0).values
        bootmodels.append(solve_model(fm,Y,weights,kind,lam,bw))
    baseline=[predict(m,fnew(basez)) for m in bootmodels]
    rows=[];allboot=[]
    for c in imp:
        zz=basez.copy();zz[np.arange(len(zz)),slots]=(latest[c]-mu)/sd
        f=fnew(zz);delta=np.average(predict(model,f)-base,weights=W[keep],axis=0)
        bs=np.array([np.average(predict(m,f)-b,weights=W[keep],axis=0) for m,b in zip(bootmodels,baseline)])
        nearest=np.sqrt(dists(f,fm).min(1));allboot.append(bs[:,0])
        rows.append(dict(player_id=IDS[c],name=old.name[IDS[c]],graph_net_delta=delta[0],graph_mcc_delta=delta[1],graph_lo=np.quantile(bs[:,0],.025),graph_hi=np.quantile(bs[:,0],.975),feature_distance=np.average(nearest,weights=W[keep]),contexts=len(keep)))
    gr=pd.DataFrame(rows).sort_values('graph_net_delta',ascending=False);gr.to_csv(O/'graph_counterfactuals.csv',index=False)
    # Feature-type sensitivity: +0.5 training SD one feature at a time. Hypothesis,
    # not a physically possible or causal intervention; an explicit local test.
    types=[]
    for j,feat in enumerate(FEATURES[:12]):
        zz=basez.copy();zz[np.arange(len(zz)),slots,j]+=.5
        f=fnew(zz);bs=np.array([np.average(predict(m,f)-b,weights=W[keep],axis=0) for m,b in zip(bootmodels,baseline)])
        d=np.average(predict(model,f)-base,weights=W[keep],axis=0)
        types.append(dict(feature=feat,net_delta=d[0],mcc_delta=d[1],lo=np.quantile(bs[:,0],.025),hi=np.quantile(bs[:,0],.975)))
    pd.DataFrame(types).to_csv(O/'type_sensitivity.csv',index=False)
    np.savez(O/'graph_model.npz',train_x=fm,alpha=model['alpha'],wn=model['wn'],km=model['km'],grand=model['grand'],ym=model['ym'],bandwidth=bw,lambda_=lam,node_mu=mu,node_sd=sd,feature_mu=fmu,feature_sd=fsd,features=np.array(FEATURES))
    return gr,latest,mins,dict(lambda_=lam,bandwidth=bw,inner_rmse=inner,contexts=len(keep))

def scouting(graph,latest,mins):
    """Transparent KBL roster-policy ranking, NOT graph-estimated KBL performance.
    No Samsung domestic lineup data exist; avoid fabricated single-import outcome.
    """
    agg=LOG.groupby('player_id')[['minutes']+STAT+['three_PM']].sum().reindex(IDS).fillna(0)
    idx=np.flatnonzero((N.is_imported.values==1)&(mins>=200))
    pp=pd.DataFrame(latest[idx,:12],columns=FEATURES[:12],index=[IDS[i] for i in idx])
    # Shooting volume is made threes, avoiding 0/0 shrunk accuracy artefacts.
    pp['three_made36']=pp.three_PA*pp.three_pct
    pp['rebounds']=pp.OREB+pp.DREB;pp['creation']=pp.AST/pp.TOV.clip(lower=.1)
    pcs=pp[['TS','points','rebounds','creation','three_made36']].rank(pct=True,method='average')
    mcc=pcs.loc[MCC];deficit=(.5-mcc[['TS','creation','three_made36']]).clip(lower=0)
    dw=deficit/deficit.sum() if deficit.sum()>0 else deficit*0+1/3
    # Explicit fixed decision weights, no fit to test rankings.
    quality=.35*pcs.TS+.2*pcs.points+.25*pcs.rebounds+.2*pcs.creation
    complement=sum(dw[c]*(pcs[c]-mcc[c]).clip(lower=0) for c in dw.index)
    # Max gap-normalized opportunity score stays in [0,1].
    complement/=sum(dw[c]*(1-mcc[c]) for c in dw.index)
    score=100*(.6*quality+.4*complement)
    rows=[]
    for i in idx:
        if IDS[i]==MCC:continue
        p=IDS[i];r=agg.loc[p];rr=pp.loc[p]
        eligible=mins[i]>=400 and N.iloc[i].height_cm>=198 and rr.rebounds>=8
        rows.append(dict(player_id=p,name=old.name[p],team_in_dataset=N.iloc[i].team_name_english,position=N.iloc[i].position,height_cm=N.iloc[i].height_cm,minutes=mins[i],screen_pass=eligible,screen_reason='통과' if eligible else '400분·198cm·축소 REB36 8 기준 일부 미충족',scout_score=score[p],quality_score=quality[p]*100,complement_score=complement[p]*100,pts36=36*r.points/r.minutes,reb36=36*(r.OREB+r.DREB)/r.minutes,ast36=36*r.AST/r.minutes,tov36=36*r.TOV/r.minutes,three_made=int(r.three_PM),three_attempts=int(r.three_PA),three_pct=r.three_PM/r.three_PA if r.three_PA>0 else None,ts=r.points/(2*(r.FGA+.44*r.FTA)),creation=rr.creation,availability='미확인',available_confirmed=False))
    df=pd.DataFrame(rows).merge(graph,on=['player_id','name'],how='left')
    df=df.sort_values(['screen_pass','scout_score'],ascending=False).reset_index(drop=True)
    df['conditional_rank']=None;df.loc[df.screen_pass,'conditional_rank']=np.arange(1,df.screen_pass.sum()+1)
    # Policy sensitivity, not probabilistic rank uncertainty.
    ss=[]
    for qweight in [.4,.6,.8]:
        v=100*(qweight*quality+(1-qweight)*complement)
        elig=df[df.screen_pass].player_id
        ranks=v.loc[elig].rank(ascending=False,method='min')
        for p in elig:ss.append(dict(player_id=p,quality_weight=qweight,score=v[p],rank=ranks[p]))
    ss=pd.DataFrame(ss);ss.to_csv(O/'scout_weight_sensitivity.csv',index=False)
    r=ss.groupby('player_id')['rank'].agg(['min','max']);df['rank_min']=df.player_id.map(r['min']);df['rank_max']=df.player_id.map(r['max'])
    df.to_csv(O/'scouting_ranking.csv',index=False)
    pc=pcs.copy();pc['name']=[old.name[p] for p in pc.index];pc.to_csv(O/'role_percentiles.csv',index_label='player_id')
    pol={'purpose':'conditional KBL rotation-scouting policy, not model-validated synergy','quality_weights':{'TS':.35,'points':.2,'rebounds':.25,'creation':.2},'quality_mix':.6,'complement_mix':.4,'mcc_percentiles':mcc.to_dict(),'deficit_weights':dw.to_dict(),'screen':{'minutes':400,'height_cm':198,'shrunk_reb36':8},'availability_in_score':False,'contract_and_budget_known':False}
    (O/'scouting_policy.json').write_text(json.dumps(pol,ensure_ascii=False,indent=2),encoding='utf-8')
    # Sampling stability of a fixed policy and fixed screen, all league games.
    eligible=df.loc[df.screen_pass,'player_id'].tolist();allgames=LOG.game_id.unique()
    statcols=['minutes']+STAT+['three_PM']
    tensor=np.zeros((len(allgames),len(IDS),len(statcols)))
    gm={g:i for i,g in enumerate(allgames)}
    for row in LOG.itertuples():
        tensor[gm[row.game_id],LOOK[row.player_id]]=np.array([getattr(row,c) for c in statcols])
    rng=np.random.default_rng(SEED);branks=[];bscores=[]
    for b in range(500):
        vals=tensor[rng.integers(len(allgames),size=len(allgames))].sum(0)
        aa=pd.DataFrame(vals,index=IDS,columns=statcols);prior=aa[STAT].sum()/aa.minutes.sum()*36
        rr=(aa[STAT]*36+200*prior)/(aa.minutes.values[:,None]+200)
        rr['TS']=(aa.points+100*(aa.points.sum()/(2*(aa.FGA.sum()+.44*aa.FTA.sum()))))/(2*(aa.FGA+.44*aa.FTA)+100)
        rr['three_pct']=(aa.three_PM+50*aa.three_PM.sum()/aa.three_PA.sum())/(aa.three_PA+50)
        rr['three_made36']=rr.three_PA*rr.three_pct;rr['rebounds']=rr.OREB+rr.DREB;rr['creation']=rr.AST/rr.TOV.clip(lower=.1)
        ppb=rr.loc[pp.index,['TS','points','rebounds','creation','three_made36']].rank(pct=True)
        mm=ppb.loc[MCC];dw2=(.5-mm[['TS','creation','three_made36']]).clip(lower=0)
        dw2=dw2/dw2.sum() if dw2.sum()>0 else dw2*0+1/3
        qq=.35*ppb.TS+.2*ppb.points+.25*ppb.rebounds+.2*ppb.creation
        cc=sum(dw2[c]*(ppb[c]-mm[c]).clip(lower=0) for c in dw2.index)/sum(dw2[c]*(1-mm[c]) for c in dw2.index)
        ssb=100*(.6*qq+.4*cc);bb=ssb.loc[eligible]
        bscores.append(bb.values);branks.append(bb.rank(ascending=False,method='min').values)
    branks=np.array(branks);bscores=np.array(bscores)
    boot=pd.DataFrame({'player_id':eligible,'score_lo':np.quantile(bscores,.025,axis=0),'score_hi':np.quantile(bscores,.975,axis=0),'rank_lo':np.quantile(branks,.025,axis=0),'rank_hi':np.quantile(branks,.975,axis=0),'top5_share':np.mean(branks<=5,axis=0)})
    boot.to_csv(O/'scout_bootstrap.csv',index=False)
    df=df.merge(boot,on='player_id',how='left');df.to_csv(O/'scouting_ranking.csv',index=False)
    return df

def checks():
    # Outcome-period perturbation must not alter a game's pre-game covariates.
    cut=old.dates[GIDS[-8]];alter=LOG.copy();alter.loc[alter.game_date>=cut,STAT+['three_PM','minutes']]*=100
    leak=np.max(abs(prior_features(cut)[0]-prior_features(cut,alter)[0]));assert leak==0
    tr=np.arange(len(S));z,_,_=scale_nodes(RAW,tr);feat=representations(z)['Graph-KRR']
    perm=np.array([3,0,4,2,1,9,7,5,8,6]);f2=representations(z[:,perm],POOL[:,:,perm],CTX)['Graph-KRR']
    inv=float(np.max(abs(feat-f2)));assert inv<1e-9
    k=np.exp(-dists(feat[:40],feat[:40])/2);mineig=float(np.linalg.eigvalsh(k).min());assert mineig>-1e-8
    assert S.stint_id.is_unique and np.isfinite(RAW).all() and np.isfinite(Y).all()
    return dict(heldout_stat_perturbation_max=leak,permutation_max=inv,kernel_min_eigenvalue=mineig)

def main():
    test=checks();metrics=evaluate();graph,latest,mins,cfg=final_graph();rank=scouting(graph,latest,mins)
    S.to_csv(O/'analysis_stints.csv',index=False)
    old.s[old.s.stint_id.isin(off)].to_csv(O/'excluded_stints.csv',index=False)
    allreg=old.raw[(old.raw.competition_phase=='regular_season')&old.raw.use&(old.raw.duration_sec>=30)&~old.raw.garbage_time&~old.raw.stint_id.isin(off)].copy()
    im=set(N[N.is_imported==1].player_id);allreg['import_count']=allreg.leo_ids.str.split('|').apply(lambda a:len(set(a)&im))
    support=allreg.groupby('import_count').agg(stints=('stint_id','size'),minutes=('duration_sec',lambda x:x.sum()/60));support.to_csv(O/'import_count_support.csv')
    meta={'date':'2026-10-10','seed':SEED,'stints':len(S),'games':S.game_id.nunique(),'minutes':W.sum(),'removed_stints':len(old.s)-len(S),'feature_timing':'strictly earlier calendar date; temporal test frozen at first test date','temporal_cutoff':old.dates[GIDS[-8]],'node_features':len(FEATURES),'graph_features':197,'candidate_count':len(rank),'screened_count':int(rank.screen_pass.sum()),'checks':test,'final_graph':cfg,'model_selection':'nested 3-fold tuning inside five outer game folds; temporal holdout also inner-tuned','caution':'old holdout was previously inspected; temporal test is reused retrospective evidence, not untouched new-season confirmation','sources':{str(f.relative_to(P.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [old.DATA/'stint_graphs.csv',old.DATA/'nodes.csv',old.BASE/'input_data/player_game_logs.csv',old.BASE/'pbp_tables/events.csv']}}
    (O/'run_summary.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    print(metrics.to_string(index=False),flush=True);print(rank[['name','screen_pass','scout_score','graph_net_delta']].head(12).to_string(index=False),flush=True)
if __name__=='__main__':main()
