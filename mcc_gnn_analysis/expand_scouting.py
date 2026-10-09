"""Contract-independent scouting ranking; fixed original percentile reference.
Rebootstrap all candidates, including retirement-reported players.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import strengthen as s
P=Path(__file__).resolve().parent; V=P/'v2'

def main():
    old=pd.read_csv(V/'scouting_ranking.csv')
    review=pd.read_csv(V/'availability_review.csv')
    df=old.drop(columns=['availability','available_confirmed','rank_lo','rank_hi','score_lo','score_hi','top5_share','rank_min','rank_max','conditional_rank']).merge(review,on=['player_id','name'],validate='one_to_one')
    df['retirement_reported']=df.status.str.contains('은퇴',na=False)
    df['benchmark_only']=False
    df['candidate_rank']=np.nan
    active=df.sort_values('scout_score',ascending=False).copy()
    active['candidate_rank']=np.arange(1,len(active)+1)
    eligible=active.player_id.astype(str).tolist()
    original_reference=pd.read_csv(V/'role_percentiles.csv',dtype={'player_id':str}).player_id.tolist()
    cols=['minutes']+s.STAT+['three_PM'];games=s.LOG.game_id.unique()
    cube=np.zeros((len(games),len(s.IDS),len(cols)));lookup={g:i for i,g in enumerate(games)}
    for row in s.LOG.itertuples():cube[lookup[row.game_id],s.LOOK[row.player_id]]=[getattr(row,c) for c in cols]
    def score(a):
        prior=a[s.STAT].sum()/max(a.minutes.sum(),1)*36
        r=(a[s.STAT]*36+200*prior)/(a.minutes.values[:,None]+200)
        r['TS']=(a.points+100*a.points.sum()/max(2*(a.FGA.sum()+.44*a.FTA.sum()),1))/(2*(a.FGA+.44*a.FTA)+100)
        r['three_pct']=(a.three_PM+50*a.three_PM.sum()/max(a.three_PA.sum(),1))/(a.three_PA+50)
        r['three_made36']=r.three_PA*r.three_pct;r['rebounds']=r.OREB+r.DREB;r['creation']=r.AST/r.TOV.clip(lower=.1)
        pc=r.loc[original_reference,['TS','points','rebounds','creation','three_made36']].rank(pct=True)
        m=pc.loc[s.MCC];w=(.5-m[['TS','creation','three_made36']]).clip(lower=0);w=w/w.sum() if w.sum()>0 else w*0+1/3
        q=.35*pc.TS+.2*pc.points+.25*pc.rebounds+.2*pc.creation
        c=sum(w[k]*(pc[k]-m[k]).clip(lower=0) for k in w.index)/sum(w[k]*(1-m[k]) for k in w.index)
        return 100*(.6*q+.4*c)
    point=score(pd.DataFrame(cube.sum(0),index=s.IDS,columns=cols)).loc[eligible].values
    assert np.allclose(point,active.scout_score,atol=1e-8)
    rng=np.random.default_rng(s.SEED);bs=[];br=[]
    for b in range(500):
        a=pd.DataFrame(cube[rng.integers(len(games),size=len(games))].sum(0),index=s.IDS,columns=cols)
        v=score(a).loc[eligible];bs.append(v.values);br.append(v.rank(ascending=False,method='min').values)
    bs=np.array(bs);br=np.array(br)
    active['score_lo']=np.quantile(bs,.025,axis=0);active['score_hi']=np.quantile(bs,.975,axis=0)
    active['rank_lo']=np.quantile(br,.025,axis=0);active['rank_hi']=np.quantile(br,.975,axis=0);active['top5_share']=np.mean(br<=5,axis=0)
    sr=[]
    for mix in [.4,.6,.8]:
        v=mix*active.quality_score+(1-mix)*active.complement_score
        rr=v.rank(ascending=False,method='min')
        for i,r in active.iterrows():sr.append({'player_id':r.player_id,'quality_weight':mix,'score':v.loc[i],'rank':rr.loc[i]})
    sensitivity=pd.DataFrame(sr);sens=sensitivity.groupby('player_id')['rank'].agg(['min','max'])
    active['weight_rank_min']=active.player_id.map(sens['min']);active['weight_rank_max']=active.player_id.map(sens['max'])
    active['role_rank']=np.nan;mask=active.screen_pass
    active.loc[mask,'role_rank']=np.arange(1,mask.sum()+1)
    active.to_csv(V/'expanded_scouting_ranking.csv',index=False,encoding='utf-8-sig')
    sensitivity.to_csv(V/'expanded_weight_sensitivity.csv',index=False,encoding='utf-8-sig')
    df[df.benchmark_only].to_csv(V/'benchmark_only.csv',index=False,encoding='utf-8-sig')
    meta={'date':'2026-10-10','candidate_scope':'All recorded foreign players >=200 minutes excluding McCullough; retirement-reported players included by user request','observed_candidates':len(df),'ranked_candidates':len(active),'role_screen_count':int(mask.sum()),'benchmark_only_count':0,'retirement_reported_included':int(df.retirement_reported.sum()),'retirement_filter':False,'contract_filter':False,'contract_in_score':False,'percentile_reference_players':len(original_reference),'bootstrap':500,'bootstrap_unit':'league game, 126 games','reference_fixed':True,'screen_fixed':True,'seed':s.SEED,'point_score_reproduction_max_error':float(np.max(abs(point-active.scout_score.values))),'interpretation':'Analyst policy score, not graph-learned synergy or guaranteed recruitment availability'}
    (V/'expanded_summary.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    print(active[['candidate_rank','name','scout_score','screen_pass']].head(12).to_string(index=False));print(meta)
if __name__=='__main__':main()
