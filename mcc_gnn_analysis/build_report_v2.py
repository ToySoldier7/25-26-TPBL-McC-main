"""Build the revised report and apply the user's strict confirmed-free-agent gate.
All scouting scores are descriptive policy scores, never GNN predictions.
"""
from pathlib import Path
import sys, json, html, shutil
P=Path(__file__).resolve().parent; V=P/'v2'; F=V/'figures'; F.mkdir(exist_ok=True)
sys.path.insert(0,str(P/'_viz_packages'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#ffffff','axes.facecolor':'#ffffff','savefig.facecolor':'#ffffff'})

# Evidence records: a reported signing is exclusion evidence, not a legal contract audit.
# No old release, NBA-only FA label, missing roster entry, or generic agency availability
# is sufficient to establish worldwide free agency as of the review date.
evidence={
10887:('재계약 보도','2026-07-01 Lioneers 재계약 보도','https://udn.com/news/amp/story/7003/9600477'),
10890:('재계약 보도','2026-07 Dreamers 재계약','https://www.asia-basket.com/Taiwan/news/1004345/Thompkins-re-signs-at-Dreamers'),
8889:('공식 영입 발표','2026-08-19 Fubon 영입 발표','https://pleagueofficial.com/news-detail/895'),
10881:('공식 계약 발표','2026-07-28 Torun 2026/27 계약 발표','https://twardepierniki.pl/posts/viktor-gaddefors-wraca-do-torunia/413'),
10861:('영입 보도','2026-08-05 Lioneers 영입 보도; 이전 비갱신 소식보다 최신','https://sports.ltn.com.tw/news/breakingnews/5529044'),
10880:('구단 소속 확인','Orange Vikings 2026/27 구단 게시물','https://orangevikings.jp/news/event_202627_0825/'),
34:('공식 로스터 등재','Kings 2026/27 로스터 등재','https://www.newtaipeikings.com/roster'),
107:('재계약 보도','Dreamers 재계약 보도','https://www.asia-basket.com/Taiwan/news/1004341/Dreamers-keep-Holman-for-another-season'),
104:('공식 계약 발표','2026-09-08 Zastal 계약 발표','https://basketzg.sportigio.com/posts/beau-beech-zastalowcem/1180'),
12908:('영입 보도','2026-08-19 CTBC 영입 보도; 과거 FA 표기보다 최신','https://tw.sports.yahoo.com/news/tpbl-%E7%89%B9%E6%94%BB%E7%B0%BD%E4%B8%8B%E5%85%A8%E8%83%BD%E6%88%B0%E5%B0%87%E5%B8%83%E9%87%8C%E8%8C%B2%E5%85%8B-%E6%94%9C%E6%89%8B%E7%B8%BD%E6%95%99%E7%B7%B4%E8%B2%BB%E9%9B%AA%E8%A1%9D%E6%93%8A%E6%96%B0%E8%B3%BD%E5%AD%A3%E7%B8%BD%E5%86%A0%E8%BB%8D-041000203.html'),
13907:('영입 보도','2026-10-01 Illawarra 계약 보도, NBL 승인 조건','https://sportando.basketball/en/illawarra-hawks-sign-makur-maker-pending-nbl-approval/'),
16:('재계약 보도','2026-08-05 Leopards 재계약 보도','https://udn.com/news/story/7003/9672036'),
10867:('영입 보도','2026-08 Toyama 영입 보도','https://sportando.basketball/en/toyama-grouses-add-aamir-simms-and-darral-willis-jr/'),
10862:('영입 보도','2026-10-08 Hapoel Holon 계약 보도','https://www.asia-basket.com/Taiwan/news/1034864/TJ-Holyfield-ex-Lioneers-agreed-terms-with-HHolon'),
10888:('영입 보도','2026-08-26 터키 리그 복귀 보도','https://sportacentrs.com/basketbols/26082026-pasecniku_karjeras_cels_ved_atpakal_uz_tu'),
68:('공식 영입 발표','2026-08-11 Fubon 영입 발표','https://pleagueofficial.com/news-detail/888'),
10869:('영입 보도','2026-08 Dreamers 영입 보도; 3월 계약종료 소식보다 최신','https://udn.com/news/amp/story/7003/9698505'),
10875:('영입 보도','2026-07-16 Veltex Shizuoka 계약 보도','https://outnumber.online/tl/article/071625016/'),
4181:('영입 보도','2026-08-09 Calor Cancun 복귀 보도','https://www.poresto.com/deportes/2026/8/9/el-calor-de-cancun-suma-musculo-y-experiencia-con-el-regreso-de-edgaras-zelionis.html'),
14843:('미확인','에이전시의 시즌 available 문구만으로 무계약 상태를 확정할 수 없음','https://5ksports.com.br/'),
10894:('미확인','집계 사이트 FA 표기와 과거 해외 계약 이력이 있어 현시점 무계약 확인 불충분','https://www.365scores.com/fil-ph/basketball/player/cady-lalanne-111059'),
14038:('미확인','2026-01 Kings 계약 보도 이후 무계약 확인 자료 부족','https://www.asia-basket.com/Taiwan/news/975965/Femi-Olujobi-ex-Chiba-signs-at-Kings'),
10868:('미확인','FIBA 선수 소속 정보는 있으나 현시점 FA 확인 자료 부족','https://www.fiba.basketball/en/players/317932-jordy-tshimanga'),
13400:('미확인','해외 계약 이력이 있으며 NBA unsigned 표기만으로 FA 확정 불가','https://basketball.realgm.com/player/Diamond-Stone/summary/41493'),
10870:('미확인','해외 계약 이력이 있으며 NBA FA 표기만으로 FA 확정 불가','https://basketball.realgm.com/player/wd/Summary/57172'),
32:('은퇴 보도·FA 미확인','은퇴 보도 정보; 활동 상태 참고','https://en.wikipedia.org/wiki/Austin_Daye'),
13777:('은퇴 보도·FA 미확인','은퇴 보도 정보; 활동 상태 참고','https://en.wikipedia.org/wiki/Julian_Boyd'),
}

def main():
    rank=pd.read_csv(V/'scouting_ranking.csv')
    rows=[]
    for r in rank.itertuples():
        status,reason,url=evidence.get(r.player_id,('미확인','2026-10-10 현재 무계약 상태를 명시한 신뢰할 자료를 확보하지 못함',''))
        rows.append(dict(player_id=r.player_id,name=r.name,status=status,reason=reason,source_url=url,checked_date='2026-10-10',available_confirmed=False))
    review=pd.DataFrame(rows).sort_values('name');review.to_csv(V/'availability_review.csv',index=False,encoding='utf-8-sig')
    joined=rank.drop(columns=['availability','available_confirmed']).merge(review,on=['player_id','name'],validate='one_to_one')
    eligible=joined[joined.available_confirmed & joined.screen_pass].sort_values('scout_score',ascending=False).copy()
    eligible.insert(0,'recruit_rank',range(1,len(eligible)+1))
    eligible.to_csv(V/'confirmed_fa_ranking.csv',index=False,encoding='utf-8-sig')
    assert len(review)==35 and eligible.available_confirmed.all()
    metrics=pd.read_csv(V/'metrics.csv'); policy=json.loads((V/'scouting_policy.json').read_text(encoding='utf-8'))
    effects=pd.read_csv(V/'type_sensitivity.csv');pair=pd.read_csv(V/'paired_comparisons.csv')
    def save(fig,name):
        fig.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight');fig.savefig(F/(name+'.svg'),bbox_inches='tight');plt.close(fig)
    models=['GNN-v1','Graph-KRR','Graph-Ridge','Node-RBF','Ridge','Mean']
    fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    for ax,split,title in zip(axs,['group_nested','temporal_frozen'],['경기 단위 5-fold · 내부 튜닝','시간 순서 후반 8경기 · 재사용 평가']):
        d=metrics[metrics.split==split].set_index('model').loc[models]
        ax.barh(models,d.net_rmse,color=['#aeb8c5','#176a80','#aeb8c5','#aeb8c5','#aeb8c5','#aeb8c5']);ax.invert_yaxis();ax.set_xlim(0,110);ax.set_xlabel('팀 순득점/36분 예측 RMSE · 낮을수록 좋음');ax.set_title(title,pad=14)
        for i,val in enumerate(d.net_rmse):ax.text(val+1,i,f'{val:.2f}',va='center',fontsize=10)
    save(fig,'model_comparison')
    p=policy['mcc_percentiles'];labels=['득점 효율 (TS%)','패스/실책 (AST/TOV)','3점 생산량/36분','득점/36분','리바운드/36분'];keys=['TS','creation','three_made36','points','rebounds']
    fig,ax=plt.subplots(figsize=(9,4.8),layout='constrained');vals=[100*p[k] for k in keys]
    ax.barh(labels,vals,color=['#be6a37']*3+['#176a80']*2);ax.invert_yaxis();ax.axvline(50,color='#576473',ls='--');ax.set_xlim(0,105);ax.set_xlabel('보유 데이터 외국인 36명 내 백분위 · 200분 이상, 축소 추정치')
    ax.set_title('맥컬러: 리바운드보다 효율·볼 연결·외곽 보완에 우선순위',pad=15)
    for i,x in enumerate(vals):ax.text(x+1,i,f'{x:.1f}',va='center')
    save(fig,'mcc_profile')
    d=pair[(pair.split=='group_nested')&(pair.target=='net')].copy()
    # One shared scale hid every non-GNN interval. Use two explicitly labelled
    # linear ranges and an aligned numeric column; no broken or logarithmic axis.
    fig=plt.figure(figsize=(11,6.8),layout='constrained')
    grid=fig.add_gridspec(2,2,height_ratios=[1,2.8],width_ratios=[3.6,2.3])
    groups=[(d[d.versus=='GNN-v1'],(-4000,200),'① 기존 GNN과 비교 · 넓은 범위',[-4000,-3000,-2000,-1000,0]),
            (d[d.versus!='GNN-v1'],(-130,100),'② 다른 기준선과 비교 · 0 주변 확대',[-100,-50,0,50,100])]
    for row,(part,limits,title,ticks) in enumerate(groups):
        part=part.reset_index(drop=True);y=np.arange(len(part));ax=fig.add_subplot(grid[row,0]);numbers=fig.add_subplot(grid[row,1])
        ax.errorbar(part.mse_delta,y,xerr=[part.mse_delta-part.lo,part.hi-part.mse_delta],fmt='o',markersize=7,capsize=5,linewidth=1.8,color='#176a80')
        ax.axvline(0,color='#be6a37',ls='--',linewidth=1.4);ax.set_yticks(y,part.versus);ax.set_ylim(len(part)-.55,-.55);ax.set_xlim(*limits);ax.set_xticks(ticks);ax.grid(axis='x',color='#e1e7ec',linewidth=.7);ax.set_axisbelow(True);ax.set_title(title,loc='left',fontsize=12,pad=13)
        numbers.set_xlim(0,1);numbers.set_ylim(len(part)-.55,-.55);numbers.axis('off');numbers.set_title('MSE 차이 [95% 재표집 구간]',fontsize=11,loc='left',pad=13)
        for i,r in enumerate(part.itertuples()):numbers.text(0,i,f'{r.mse_delta:+,.1f}  [{r.lo:+,.1f}, {r.hi:+,.1f}]',va='center',fontsize=11,color='#142b40')
        if row==1:ax.set_xlabel('Graph-KRR MSE - 비교 모델 MSE\n음수: Graph-KRR 오차가 작음 · 양수: 비교 모델 오차가 작음',labelpad=10)
    fig.suptitle('GNN 대비 오차 감소 · 다른 기준선과의 차이는 불확실',fontsize=16)
    fig.supxlabel('두 패널의 x축 범위가 다릅니다. 점 = 오차 차이 추정값 · 가로선 = 95% 구간 · 단위 = (점/36분)²',fontsize=10)
    save(fig,'paired_uncertainty')
    e=effects[effects.feature.isin(['three_PA','AST','OREB','DREB','three_pct','TS'])].copy()
    if len(e)<4:e=effects.iloc[:8]
    fig,ax=plt.subplots(figsize=(9,4.8),layout='constrained');y=np.arange(len(e));ax.errorbar(e.net_delta,y,xerr=[e.net_delta-e.lo,e.hi-e.net_delta],fmt='o',capsize=4,color='#176a80');ax.axvline(0,color='#be6a37',ls='--');ax.set_yticks(y,e.feature);ax.invert_yaxis();ax.set_xlabel('특성 +0.5 학습 표준편차일 때 예측 순득점/36분 변화');ax.set_title('그래프 모형의 유형 효과: 선택한 특성 모두 95% 구간이 0 포함',pad=15)
    save(fig,'type_uncertainty')
    positive=int((review.status!='미확인').sum())
    fig,ax=plt.subplots(figsize=(9,3.8),layout='constrained');ax.barh(['분석 가능한 외국인','체격·출전량 가정 통과','확인된 FA이며 가정 통과'],[35,23,len(eligible)],color=['#aeb8c5','#aeb8c5','#176a80']);ax.invert_yaxis();ax.set_xlim(0,40);ax.set_xlabel('선수 수');ax.set_title('공개 자료로 확인된 자유계약 선수만 영입 명단에 포함',pad=15)
    for i,x in enumerate([35,23,len(eligible)]):ax.text(x+.5,i,str(x),va='center')
    save(fig,'fa_gate')
    def image(name,alt):return f'<figure><div class="chart-scroll" tabindex="0" aria-label="그래프: 작은 화면에서 좌우 스크롤"><img src="v2/figures/{name}.svg" alt="{alt}" loading="lazy"></div><figcaption>{alt} · <a href="v2/figures/{name}.png">PNG</a> / <a href="v2/figures/{name}.svg">SVG</a> · 작은 화면에서는 그래프를 좌우로 스크롤하세요</figcaption></figure>'
    def esc(s):return html.escape(str(s))
    evidence_rows=''.join(f'<tr><td>{esc(r.name)}</td><td>{esc(r.status)}</td><td>{esc(r.reason)}</td><td>'+ (f'<a href="{esc(r.source_url)}" target="_blank" rel="noopener">근거</a>' if r.source_url else '확인 자료 없음')+'</td></tr>' for r in review.itertuples())
    table=metrics[['split','model','net_rmse','mcc_rmse']].rename(columns={'split':'평가','model':'모델','net_rmse':'팀 RMSE','mcc_rmse':'맥컬러 RMSE'}).to_html(index=False,float_format=lambda x:f'{x:.3f}',border=0)
    content=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>McCullough · 그래프 커널 검증과 FA 스카우팅</title><style>
    :root{{--ink:#142b40;--muted:#516274;--blue:#176a80;--line:#d9e1e8;--paper:#f4f7f9}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.75 'Malgun Gothic',sans-serif}}main{{max-width:1120px;margin:auto;padding:40px 24px 80px}}header{{border-top:6px solid var(--blue);padding-top:24px}}h1{{font-size:clamp(28px,4vw,44px);line-height:1.3;letter-spacing:-1px}}h2{{font-size:25px;line-height:1.4;margin:0 0 18px}}h3{{font-size:19px}}.eyebrow{{font-size:13px;letter-spacing:2px;color:var(--blue);font-weight:bold}}.lead{{font-size:20px;max-width:900px}}.muted,figcaption{{color:var(--muted);font-size:14px}}section{{background:white;border:1px solid var(--line);border-radius:14px;padding:30px;margin-top:24px;scroll-margin-top:15px}}a{{color:#086581;overflow-wrap:anywhere}}nav{{display:flex;flex-wrap:wrap;gap:16px;margin:24px 0}}.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:24px 0}}.card{{background:#e9f1f5;padding:20px;border-radius:10px}}.big{{font-size:32px;font-weight:bold;display:block}}.note{{border-left:4px solid #bd6d36;background:#fff5eb;padding:16px 20px;margin:18px 0}}figure{{margin:24px 0}}img{{display:block;width:100%;height:auto}}.chart-scroll{{overflow-x:auto}}.chart-scroll img{{min-width:640px}}figcaption{{margin-top:8px}}.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:14px;text-align:left}}td,th{{padding:12px;border-bottom:1px solid var(--line);vertical-align:top}}th{{background:#eef3f6;white-space:nowrap}}summary{{cursor:pointer;font-weight:bold;padding:12px 0}}input{{padding:12px;border:1px solid #798e9b;border-radius:6px;width:min(100%,420px);font:inherit}}.pipeline{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.step{{border:1px solid var(--line);padding:16px;border-radius:8px}}code{{font-size:14px;overflow-wrap:anywhere}}@media(max-width:650px){{main{{padding:24px 14px 50px}}section{{padding:20px 16px}}.cards,.pipeline{{grid-template-columns:1fr}}.lead{{font-size:18px}}td,th{{padding:9px}}}}@media print{{body{{background:white}}main{{max-width:none;padding:0}}section{{break-inside:avoid}}nav,input{{display:none}}details{{display:block}}}}
    </style></head><body><main><header><div class="eyebrow">SAMSUNG THUNDERS · GRAPH LEARNING · V2</div><h1>맥컬러를 보완하는 선수 유형과<br>확인된 FA 영입 후보 검증</h1><p class="lead">그래프 커널 회귀는 기존 GNN보다 안정적이었습니다. 그러나 단순 평균·회귀보다 우수한 궁합 예측은 확인되지 않았습니다. 선수 유형은 관측 통계에 근거한 스카우팅 가설로 제시합니다.</p><p class="muted">분석·계약 확인 기준일 2026-10-10 · TPBL 2025–26 자료 · 서울 삼성 썬더스</p></header>
    <nav aria-label="보고서 목차"><a href="#results">모델 검증</a><a href="#type">선수 유형</a><a href="#fa">FA 후보</a><a href="#methods">방법과 한계</a><a href="#files">재현 파일</a></nav>
    <div class="cards"><div class="card"><span class="big">24경기</span>정제한 385구간 · 595.2분</div><div class="card"><span class="big">19.6% ↓</span>기존 GNN 대비 교차검증 팀 RMSE</div><div class="card"><span class="big">0명</span>보유 데이터에서 확인된 FA 후보</div></div>
    <section id="results"><h2>01 · GNN 대안: 속성 그래프 커널 회귀</h2><p><b>Graph-KRR</b>은 선수 노드의 경기 전 특성과 아군·상대 관계를 고정 길이 그래프 표현으로 바꾼 뒤, 그래프 간 유사도를 이용해 순득점과 맥컬러 득점을 예측합니다. 중심성·커뮤니티 탐지·클러스터링은 사용하지 않았습니다.</p>
    {image('model_comparison','동일 정제 데이터·경기 단위 분할에서 비교. 단위는 점/36분이며 RMSE가 작을수록 좋습니다.')}
    <p>팀 순득점 RMSE는 교차검증에서 <b>86.78 → 69.81</b>, 시간 순서 평가에서 <b>93.49 → 64.43</b>으로 개선됐습니다. 다만 교차검증 평균 기준선은 69.69, Ridge는 69.66으로 Graph-KRR보다 소폭 좋았습니다. 기존 GNN은 기존 하이퍼파라미터를 유지한 3개 시드 평균이며, 새 커널 모형처럼 재튜닝하지 않았습니다. 개선율은 이 기존 구현과의 비교이며 모든 GNN보다 우수하다는 뜻은 아닙니다.</p>
    {image('paired_uncertainty','넓은 범위의 GNN 비교와 0 주변의 기준선 비교를 분리했습니다. 경기 단위 2,000회 짝지은 부트스트랩의 95% 구간이며, 아래 패널의 모든 구간은 0을 포함합니다. 고정된 외부 예측의 오차 차이로 재학습 불확실성 전체는 포함하지 않습니다.')}
    <div class="note"><b>발표에서 사용할 결론:</b> “소표본에서 기존 GNN의 불안정성을 줄였지만, 그래프 관계 정보를 추가한 예측 이득은 입증하지 못했다.” 시간 순서 후반 8경기는 이전 분석에서도 사용한 구간으로, 새 시즌의 독립 검증 결과가 아닙니다.</div><details><summary>모든 모델의 결과 보기</summary><div class="scroll">{table}</div><p class="muted">group_nested = 경기 단위 외부 5-fold / 내부 3-fold 튜닝. temporal_frozen = 앞 16경기 학습, 뒤 8경기 평가; 평가 특성은 첫 평가일 이전으로 동결. 보조 목표인 맥컬러 득점의 하이퍼파라미터는 팀 순득점 기준으로 선택했습니다.</p></details></section>
    <section id="type"><h2>02 · 우선 검토할 유형: 효율과 볼 연결을 갖춘 슈팅 빅맨</h2><p>맥컬러는 보유 외국인 표본에서 리바운드 백분위가 <b>88.9</b>로 높습니다. 보완 우선순위는 <b>득점 효율 → 패스/실책 관리 → 외곽 생산</b>입니다. 리바운드를 약점으로 간주해 리바운더만 더하는 해석은 자료와 맞지 않습니다.</p>
    {image('mcc_profile','외국인 36명(맥컬러 포함)의 축소 추정 통계로 계산한 상대적 위치. 낮은 백분위는 해당 비교집단 내 낮은 수치를 뜻합니다.')}
    <p>전술 가설은 <b>리바운드 기본 기여를 유지하면서, 외곽에서 공간을 만들고 패스로 공격을 연결하는 4–5번</b>입니다. 3점 성공률만 보지 않고 시도량과 생산량을 함께 확인해야 합니다. 이 유형은 2·3쿼터 동시 출전에서 공간·패스 선택지를 늘리고, 1·4쿼터 교대에서도 공격 기여를 유지한다는 전술 가설입니다. 두 역할의 효과를 개별적으로 검증한 결과는 아닙니다.</p><p>내부 선별 가정은 시즌 400분 이상, 신장 198cm 이상, 축소 추정 리바운드/36분 8개 이상입니다. 이는 분석자가 정한 조건이며 KBL 자격 규정이 아닙니다. 수비 매치업·스크린·롤/팝 효율은 자료가 없어 확인하지 못했습니다.</p>
    {image('type_uncertainty','같은 상대·상황 프로필에서 한 특성을 바꾼 모형 민감도. 100회 경기 재표집·계수 재추정 구간이며 고정 튜닝값을 사용합니다. 인과효과가 아닙니다.')}
    <p><b>GNN이 최적 유형을 학습했다고 주장할 수는 없습니다.</b> 그래프 민감도는 거의 0이고 불확실성 구간도 0을 포함합니다. 따라서 위 유형은 통계적 보완 가설이며, 실제 궁합은 추가 경기 영상과 KBL 로테이션 데이터로 검증해야 합니다.</p></section>
    <section id="fa"><h2>03 · 확인된 자유계약 선수만: 현재 추천 순위 없음</h2><div class="note"><b id="faCount">검증된 후보 0명.</b> 보유 TPBL 데이터의 35명을 확인했으나, 기준일 현재 자유계약 상태와 분석 가능 기록을 모두 충족한다고 확인한 선수가 없습니다. 이는 전 세계 FA가 0명이라는 뜻이 아닙니다. 계약 상태가 불분명한 선수를 FA로 간주한 순위는 발행하지 않았습니다.</div>
    {image('fa_gate','데이터 범위 35명 → 분석자 선별 가정 통과 23명 → FA 확인까지 통과 0명. 미확인은 영입 가능으로 처리하지 않습니다.')}
    <p>공식 발표·로스터와 최신 이적 보도를 검토했습니다. 예를 들어 <a href="https://pleagueofficial.com/news-detail/895">Marko Todorovic의 Fubon 영입</a>, <a href="https://twardepierniki.pl/posts/viktor-gaddefors-wraca-do-torunia/413">Viktor Gaddefors의 Torun 계약</a>, <a href="https://www.newtaipeikings.com/roster">Jason Washburn의 Kings 2026/27 로스터 등재</a>가 확인됩니다. 과거 방출 기사, NBA 한정 FA 표기, 에이전시의 일반적인 available 문구는 현시점 무계약 증거로 인정하지 않았습니다.</p>
    <p><a href="v2/confirmed_fa_ranking.csv">확인된 FA 순위 CSV (현재 헤더만 있음)</a> · <a href="v2/availability_review.csv">35명 계약 확인표 CSV</a></p>
    <p>삼성은 맥컬러 영입 당시 케렘 칸터와의 계약도 발표된 상태입니다(<a href="https://v.daum.net/v/20260824163351533">2026-08-24 보도</a>). 따라서 이 프로젝트의 영입은 향후 교체 시나리오입니다. 칸터 비교 데이터가 없어 현 선수 교체의 타당성은 평가하지 않았습니다.</p>
    <details><summary>후보 제외·미확인 근거 35명 보기 — 이름순, 추천 순위 아님</summary><label for="search">선수 이름 검색</label><br><input id="search" type="search" placeholder="예: Marin Maric"><p id="count" aria-live="polite"></p><div class="scroll"><table><thead><tr><th>선수</th><th>확인 내용</th><th>사유 · 2026-10-10 확인</th><th>출처</th></tr></thead><tbody id="reviewRows">{evidence_rows}</tbody></table></div></details>
    <details><summary>FA가 확인되면 적용할 점수와 불확실성</summary><p>내부 정책 점수 = 60% 기본 기여 + 40% 맥컬러 대비 보완. 기본 기여는 TS 35%, 득점 20%, 리바운드 25%, AST/TOV 20%입니다. 보완 점수는 맥컬러의 중위값 미달 정도에 따라 효율 40.0%, 볼 연결 37.1%, 외곽 생산 22.9%를 사용합니다. 모두 보유 표본 내 백분위 기반의 분석자 정책이며 학습된 승리 확률이 아닙니다.</p><p>정책 가중치 40/60/80% 비교와 리그 경기 500회 재표집을 수행했습니다. 신뢰구간은 고정한 선별집단에서 통계 변동을 나타내며, 계약·가격·부상·KBL 적응 불확실성은 포함하지 않습니다. 기술 파일의 conditional_rank는 전체 데이터 역할 비교용이며 FA 추천 순위가 아닙니다.</p></details></section>
    <section id="methods"><h2>04 · 재현 가능한 검증 설계와 적용 한계</h2><div class="pipeline"><div class="step"><b>1. 정제</b><br>30초 이상·비가비지 정규시즌<br>코트 밖 선수 이벤트가 있는 16구간 제외</div><div class="step"><b>2. 경기 전 정보</b><br>같은 날·이후 기록 제외<br>노드 스케일은 학습 구간으로 추정</div><div class="step"><b>3. 그래프 표현</b><br>10명 노드 × 19특성<br>아군/상대 쌍 관계를 197차원으로 집계</div><div class="step"><b>4. 커널 회귀</b><br>RBF 유사도 + 가중 ridge<br>경기 단위 분리와 내부 튜닝</div></div>
    <p>기본 61차원은 역할별 특성 평균 57개와 상황 특성 4개입니다. 맥컬러–동료 상호작용 64개, 동료 간 상호작용 64개, 아군–상대 차이 8개를 더해 197차원 표현을 만듭니다. 관계 종류가 고정된 완전 그래프이므로 변화하는 정보는 주로 선수 속성입니다. 노드만 사용하는 Node-RBF와 비교해 관계 표현의 추가 이득을 검증했습니다.</p>
    <p>커널은 k(G,H)=exp(−‖φ(G)−φ(H)‖²/(2σ²d)) 형태입니다. 실제 구현의 거리 정규화와 가중 중심화는 <a href="strengthen.py">strengthen.py</a>가 기준입니다. λ와 커널 폭은 내부 경기 교차검증으로 선택합니다. 특정 논문의 구현을 그대로 복제한 것이 아닌, 속성 그래프 표현과 표준 커널 회귀를 결합한 맞춤 모형입니다. 관련 원리는 <a href="https://papers.nips.cc/paper_files/paper/2013/hash/a2557a7b2e94197ff767970b67041697-Abstract.html">연속 속성 그래프 커널 연구</a>를 참고할 수 있습니다.</p>
    <p><b>리그 전이의 핵심 제약:</b> 2026–27 KBL은 외국인 2명 보유, 2·3쿼터 최대 2명 동시 출전, 1·4쿼터 1명 출전으로 변경됐습니다(<a href="https://v.daum.net/v/20260115151652686?f=p">KBL 이사회 결정 보도</a>, <a href="https://www.yna.co.kr/view/AKR20260928079300007">시즌 개막 시점 재확인</a>). 동시 출전 궁합이 이번 시즌에는 실제 전술 질문입니다. 다만 리그·국내 동료·쿼터·경기 속도가 달라 TPBL 성과를 삼성 성과로 그대로 옮길 수 없습니다. 보유 팀의 정제된 정규시즌 자료 중 외국인 1명 구간은 3개·4.75분에 불과합니다. 따라서 두 외국인 동시 출전 맥락의 학습에 비해, 1·4쿼터에 필요한 외국인 1명 운용 성능을 직접 학습할 근거는 특히 부족합니다.</p>
    <p>후보 교체 실험은 384개의 공통 상황에서 동일한 상대 속성 프로필을 사용합니다. 상대 프로필은 익명화된 비교 맥락이며 후보와 실제 맞대결한 기록을 뜻하지 않습니다. 전체 시즌 통계로 만든 사후 실험으로, 신규 선수의 미래 성적 검증이 아닙니다. 커널의 강한 정규화로 차이가 거의 사라진 결과를 유의미한 궁합 순위로 해석하지 않았습니다.</p>
    <details><summary>데이터·불확실성 및 검증 체크</summary><ul><li>선수별 분당 기록은 200분, 3점 성공률은 50시도, TS는 분모 100의 리그 사전값으로 축소합니다.</li><li>경기 단위 분할로 같은 경기 구간이 학습·평가에 섞이지 않도록 했습니다. 교차검증은 사후 평가입니다. 무작위 경기 fold에서는 평가 경기의 박스스코어가 그 이후 학습 경기의 사전 누적 통계에 반영될 수 있으므로 완전히 독립된 미래 예측 검증으로 해석하지 않습니다. 시간 순서 분할에서는 학습일이 모두 평가일보다 앞서고 평가 특성을 동결하여 이 경로를 막았습니다. 실전 예측 해석은 시간 평가를 우선합니다.</li><li>미래 기록을 100배 바꾸어도 해당 경기 전 특성 변화는 0. 노드 순서 변경 시 표현 차이는 1.8e−15. 검사한 커널 행렬의 최소 고윳값은 양수입니다.</li><li>동일 날짜 통계 제외·학습 노드 스케일링으로 기존 정보 누출 위험을 줄였습니다. 정제 CSV에서 재구성했으며 원시 API 응답까지의 감사를 완료한 것은 아닙니다.</li><li>24경기에서 나온 385구간은 독립 표본 385개가 아닙니다. 짧은 구간의 36분 환산 목표가 매우 변동적입니다. 인과적 선수 효과·삼성 승률·계약 가능 확률은 추정하지 않습니다.</li><li>조건부 스카우팅 풀은 보유 TPBL 선수에 한정됩니다. 전 세계 FA 탐색·다른 리그 성적 수집·연봉 협상·메디컬·등록 적격성 확인은 이번 데이터로 완료되지 않았습니다.</li></ul></details></section>
    <section id="files"><h2>05 · 발표·재현 파일</h2><p><a href="v2/metrics.csv">모델 성능</a> · <a href="v2/paired_comparisons.csv">오차 차이 구간</a> · <a href="v2/splits.csv">분할 명세</a> · <a href="v2/hyperparameters.csv">튜닝 결과</a> · <a href="v2/run_summary.json">실행·검증·입력 해시</a> · <a href="v2/excluded_stints.csv">제외 구간</a> · <a href="strengthen.py">분석 코드</a> · <a href="build_report_v2.py">보고서·FA 필터 코드</a></p><p>실행 순서: <code>python strengthen.py</code> → <code>python build_report.py</code>. 이전 보고서는 <a href="mcc_gnn_report_v1.html">v1 보관본</a>으로 유지했습니다. v1의 네트워크 전이 점수·후보 순위는 이번 결론에 사용하지 않습니다.</p><p class="muted">가장 중요한 후속 자료: 현재 FA임을 명시한 구단/선수/에이전트의 최신 확인, 해당 선수의 경기 기록, KBL 외국인 1명 및 2명 운용을 구분한 라인업·포제션·영상 데이터. 이 자료가 있어야 실제 영입 순위를 검증 가능한 형태로 확장할 수 있습니다.</p></section>
    </main><script>const box=document.querySelector('#search'), rows=[...document.querySelectorAll('#reviewRows tr')];function filter(){{let q=box.value.toLowerCase();let n=0;rows.forEach(r=>{{r.hidden=!r.cells[0].textContent.toLowerCase().includes(q);if(!r.hidden)n++}});document.querySelector('#count').textContent=n+'명 표시 · 추천 명단이 아닌 계약 확인표';const u=new URL(location);q?u.searchParams.set('q',box.value):u.searchParams.delete('q');history.replaceState(null,'',u)}}box.value=new URL(location).searchParams.get('q')||'';box.addEventListener('input',filter);filter();</script></body></html>'''
    dest=P/'mcc_gnn_report.html'
    if not (P/'mcc_gnn_report_v1.html').exists():shutil.copy2(dest,P/'mcc_gnn_report_v1.html')
    dest.write_text(content,encoding='utf-8')
    (V/'report_checks.json').write_text(json.dumps({'eligible_fa_count':len(eligible),'reviewed_players':len(review),'no_unknown_in_eligible':True,'figures':5},indent=2),encoding='utf-8')
    print('Report updated; confirmed free agents:',len(eligible))
if __name__=='__main__':main()
