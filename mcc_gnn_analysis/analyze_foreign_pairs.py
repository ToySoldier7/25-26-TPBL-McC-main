"""Observed McCullough pairs and TPBL import role profiles.

Outputs are retrospective associations. No neural predictions or recruiting
policy scores enter the pair comparison. Game is the resampling unit.
"""
from pathlib import Path
import hashlib, itertools, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'GNN'
OUT=ROOT/'foreign_pair_analysis'
FIG=OUT/'figures'
OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
SEED=20261010;B=5000;MCC=10860
PARTNERS=[68,16,10861]
COLORS={68:'#176A80',16:'#8E6C8A',10861:'#C57A36'}
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':12,'savefig.dpi':180})

def read(f):return pd.read_csv(f)
def save(df,f):df.to_csv(OUT/f,index=False,encoding='utf-8-sig')
def ratio(a,b,scale=1):
    return np.divide(scale*np.asarray(a,dtype=float),np.asarray(b,dtype=float),out=np.full(np.broadcast_shapes(np.shape(a),np.shape(b)),np.nan),where=np.asarray(b)>0)
def quant(x):return np.nanquantile(x,[.025,.975],axis=0)

nodes=read(BASE/'output_data/gnn_dataset/nodes.csv')
names=nodes.set_index('player_id').player_name_english.to_dict()
foreign=set(nodes.loc[nodes.is_imported==1,'player_id'])
raw=read(BASE/'output_data/gnn_dataset/stint_graphs.csv')
events=read(BASE/'pbp_tables/events.csv')
games=read(BASE/'input_data/games.csv')
logs=read(BASE/'input_data/player_game_logs.csv')
logs=logs[(logs.competition_phase=='regular_season')&(logs.minutes>0)].copy()
lineups={r.stint_id:set(int(v) for v in (r.leo_ids+'|'+r.opp_ids).split('|')) for r in raw.itertuples() if isinstance(r.leo_ids,str) and isinstance(r.opp_ids,str)}
bad=set()
for r in events[(events.event_type!='Rotation')&events.player_id.notna()&events.stint_id.notna()].itertuples():
    if r.stint_id in lineups and int(r.player_id) not in lineups[r.stint_id]:bad.add(r.stint_id)
clean=raw[(raw.competition_phase=='regular_season')&raw.use&~raw.stint_id.isin(bad)].copy()
clean['partner_id']=clean.leo_ids.map(lambda ids:next((int(v) for v in ids.split('|') if int(v) in foreign and int(v)!=MCC),-1))
clean['import_count']=clean.leo_ids.map(lambda ids:sum(int(v) in foreign for v in ids.split('|')))
primary=clean[clean.mcc_on&(clean.duration_sec>=30)&~clean.garbage_time].copy()
assert set(primary.stint_id)==set(read(ROOT/'v2/analysis_stints.csv').stint_id)
assert primary.import_count.le(2).all()
S=primary[primary.partner_id.isin(PARTNERS)].copy().reset_index(drop=True)
S['minutes']=S.duration_sec/60
S['game_date']=S.game_id.map(games.set_index('game_id').game_date)

cols=['minutes','leo_pts','opp_pts','margin','leo_poss','opp_poss','poss_avg','mcc_PTS','mcc_FGA','mcc_FTA','mcc_FGM','mcc_3PM','mcc_3PA','mcc_FGM_assisted','mcc_AST','mcc_TOV','mcc_OREB','mcc_DREB','mcc_TSA','mcc_rim_FGA','mcc_rim_FGM','mcc_usage_poss']
col={v:i for i,v in enumerate(cols)}
def metrics(a):
    g=lambda c:a[...,col[c]]
    return dict(minutes=g('minutes'),net36=ratio(g('margin'),g('minutes'),36),net100=ratio(g('margin'),g('poss_avg'),100),
        team_pts100=ratio(g('leo_pts'),g('poss_avg'),100),opponent_pts100=ratio(g('opp_pts'),g('poss_avg'),100),
        ortg=ratio(g('leo_pts'),g('leo_poss'),100),drtg=ratio(g('opp_pts'),g('opp_poss'),100),
        mcc_pts36=ratio(g('mcc_PTS'),g('minutes'),36),mcc_ts=ratio(g('mcc_PTS'),2*g('mcc_TSA')),
        mcc_fga36=ratio(g('mcc_FGA'),g('minutes'),36),mcc_fta36=ratio(g('mcc_FTA'),g('minutes'),36),
        mcc_ast36=ratio(g('mcc_AST'),g('minutes'),36),mcc_tov36=ratio(g('mcc_TOV'),g('minutes'),36),
        mcc_reb36=ratio(g('mcc_OREB')+g('mcc_DREB'),g('minutes'),36),
        mcc_assisted_share=ratio(g('mcc_FGM_assisted'),g('mcc_FGM')),
        mcc_rim_share=ratio(g('mcc_rim_FGA'),g('mcc_FGA')),mcc_rim_pct=ratio(g('mcc_rim_FGM'),g('mcc_rim_FGA')),
        mcc_usage_proxy=ratio(g('mcc_usage_poss'),g('leo_poss')),mcc_team_point_share=ratio(g('mcc_PTS'),g('leo_pts')))

gids=np.array(sorted(S.game_id.unique()));pididx={p:i for i,p in enumerate(PARTNERS)}
tensor=np.zeros((len(gids),3,len(cols)))
for i,g in enumerate(gids):
    for p,j in pididx.items():tensor[i,j]=S.loc[(S.game_id==g)&(S.partner_id==p),cols].sum().values
rng=np.random.default_rng(SEED);draws=rng.integers(len(gids),size=(B,len(gids)))
boot_tensor=tensor[draws].sum(1);point=metrics(tensor.sum(0));boots=metrics(boot_tensor)
rows=[]
for p,j in pididx.items():
    ss=S[S.partner_id==p];r={'partner_id':p,'partner':names[p],'stints':len(ss),'games':ss.game_id.nunique(),'first_date':ss.game_date.min(),'last_date':ss.game_date.max()}
    r.update({c:float(tensor[:,j,col[c]].sum()) for c in cols if c!='minutes'})
    for k,v in point.items():
        r[k]=float(v[j]);lo,hi=quant(boots[k][:,j]);r[k+'_lo']=float(lo);r[k+'_hi']=float(hi)
    rows.append(r)
summary=pd.DataFrame(rows);save(summary,'pair_summary.csv')
gg=S.groupby(['game_id','game_date','partner_id'])[cols].sum().reset_index()
gm=metrics(gg[cols].values)
for k,v in gm.items():gg[k]=v
gg['partner']=gg.partner_id.map(names);save(gg,'pair_by_game.csv')

# Descriptive contrasts and within-game comparisons. Each game must provide
# exposure to both partners. Harmonic exposure gives low weight to tiny cells.
out=[];within_details=[]
for a,b in itertools.combinations(PARTNERS,2):
    ia,ib=pididx[a],pididx[b]
    for key in ['net36','net100','mcc_pts36','mcc_ts','mcc_fga36','mcc_assisted_share']:
        lo,hi=quant(boots[key][:,ia]-boots[key][:,ib])
        out.append(dict(method='all_games_unadjusted',min_shared_minutes=0,a=names[a],b=names[b],metric=key,difference=point[key][ia]-point[key][ib],lo=lo,hi=hi,games=len(gids)))
    for min_minutes in [0,2,5]:
        valid=(tensor[:,ia,col['minutes']]>min_minutes)&(tensor[:,ib,col['minutes']]>min_minutes)
        tt=tensor[valid];ng=len(tt)
        for key in ['net36','net100','mcc_pts36','mcc_ts']:
            den='poss_avg' if key=='net100' else ('mcc_TSA' if key=='mcc_ts' else 'minutes')
            da=tt[:,ia,col[den]];db=tt[:,ib,col[den]]
            w=ratio(da*db,da+db)
            met=metrics(tt);d=met[key][:,ia]-met[key][:,ib];ok=np.isfinite(d)&np.isfinite(w)&(w>0)
            ww=w[ok];dd=d[ok];ids=gids[valid][ok]
            if len(dd)<2:continue
            ix=rng.integers(len(dd),size=(B,len(dd)));dist=(ww[ix]*dd[ix]).sum(1)/ww[ix].sum(1)
            lo,hi=quant(dist)
            out.append(dict(method='within_same_game_harmonic_weight',min_shared_minutes=min_minutes,a=names[a],b=names[b],metric=key,difference=np.average(dd,weights=ww),lo=lo,hi=hi,games=len(dd)))
            if min_minutes==2:
                within_details.extend(dict(a=names[a],b=names[b],game_id=g,metric=key,difference=dv,weight=wv) for g,dv,wv in zip(ids,dd,ww))
comparisons=pd.DataFrame(out);save(comparisons,'pair_comparisons.csv');save(pd.DataFrame(within_details),'within_game_details.csv')

# Game fixed effects, with and without measured context/domestic teammate controls.
# All outcome and design variables are demeaned within game, using duration.
# Coefficients are conditional associations. These are not predictive models.
regrows=[];reg_audit=[]
for spec in ['game_FE','game_FE_context_domestic']:
    x=pd.DataFrame({'Miller':(S.partner_id==16).astype(float),'Diallo':(S.partner_id==10861).astype(float)})
    if spec.endswith('domestic'):
        for q in [2,3,4,5]:
            if (S.quarter==q).any():x[f'quarter_{q}']=(S.quarter==q).astype(float)
        x['margin_at_start']=S.margin_at_start/20
        x['sec_remaining_regulation']=S.sec_remaining_regulation/2880
        domestic=sorted(set(int(v) for ids in S.leo_ids for v in ids.split('|'))-foreign)
        exposure={p:S.loc[S.leo_ids.map(lambda ids:str(p) in ids.split('|')),'minutes'].sum() for p in domestic}
        # Common domestic players only, to avoid fitting one-game/6-minute
        # nuisance indicators in a 24-game cluster bootstrap. The most-used
        # domestic player is the reference. Rare lineups remain a limitation.
        reference=max(domestic,key=lambda p:exposure[p])
        for p in domestic:
            if p!=reference and exposure[p]>=60:x[f'domestic_{p}']=S.leo_ids.map(lambda ids:float(str(p) in ids.split('|')))
    y=np.c_[ratio(S.mcc_PTS,S.minutes,36),ratio(S.margin,S.minutes,36)]
    xx=x.values;w=S.minutes.values;xd=np.empty_like(xx);yd=np.empty_like(y)
    for g in gids:
        m=S.game_id.values==g;xd[m]=xx[m]-np.average(xx[m],axis=0,weights=w[m]);yd[m]=y[m]-np.average(y[m],axis=0,weights=w[m])
    xtx=np.array([xd[S.game_id.values==g].T@(w[S.game_id.values==g,None]*xd[S.game_id.values==g]) for g in gids])
    xty=np.array([xd[S.game_id.values==g].T@(w[S.game_id.values==g,None]*yd[S.game_id.values==g]) for g in gids])
    coef=np.linalg.pinv(xtx.sum(0),rcond=1e-10)@xty.sum(0)
    # Entire fitted game effects and coefficients are recomputed in each draw.
    beta=[];ranks=[]
    for ix in draws[:2000]:
        a=xtx[ix].sum(0);ranks.append(np.linalg.matrix_rank(a));beta.append(np.linalg.pinv(a,rcond=1e-10)@xty[ix].sum(0))
    beta=np.array(beta)
    contrast={(68,16):np.array([-1.,0.]),(68,10861):np.array([0.,-1.]),(16,10861):np.array([1.,-1.])}
    for (a,b),v in contrast.items():
        cc=np.r_[v,np.zeros(x.shape[1]-2)]
        for k,key in enumerate(['mcc_pts36','net36']):
            dist=beta[:,:,k]@cc;lo,hi=quant(dist)
            regrows.append(dict(spec=spec,a=names[a],b=names[b],metric=key,difference=cc@coef[:,k],lo=lo,hi=hi,bootstrap=2000))
    reg_audit.append(dict(spec=spec,columns=x.columns.tolist(),columns_count=x.shape[1],point_rank=int(np.linalg.matrix_rank(xtx.sum(0))),bootstrap_rank_min=int(min(ranks)),full_rank_bootstrap_share=float(np.mean(np.array(ranks)==x.shape[1]))))
reg=pd.DataFrame(regrows);save(reg,'adjusted_contrasts.csv')

# Assist links provide direct observed interaction counts, not a causal mechanism.
ev=events[events.stint_id.isin(S.stint_id)].copy();st_to_p=S.set_index('stint_id').partner_id.to_dict();ev['partner_id']=ev.stint_id.map(st_to_p)
links=[]
for p in PARTNERS:
    e=ev[ev.partner_id==p];mins=float(summary.set_index('partner_id').loc[p,'minutes'])
    m=(e.player_id==MCC)&e.is_fga&e.is_made
    p_to_m=e[m&(e.assist_by==p)]
    m_to_p=e[(e.player_id==p)&e.is_fga&e.is_made&(e.assist_by==MCC)]
    linked_mcc=int((m&e.assist_by.notna()).sum());assert linked_mcc==int(summary.set_index('partner_id').loc[p,'mcc_FGM_assisted'])
    links.append(dict(partner_id=p,partner=names[p],minutes=mins,partner_to_mcc_fg_assists=len(p_to_m),partner_to_mcc_assisted_points=p_to_m.points.sum(),partner_to_mcc_fg_assists36=36*len(p_to_m)/mins,mcc_to_partner_fg_assists=len(m_to_p),all_mcc_assisted_fg=linked_mcc,mcc_FGM=int(m.sum())))
assist=pd.DataFrame(links);save(assist,'direct_assist_links.csv')

sp=read(BASE/'pbp_tables/stint_players.csv')
shared=sp.merge(S[['stint_id','partner_id','minutes']],on='stint_id',validate='many_to_one')
partner_stats=[]
for p in PARTNERS:
    ss=shared[(shared.partner_id==p)&(shared.player_id==p)]
    assert len(ss)==int((S.partner_id==p).sum())
    minutes=S.loc[S.partner_id==p,'minutes'].sum()
    partner_stats.append(dict(partner=names[p],minutes=minutes,partner_pts36=36*ss.PTS.sum()/minutes,
        partner_ast36=36*ss.AST.sum()/minutes,partner_reb36=36*(ss.OREB.sum()+ss.DREB.sum())/minutes,
        partner_fga36=36*ss.FGA.sum()/minutes,partner_ts=float(ratio(ss.PTS.sum(),2*(ss.FGA.sum()+.44*ss.FTA.sum())))))
save(pd.DataFrame(partner_stats),'partner_production_in_pairs.csv')

# Filter sensitivity, recomputed after the same off-court-event exclusion.
sens=[]
variants={'all_clean_non_garbage':clean[clean.mcc_on&~clean.garbage_time],
          'primary_30s_non_garbage':primary,
          'min60s_non_garbage':clean[clean.mcc_on&(clean.duration_sec>=60)&~clean.garbage_time],
          'min30s_include_garbage':clean[clean.mcc_on&(clean.duration_sec>=30)]}
for label,ss in variants.items():
    ss=ss.copy();ss['minutes']=ss.duration_sec/60
    for p in PARTNERS:
        v=ss[ss.partner_id==p];m=metrics(v[cols].sum().values)
        sens.append(dict(filter=label,partner=names[p],stints=len(v),games=v.game_id.nunique(),**{k:float(m[k]) for k in ['minutes','net36','net100','mcc_pts36','mcc_ts']}))
sensitivity=pd.DataFrame(sens);save(sensitivity,'filter_sensitivity.csv')

# TPBL-wide observed role profiles. All 48 imports are output. The comparison
# reference is 36 imports >=200 minutes to avoid letting tiny samples define roles.
stats=['points','FGA','three_PA','three_PM','FTA','OREB','DREB','AST','TOV','BLK','STL','source_field_goals_attempted_in_the_paint']
agg=logs.groupby('player_id')[['minutes']+stats].sum()
prior=agg[stats].sum()/agg.minutes.sum()*36
shr=(36*agg[stats]+200*prior)/(agg.minutes.values[:,None]+200)
shr['reb36']=shr.OREB+shr.DREB;shr['three_rate']=shr.three_PA/shr.FGA
shr['paint_rate']=shr.source_field_goals_attempted_in_the_paint/shr.FGA
shr['ast_tov']=shr.AST/shr.TOV.clip(lower=.1)
league_ts=agg.points.sum()/(2*(agg.FGA.sum()+.44*agg.FTA.sum()))
league_3=agg.three_PM.sum()/agg.three_PA.sum()
shr['ts']=(agg.points+100*league_ts)/(2*(agg.FGA+.44*agg.FTA)+100)
shr['three_pct']=(agg.three_PM+50*league_3)/(agg.three_PA+50)
shr['three_made36']=shr.three_PA*shr.three_pct
profile=nodes.loc[nodes.is_imported==1,['player_id','player_name_english','team_name_english','position','height_cm']].merge(agg,left_on='player_id',right_index=True,validate='one_to_one')
profile=profile.rename(columns={'player_name_english':'name','team_name_english':'team'})
for c in ['points','FGA','FTA','AST','TOV','BLK','STL']:profile['shr_'+c+'36']=profile.player_id.map(shr[c])
for c in ['reb36','three_rate','paint_rate','ast_tov','ts','three_pct','three_made36']:profile['shr_'+c]=profile.player_id.map(shr[c])
for c in ['points','AST','TOV','BLK','STL']:profile[c.lower()+'36']=36*profile[c]/profile.minutes
profile['reb36']=36*(profile.OREB+profile.DREB)/profile.minutes
profile['three_pct']=ratio(profile.three_PM,profile.three_PA)
profile['ts']=profile.points/(2*(profile.FGA+.44*profile.FTA));profile['ast_tov']=profile.AST/profile.TOV
profile['reference_200min']=profile.minutes>=200
ref=profile[profile.reference_200min].copy();assert len(profile)==48 and len(ref)==36
axes={'creation':'shr_AST36','shooting':'shr_three_made36','rebounding':'shr_reb36','blocking':'shr_BLK36','steals':'shr_STL36','efficiency':'shr_ts','shot_usage':'shr_FGA36','paint':'shr_paint_rate','ball_security':'shr_ast_tov'}
for label,c in axes.items():
    ranked=ref.set_index('player_id')[c].rank(pct=True)*100
    profile[label+'_pctile']=profile.player_id.map(ranked)
    small=~profile.reference_200min
    profile.loc[small,label+'_pctile']=[100*np.mean(ref[c].values<=v) for v in profile.loc[small,c]]
    profile[label+'_all48_pctile']=profile[c].rank(pct=True)*100

def tags(r):
    t=[]
    if r.creation_pctile>=75:t.append('공격 전개')
    if r.shooting_pctile>=75:t.append('외곽 생산')
    if r.rebounding_pctile>=75:t.append('리바운드')
    if r.paint_pctile>=75:t.append('페인트존 슛 비중')
    if r.blocking_pctile>=75:t.append('블록 기여')
    if r.steals_pctile>=75:t.append('스틸 기여')
    if r.efficiency_pctile>=75:t.append('득점 효율')
    if r.shot_usage_pctile<=25:t.append('낮은 슛 사용량')
    return ' / '.join(t) if t else '뚜렷한 상위 사분위 특성 없음'
profile['role_tags']=profile.apply(tags,axis=1)
subtypes={68:'공격 전개와 슛 사용량이 큰 윙',16:'블록 기여가 크고 슛 사용량이 낮은 윙',10861:'인사이드 마무리와 리바운드 중심 빅맨',10860:'리바운드와 슛 사용량이 큰 빅맨'}
profile['target_interpretation']=profile.player_id.map(subtypes).fillna('')

# Exploratory clusters are a check on whether sharp type boundaries are supported.
# We do not force three partners into three distinct clusters.
cluster_features=['shr_three_rate','shr_paint_rate','shr_AST36','shr_reb36','shr_BLK36','shr_STL36','shr_FGA36']
mu=ref[cluster_features].mean();sd=ref[cluster_features].std(ddof=0)
x=((ref[cluster_features]-mu)/sd).values
selection=[];models={}
for k in range(2,7):
    model=KMeans(n_clusters=k,n_init=100,random_state=SEED).fit(x);models[k]=model
    selection.append(dict(k=k,silhouette=silhouette_score(x,model.labels_),inertia=model.inertia_))
selection=pd.DataFrame(selection);save(selection,'cluster_selection.csv')
k=int(selection.loc[selection.silhouette.idxmax(),'k']);model=models[k]
allx=((profile[cluster_features]-mu)/sd).values
profile['exploratory_cluster']=model.predict(allx)
centers=pd.DataFrame(model.cluster_centers_,columns=cluster_features)
centers['cluster']=np.arange(k);save(centers,'cluster_centers_standardized.csv')
for j in range(k):
    rr=ref.iloc[np.flatnonzero(model.labels_==j)]
    label='공격 전개 중심 그룹' if rr.shr_AST36.mean()>ref.shr_AST36.mean() else '리바운드·인사이드 기여 그룹'
    profile.loc[profile.exploratory_cluster==j,'exploratory_cluster_label']=label
save(profile.sort_values('minutes',ascending=False),'tpbl_import_profiles_all48.csv')
target=profile[profile.player_id.isin([MCC]+PARTNERS)].copy();save(target,'target_role_profiles.csv')
distance=np.sqrt(((allx[:,None]-allx[None,:])**2).mean(2));neighbors=[]
for p in PARTNERS:
    i=int(np.flatnonzero(profile.player_id.values==p)[0])
    js=[j for j in np.argsort(distance[i]) if j!=i and profile.iloc[j].reference_200min][:5]
    for rank,j in enumerate(js,1):neighbors.append(dict(partner=names[p],neighbor_rank=rank,neighbor=profile.iloc[j]['name'],distance=distance[i,j]))
save(pd.DataFrame(neighbors),'role_neighbors.csv')

audit={'seed':SEED,'game_bootstrap':B,'adjustment_bootstrap':2000,'role_profile_observed_imports':48,'role_reference_imports_min200':36,'league_games':int(logs.game_id.nunique()),'league_teams':int(logs.team_id.nunique()),
 'primary_mcc_games':int(primary.game_id.nunique()),'primary_mcc_stints':len(primary),'primary_mcc_minutes':float(primary.duration_sec.sum()/60),
 'pair_only_stints':len(S),'pair_only_minutes':float(S.minutes.sum()),'excluded_single_import_stints':int((primary.import_count==1).sum()),'excluded_single_import_minutes':float(primary.loc[primary.import_count==1,'duration_sec'].sum()/60),
 'off_court_event_stints_removed_from_mcc_30s_non_garbage':int(raw[(raw.competition_phase=='regular_season')&raw.use&raw.mcc_on&(raw.duration_sec>=30)&~raw.garbage_time].stint_id.isin(bad).sum()),
 'regression_audit':reg_audit,'exploratory_cluster_selected_k':k,'exploratory_cluster_silhouette':float(selection.silhouette.max()),'cluster_features':cluster_features,
 'meaning':'Retrospective observed associations, not causal uplift or prospective prediction. Role tags use >=75th percentile; low shot usage uses <=25th percentile. Blocks/steals are event production, not complete defensive ability. Adjusted domestic indicators only for players with >=60 shared minutes, with most-used domestic player omitted as reference.',
 'possessions':'Box-score estimate FGA-OREB+TOV+0.44FTA. net100 uses mean own/opponent possessions; ORtg/DRtg use separate own/opponent denominators.',
 'within_game':'Same game harmonic exposure weighted pair differences; minimum exposure variants 0/2/5 minutes. TS weights use shot-attempt-equivalent exposure.',
 'sources':{str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'output_data/gnn_dataset/stint_graphs.csv',BASE/'output_data/gnn_dataset/nodes.csv',BASE/'input_data/player_game_logs.csv',BASE/'pbp_tables/events.csv',BASE/'pbp_tables/stint_players.csv']}}
(OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')

def figsave(fig,name):
    fig.savefig(FIG/(name+'.png'),bbox_inches='tight',facecolor='white');fig.savefig(FIG/(name+'.svg'),bbox_inches='tight',facecolor='white');plt.close(fig)
labels=['McCullough + Kromah','McCullough + Miller','McCullough + Diallo']
fig,axs=plt.subplots(1,3,figsize=(15.6,5.5),layout='constrained')
for ax,key,title in zip(axs,['net100','mcc_pts36','mcc_ts'],['팀 순득실 / 추정 100포제션','맥컬러 득점 / 36분','맥컬러 TS%']):
    for i,p in enumerate(PARTNERS):
        r=summary[summary.partner_id==p].iloc[0];scale=100 if key=='mcc_ts' else 1
        val=r[key]*scale;lo=r[key+'_lo']*scale;hi=r[key+'_hi']*scale
        ax.errorbar(val,2-i,xerr=[[val-lo],[hi-val]],fmt='o',color=COLORS[p],capsize=5,markersize=8)
        ax.annotate(f'{val:.1f}',(val,2-i),xytext=(0,12),textcoords='offset points',ha='center',fontweight='bold')
    ax.set_yticks([2,1,0],[names[p] for p in PARTNERS]);ax.set_title(title,pad=22,fontweight='bold');ax.set_ylim(-.5,2.55);ax.grid(axis='x',alpha=.2)
    if key=='net100':ax.axvline(0,color='#78838A',linestyle='--',lw=1)
fig.suptitle('팀 순득실은 Diallo, 맥컬러 개인 득점·효율은 Kromah 조합에서 가장 높음',fontsize=17,fontweight='bold')
fig.supxlabel('점: 관측 집계값 / 선: 경기 단위 5,000회 재표집의 2.5~97.5% 구간',fontsize=11)
figsave(fig,'01_pair_outcomes')

wf=comparisons[(comparisons.method=='within_same_game_harmonic_weight')&(comparisons.min_shared_minutes==2)&(comparisons.a=='Lasannah Kromah')]
fig,axs=plt.subplots(1,2,figsize=(11.5,4.8),layout='constrained')
for ax,key,title in zip(axs,['mcc_pts36','net100'],['맥컬러 득점 차이 / 36분','팀 순득실 차이 / 추정 100포제션']):
    rr=wf[wf.metric==key]
    for i,r in enumerate(rr.itertuples()):
        ax.errorbar(r.difference,1-i,xerr=[[r.difference-r.lo],[r.hi-r.difference]],fmt='o',color='#176A80',capsize=5,markersize=8)
        ax.annotate(f'{r.difference:+.1f} (n={r.games})',(r.difference,1-i),xytext=(0,13),textcoords='offset points',ha='center')
    ax.set_yticks([1,0],['Kromah - Miller','Kromah - Diallo']);ax.set_ylim(-.5,1.55);ax.axvline(0,color='#78838A',ls='--');ax.set_title(title,pad=20,fontweight='bold');ax.grid(axis='x',alpha=.2)
fig.suptitle('같은 경기 안에서 파트너를 비교한 결과',fontsize=17,fontweight='bold')
fig.supxlabel('두 조합 모두 2분 초과 출전한 경기 / 노출량 조화 가중 / 경기 재표집 95% 구간 / 인과효과 아님',fontsize=10)
figsave(fig,'02_within_game_comparisons')

axkeys=['creation','shooting','rebounding','blocking','efficiency','shot_usage','ball_security']
axlabs=['공격 전개\nAST/36','외곽 생산\n3PM/36','리바운드\nREB/36','블록 기여\nBLK/36','득점 효율\nTS','슛 사용량\nFGA/36','패스/실책\nAST/TOV']
tr=target.set_index('player_id').loc[PARTNERS]
mat=tr[[a+'_pctile' for a in axkeys]].values
fig,ax=plt.subplots(figsize=(12.3,4.8),layout='constrained');im=ax.imshow(mat,vmin=0,vmax=100,cmap='YlGnBu',aspect='auto')
ax.set_xticks(range(len(axkeys)),axlabs);ax.set_yticks(range(3),[names[p] for p in PARTNERS]);ax.set_title('세 파트너의 역할 프로필은 서로 다름',fontsize=18,pad=20,fontweight='bold')
for i in range(3):
    for j in range(len(axkeys)):ax.text(j,i,f'{mat[i,j]:.0f}',ha='center',va='center',color='white' if mat[i,j]>=65 else '#182C3A',fontsize=16,fontweight='bold')
fig.colorbar(im,ax=ax,label='36명 참조집단 내 백분위',shrink=.8)
fig.supxlabel('정규시즌 외국인 48명 전원 산출 / 비교 기준은 200분 이상 36명 / 출전량에 따른 축소 추정',fontsize=11)
figsave(fig,'03_partner_role_profiles')

fig,ax=plt.subplots(figsize=(10.8,6.8),layout='constrained')
refplot=profile[profile.reference_200min];ax.scatter(refplot.shr_AST36,refplot.shr_reb36,color='#AAB6C0',s=45,alpha=.7)
for p in [MCC]+PARTNERS:
    r=target[target.player_id==p].iloc[0];c=COLORS.get(p,'#233341');ax.scatter(r.shr_AST36,r.shr_reb36,s=150,color=c,edgecolor='white',linewidth=1.2,zorder=3);ax.annotate(r['name'],(r.shr_AST36,r.shr_reb36),xytext=(9,8),textcoords='offset points',color=c,fontweight='bold')
ax.set_xlabel('공격 전개: 축소 AST/36분');ax.set_ylabel('리바운드: 축소 REB/36분');ax.grid(alpha=.2);ax.set_title('Kromah는 공격 전개, Diallo는 리바운드에서 차별화',fontsize=18,pad=20,fontweight='bold');fig.supxlabel('회색 점: 정규시즌 200분 이상 외국인 36명. 두 축만 표시하므로 전체 유형을 대체하지 않음.',fontsize=10)
figsave(fig,'04_tpbl_role_map')

print('PAIR SUMMARY');print(summary[['partner','minutes','games','net36','net100','mcc_pts36','mcc_ts','mcc_assisted_share']].round(4).to_string(index=False))
print('\nSAME GAME');print(wf[['a','b','metric','difference','lo','hi','games']].round(4).to_string(index=False))
print('\nADJUSTED');print(reg.round(4).to_string(index=False))
print('\nDIRECT ASSISTS');print(assist.to_string(index=False))
print('\nTARGET TYPES');print(target[['name','points36','reb36','ast36','three_pct','ts','role_tags','exploratory_cluster_label']].round(4).to_string(index=False))
print('\nFILTER SENSITIVITY');print(sensitivity.round(4).to_string(index=False))
print('\nCLUSTER SELECTION');print(selection.to_string(index=False))
