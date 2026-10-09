"""Detailed HTML report with contract-independent candidate comparisons."""
from pathlib import Path
import json, html, re, shutil
import build_report_v2 as base
pd=base.pd;np=base.np;plt=base.plt
P=base.P;V=base.V;F=base.F

NOTES={
10887:('효율·외곽·볼 연결을 함께 갖춘 4–5번','TS 64.2%, 3점 63/195, AST 2.99/36분으로 여러 보완 항목을 함께 충족합니다. 출전량도 1,203.9분으로 후보 중 충분한 편입니다.','3점 성공률은 32.3%입니다. 엘리트 슈터로 단정하기보다 시도량과 효율의 결합을 평가해야 합니다. 실제 스크린·수비 적응은 별도 확인이 필요합니다.'),
13029:('볼 창출·외곽 보완형 가드','27.28득점·5.19어시스트/36분, 3점 42/115로 공격 보완 점수가 높습니다. 포지션 제한을 풀면 전체 2위입니다.','193cm 가드이며 리바운드는 6.16/36분입니다. 삼성의 두 번째 외국인에게 빅맨 수비를 요구한다면 역할상 맞지 않을 수 있습니다.'),
10890:('외곽과 패스를 결합한 파워포워드','3점 45/125(36.0%), TS 60.0%, AST 3.39/36분으로 공간과 공격 연결을 함께 제공하는 유형입니다.','리바운드·수비·운동 능력은 별도 영상 검증이 필요합니다. 과거 TPBL 효율만으로 KBL 득점 효율을 보장할 수 없습니다.'),
8889:('득점·리바운드 기반의 공격형 센터','23.04득점·13.73리바운드/36분, TS 60.9%, 3점 36/104로 기본 기여와 외곽 선택지를 함께 갖춥니다.','AST 2.79 대 TOV 2.91/36분으로 실측 AST/TOV는 1 미만입니다. 패스 보완이 가장 뛰어난 후보라는 해석은 피해야 합니다.'),
10881:('효율·볼 연결 중심 포워드','TS 60.8%, AST 3.53 대 TOV 2.29/36분으로 공격 연결이 강점입니다.','3점은 2/30(6.7%)입니다. 종합 상위권이어도 슈팅 빅맨이라는 최우선 가설을 직접 충족하지는 않습니다.'),
10861:('효율·리바운드 중심 인사이드','TS 63.3%, 24.47득점·14.97리바운드/36분으로 기본 기여가 높습니다.','3점 0/1이며 AST/TOV도 낮습니다. 맥컬러와 역할이 중복될 수 있어 슈팅·패스 보완보다 인사이드 운용 시나리오에 적합합니다.'),
107:('외곽 생산과 리바운드를 갖춘 4번','3점 55/163(33.7%), 리바운드 13.12/36분으로 외곽 시도량과 리바운드 기여가 함께 있습니다.','TS는 56.8%이고 TOV 3.70/36분입니다. 효율과 실책 관리에서 최상위 후보보다 약한 부분이 있습니다.'),
12908:('패스 중심의 윙·포워드','AST 6.02 대 TOV 2.29/36분, 3점 18/47(38.3%)로 볼 연결을 보완합니다.','198cm이며 표본은 424.3분·3점 47시도입니다. 빅맨 매치업과 외곽 성공률의 지속성은 검증이 필요합니다.'),
104:('외곽 생산을 우선한 스트레치 포워드','3점 49/127(38.6%)이며 표본 내 축소 외곽 생산 백분위가 가장 높습니다. 슈팅 보완을 우선할 때 검토 가치가 있습니다.','전체 기본 기여 점수는 50.7입니다. 출전량 466.4분이며 인사이드 수비·리바운드 역할은 추가 확인이 필요합니다.'),
10880:('득점과 외곽을 겸하는 포워드','22.79득점·10.86리바운드/36분에 3점 37/116으로 득점 선택지가 있습니다.','3점 성공률 31.9%, AST 1.97/36분입니다. 최상위의 패스 보완 후보로 보기는 어렵습니다.'),
34:('효율 중심의 센터','TS 62.0%, 11.49리바운드/36분으로 인사이드 기본 기여가 있습니다.','3점 2/19입니다. 점수가 높아도 외곽 공간을 만드는 유형으로 해석하면 안 됩니다.'),
}

def esc(v):return html.escape(str(v))
def num(v,n=1):return '—' if pd.isna(v) else f'{v:.{n}f}'
def fig(name,caption):return f'<figure><div class="chart-scroll" tabindex="0" aria-label="그래프를 좌우로 스크롤할 수 있습니다"><img src="v2/figures/{name}.svg" alt="{esc(caption)}" loading="lazy"></div><figcaption>{caption} · <a href="v2/figures/{name}.png">PNG</a> / <a href="v2/figures/{name}.svg">SVG</a></figcaption></figure>'
def save(f,name):
    f.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight');f.savefig(F/(name+'.svg'),bbox_inches='tight');plt.close(f)

def main():
    # Rebuild current model charts and methods from the established source.
    base.main()
    from expand_scouting import main as expand
    expand()
    d=pd.read_csv(V/'expanded_scouting_ranking.csv');pc=pd.read_csv(V/'role_percentiles.csv').set_index('player_id')
    sensitivity=pd.read_csv(V/'expanded_weight_sensitivity.csv');bench=pd.read_csv(V/'benchmark_only.csv')
    meta=json.loads((V/'expanded_summary.json').read_text(encoding='utf-8'))
    top=d.head(15).iloc[::-1]
    f,ax=plt.subplots(figsize=(11,7.2),layout='constrained');y=np.arange(len(top))
    ax.barh(y,.6*top.quality_score,label='기본 기여 60%',color='#176a80');ax.barh(y,.4*top.complement_score,left=.6*top.quality_score,label='맥컬러 보완 40%',color='#d79152')
    ax.set_yticks(y,top.name);ax.set_xlim(0,100);ax.set_xlabel('기준 적합도 점수 · 100점 척도 · 전체 35명 중 상위 15명');ax.set_title('Drew Pember가 1위 · 가드까지 넓히면 Jalen Harris가 2위',pad=18);ax.legend(loc='lower right')
    for i,r in enumerate(top.itertuples()):ax.text(r.scout_score+.8,i,f'{r.scout_score:.1f}',va='center')
    save(f,'expanded_ranking')
    f,ax=plt.subplots(figsize=(11,7.2),layout='constrained');ax.errorbar(top.scout_score,y,xerr=[top.scout_score-top.score_lo,top.score_hi-top.scout_score],fmt='o',capsize=3,color='#176a80');ax.set_yticks(y,top.name);ax.set_xlim(0,100);ax.set_xlabel('기준 점수와 경기 500회 재표집 2.5–97.5% 범위');ax.set_title('점수 구간의 중첩이 큼 · 작은 순위 차이는 신중하게 해석',pad=18);save(f,'expanded_uncertainty')
    keys=['TS','creation','three_made36','points','rebounds'];labs=['효율','패스/실책','외곽 생산','득점','리바운드'];pool=d.head(10)
    a=pc.loc[[10860]+pool.player_id.tolist(),keys]*100
    f,ax=plt.subplots(figsize=(10,7),layout='constrained');im=ax.imshow(a,cmap='Blues',vmin=0,vmax=100,aspect='auto');ax.set_xticks(range(5),labs);ax.set_yticks(range(len(a)),['Chris McCullough']+pool.name.tolist());ax.set_title('상위 10명의 보완 항목 비교 · 같은 점수에도 역할은 다름',pad=18)
    for i in range(len(a)):
        for j in range(5):ax.text(j,i,f'{a.iloc[i,j]:.0f}',ha='center',va='center',color='white' if a.iloc[i,j]>=65 else '#142b40')
    f.colorbar(im,ax=ax,label='외국인 36명 내 축소 통계 백분위');save(f,'candidate_profiles')
    chosen=d.head(8)
    f,ax=plt.subplots(figsize=(10,5.3),layout='constrained')
    colors=plt.get_cmap('tab10').colors
    for i,r in enumerate(chosen.itertuples()):
        z=sensitivity[sensitivity.player_id==r.player_id].sort_values('quality_weight');ax.plot(z.quality_weight*100,z['rank'],marker='o',label=r.name,color=colors[i])
    ax.invert_yaxis();ax.set_xticks([40,60,80]);ax.set_ylabel('전체 35명 내 순위 · 작을수록 상위');ax.set_xlabel('기본 기여 비중 (%) · 나머지는 맥컬러 보완');ax.set_title('가중치에 따른 순위 변화 · 상위 8명',pad=16);ax.legend(bbox_to_anchor=(1.02,1),loc='upper left',fontsize=9);save(f,'expanded_weights')
    cards=[]
    for pid in [10887,13029,10890,8889,10881,10861,107,12908,104]:
        r=d[d.player_id==pid].iloc[0];title,strong,risk=NOTES[pid]
        source=f'<a href="{esc(r.source_url)}" target="_blank" rel="noopener">계약 확인 출처</a>' if pd.notna(r.source_url) else '추가 계약 확인 필요'
        role='체격·리바운드 조건 통과' if r.screen_pass else '빅맨 역할 조건 미충족'
        cards.append(f'<article class="player-card"><div class="eyebrow">전체 {int(r.candidate_rank)}위 · {num(r.scout_score)}점</div><h3>{esc(r["name"])}</h3><p><b>{title}</b></p><p>{strong}</p><p class="muted"><b>검토할 점:</b> {risk}</p><p class="small">{role} · 점수 재표집 {num(r.score_lo)}–{num(r.score_hi)} · 순위 재표집 {num(r.rank_lo)}–{num(r.rank_hi)}</p><p class="small">계약: {esc(r.status)} · {source}</p></article>')
    scope=f'''<section id="ranking"><h2>03 · 계약 상태를 제한하지 않은 외국인 스카우팅 순위</h2><p>보유 데이터에서 맥컬러를 제외한 외국인 중 200분 이상 출전한 <b>35명</b>을 비교했습니다. 계약 선수와 계약 미확인 선수도 포함합니다. 은퇴 보도 선수 2명도 동일 기준으로 포함하여 <b>전체 35명에게 영입 검토 순위</b>를 부여했습니다. 활동 상태는 참고 정보로 표시하며 순위에서 제외하거나 감점하지 않습니다. 이 중 기존 체격·출전량·리바운드 조건을 만족하는 선수는 <b>23명</b>입니다.</p><div class="note">순위는 <b>기술·역할 적합도에 따른 스카우팅 우선순위</b>입니다. 계약·이적료·연봉·부상 정보는 점수에 반영하지 않았습니다. 따라서 상위 선수도 즉시 영입 가능한 선수라는 의미는 아닙니다. 기존 계약 확인 결과는 기준일과 출처를 함께 표시합니다.</div>
    {fig('expanded_ranking','점수는 기본 기여와 맥컬러 대비 보완을 합친 분석자 정책입니다. GNN이나 그래프 커널이 학습한 선수 궁합 점수가 아닙니다.')}
    <h3>전체 35명 비교표</h3><p>기본 순위는 모든 포지션을 포함합니다. 빅맨 역할 조건을 켜면 23명으로 좁혀집니다. 점수 비중을 바꾸면 전체 후보의 순위를 다시 계산합니다. 검색·필터를 적용해도 순위는 해당 비중에서의 전체 35명 기준입니다.</p>
    <div class="controls"><label>선수·과거 소속 검색<input id="candidateSearch" type="search" placeholder="예: Pember, Harris, Dreamers"></label><label>비교 범위<select id="roleFilter"><option value="all">전체 35명</option><option value="role">빅맨 역할 조건 통과 23명</option><option value="other">역할 조건 미충족 12명</option></select></label><label>점수 비중<select id="mix"><option value="60">기본 기여 60% + 보완 40%</option><option value="40">보완 중시: 기본 40% + 보완 60%</option><option value="80">기본 중시: 기본 80% + 보완 20%</option></select></label></div>
    <p id="candidateCount" aria-live="polite"></p><div class="scroll" tabindex="0" aria-label="후보 비교표: 좌우 스크롤"><table class="rank-table"><thead><tr><th>전체 순위</th><th>선수 · 데이터 당시 소속</th><th>적합도</th><th>기본 / 보완</th><th>역할 조건</th><th>출전분</th><th>PTS / REB / AST<br>36분당</th><th>TS%</th><th>3점 성공/시도</th><th>기준 점수<br>95% 재표집 범위</th><th>계약 확인</th></tr></thead><tbody id="candidateRows"></tbody></table></div><noscript><p>전체 순위는 <a href="v2/expanded_scouting_ranking.csv">CSV 다운로드</a>로 확인할 수 있습니다.</p></noscript>
    <p class="muted">표의 PTS/REB/AST·TS·3점은 시즌 실측 통계입니다. 적합도는 출전량을 고려해 축소한 통계의 백분위를 사용하므로, 표의 실측 값만으로 계산한 순서와 다를 수 있습니다. 재표집 범위는 기본 60/40 정책 기준이며 비중을 변경해도 그 기준 범위를 표시합니다. 데이터 당시 소속과 현재 계약 소속은 구분해야 합니다.</p>
    <p><a href="v2/expanded_scouting_ranking.csv">35명 순위·통계·계약 확인 CSV</a> · <a href="v2/expanded_weight_sensitivity.csv">가중치별 전체 순위 CSV</a> · <a href="v2/availability_review.csv">35명 계약 근거 CSV</a></p>
    <h3>포지션에 따라 달라지는 해석</h3><p>전체 점수에서는 <b>Drew Pember → Jalen Harris → Trey Thompkins III → Marko Todorovic → Viktor Gaddefors</b> 순입니다. 빅맨 역할 조건을 적용하면 <b>Pember → Thompkins → Todorovic → Gaddefors → Cheick Diallo</b>가 상위 5명입니다. Harris는 공격 보완형 가드이고, Gaddefors·Diallo는 종합 점수가 높아도 외곽 보완 유형과는 다릅니다. 삼성의 역할 요구를 먼저 정한 뒤 순위를 읽어야 합니다.</p>
    {fig('candidate_profiles','맥컬러와 상위 10명 동일 참조집단의 백분위 비교. 모든 지표는 높을수록 해당 통계가 높은 것이며 수비 성능을 뜻하지 않습니다.')}
    <h3>상위 선수별 검토 근거</h3><div class="player-grid">{''.join(cards)}</div>
    <h3>점수 차이의 불확실성</h3>{fig('expanded_uncertainty','리그 경기 126개를 경기 단위로 500회 재표집하고, 모든 후보의 점수·순위를 다시 계산했습니다. 후보 35명과 원래 백분위 참조집단 36명을 고정했습니다.')}
    <p>1위 Pember도 재표집에서는 순위가 변합니다. 높은 점수는 유망한 검토 대상을 뜻하지만, 작은 점수 차이로 선수 간 우열을 확정할 수는 없습니다. 상위 5위 비율은 재표집의 안정성 지표이며 실제 성공 확률이 아닙니다.</p>
    {fig('expanded_weights','기본 기여 비중 40/60/80%에서의 전체 35명 순위. 위 그래프는 통계 재표집 구간과 다른, 분석자 가중치 선택에 대한 민감도입니다.')}
    <p>삼성은 맥컬러 영입 당시 케렘 칸터 계약도 보도됐습니다(<a href="https://v.daum.net/v/20260824163351533">2026-08-24 보도</a>). 따라서 실제 영입은 교체 또는 향후 시즌 구상과 연결됩니다. 칸터의 동일 기준 자료가 없어 현 선수보다 낫다는 교체 결론은 내리지 않았습니다.</p></section>'''
    detail='''<section id="scoring"><h2>04 · 적합도 점수는 어떻게 계산했는가</h2><p>그래프 모형에서 후보 교체 효과가 거의 0으로 수렴했으므로, 그 미세한 예측 차이를 정밀한 순위로 확대하지 않았습니다. 선수 추천에는 맥컬러의 관측 프로필을 보완하는 투명한 정책을 적용했습니다. <b>모델 성능 검증</b>과 <b>실제 스카우팅 점수</b>는 서로 다른 결과입니다.</p>
    <div class="formula"><b>적합도 S = 0.60 × 기본 기여 Q + 0.40 × 보완 C</b><br>Q = 0.35 × 효율 + 0.20 × 득점 + 0.25 × 리바운드 + 0.20 × 패스/실책<br>각 항목은 동일 참조집단 내 백분위이며 Q·C·S를 0–100점 척도로 표시합니다.</div>
    <h3>기본 기여 Q</h3><p>효율은 TS%, 득점은 36분당 득점, 리바운드는 공격+수비 리바운드/36분, 볼 연결은 축소 AST/TOV입니다. 출전량이 적은 선수의 극단적인 통계를 줄이기 위해 리그 사전값으로 축소했습니다. 기본 기여를 60% 둔 것은 공격 보완뿐 아니라 독립적으로 경기에 기여할 능력도 평가하려는 분석자의 선택입니다. 승률을 최대화하도록 학습한 비중은 아닙니다.</p>
    <h3>보완 C</h3><p>맥컬러가 표본 중위값(50백분위)에 못 미친 세 항목을 사용했습니다. 효율 11.1백분위, 볼 연결 13.9, 외곽 생산 27.8이므로 50까지 부족한 정도를 정규화해 <b>효율 40.0%·볼 연결 37.1%·외곽 생산 22.9%</b>를 얻었습니다. 후보가 맥컬러보다 높은 부분만 기여하고, 각 항목의 가능한 최대 개선 폭으로 정규화했습니다.</p>
    <div class="formula">wⱼ = max(50 − 맥컬러 백분위ⱼ, 0) / 부족분 합계<br>C = 100 × [Σ wⱼ × max(후보 백분위ⱼ − 맥컬러 백분위ⱼ, 0)] / [Σ wⱼ × (100 − 맥컬러 백분위ⱼ)]</div>
    <p>높은 보완 점수가 모든 항목의 강점을 보장하지는 않습니다. 효율·패스가 좋은 선수도 외곽이 약할 수 있으므로 항목별 프로필과 선수 카드의 제한점을 함께 확인해야 합니다. 리바운드가 이미 강점인 맥컬러의 보완 C에는 리바운드를 넣지 않고 기본 기여 Q에서 유지했습니다.</p>
    <h3>참조집단과 선별 조건</h3><p>백분위는 맥컬러를 포함한 외국인 36명(200분 이상)으로 고정합니다. 보고서의 후보 35명은 이 집단에서 맥컬러만 제외한 수입니다. 은퇴 보도 선수도 다른 선수와 같은 점수·순위 계산에 포함합니다. 포지션이나 계약으로 화면을 필터링해도 백분위를 다시 계산하지 않습니다.</p><p>기존 역할 조건인 400분 이상·198cm 이상·축소 REB/36분 8 이상은 현재 선택 필터입니다. 포지션 적합성을 직접 학습한 기준이 아니고, 신장과 리바운드로 수비력을 보장하지도 않습니다. 표본 200–399분 선수는 순위에 포함하되 출전량과 재표집 변동을 함께 확인합니다.</p>
    <h3>실측 기록과 축소 기록</h3><div class="scroll"><table><thead><tr><th>지표</th><th>실측 계산</th><th>순위에 쓰는 축소 방식</th><th>해석</th></tr></thead><tbody><tr><td>36분당 기록</td><td>기록 × 36 / 출전분</td><td>(기록 × 36 + 200 × 리그 평균/36분) / (출전분 + 200)</td><td>적은 출전량의 극단값을 완화</td></tr><tr><td>3점 성공률</td><td>3PM / 3PA</td><td>(3PM + 50 × 리그 3P%) / (3PA + 50)</td><td>시도량이 적은 성공률을 완화</td></tr><tr><td>외곽 생산</td><td>3PM / 36분 환산</td><td>축소 3PA/36분 × 축소 3P%</td><td>볼륨과 정확도를 함께 반영</td></tr><tr><td>TS%</td><td>PTS / [2 × (FGA + 0.44 FTA)]</td><td>(PTS + 100 × 리그 TS) / [2 × (FGA + 0.44 FTA) + 100]</td><td>자유투를 포함한 득점 효율</td></tr><tr><td>AST/TOV</td><td>AST / TOV</td><td>축소 AST / max(축소 TOV, 0.1)</td><td>볼 연결과 실책의 대리 지표</td></tr></tbody></table></div></section>
    <section id="interpretation"><h2>05 · 삼성에서 확인해야 할 실제 역할</h2><div class="scroll"><table><thead><tr><th>운용 시나리오</th><th>보완 질문</th><th>자료에서 볼 수 있는 것</th><th>추가 검증</th></tr></thead><tbody><tr><td>맥컬러와 동시 출전</td><td>외곽 공간·패스 선택지를 늘리는가?</td><td>3점 생산, TS, AST/TOV</td><td>스크린·롤/팝·하이로 패스·코너 공간의 영상</td></tr><tr><td>맥컬러와 교대</td><td>독립적인 득점·리바운드를 유지하는가?</td><td>36분당 생산 및 기본 기여 점수</td><td>외국인 1명 운용 라인업과 국내 동료 조합</td></tr><tr><td>상대 빅맨 대응</td><td>수비·박스아웃·파울 관리를 수행하는가?</td><td>신장·리바운드는 일부 대리 정보</td><td>수비 매치업, 림 근처 허용률, 파울, 영상</td></tr><tr><td>실제 계약</td><td>예산·이적 조건·건강 상태가 맞는가?</td><td>기존 공개 계약 확인 상태</td><td>구단·에이전트 확인, 메디컬, 등록 조건</td></tr></tbody></table></div>
    <p>선수 유형을 더 정확히 표현하면 <b>“리바운드 기본 기여를 갖춘 효율·볼 연결형 빅맨, 그중 외곽 생산이 검증된 선수 우선”</b>입니다. 이 요구에는 Pember·Thompkins가 여러 항목을 함께 충족하고, Todorovic은 공격형 센터, Beech는 외곽 특화형으로 검토할 수 있습니다. Gaddefors·Diallo처럼 다른 강점으로 점수가 높은 선수는 다른 전술 시나리오로 읽어야 합니다.</p>
    <h3>발표에서 구분할 네 가지 주장</h3><ol><li><b>관측 사실:</b> 맥컬러는 해당 표본에서 리바운드가 높고 효율·볼 연결·외곽 생산이 상대적으로 낮습니다.</li><li><b>전술 가설:</b> 효율·패스·외곽을 보완하는 파트너가 삼성의 공격 선택지를 넓힐 수 있습니다.</li><li><b>모델 검증:</b> 기존 GNN보다 Graph-KRR 오차가 작지만 단순 기준선 대비 추가 예측 이득은 부족합니다.</li><li><b>스카우팅 정책:</b> 가설을 점수로 명시해 35명의 검토 순서를 만들었습니다. 실제 궁합·승률·계약 가능성을 검증한 순서는 아닙니다.</li></ol></section>'''
    dest=P/'mcc_gnn_report.html';content=dest.read_text(encoding='utf-8')
    content=re.sub(r'<section id="fa">.*?</section>',scope+'\n'+detail,content,flags=re.S)
    content=content.replace('<title>McCullough · 그래프 커널 검증과 FA 스카우팅</title>','<title>McCullough · 외국인 35명 확장 순위와 그래프 분석 상세 보고서</title>')
    content=content.replace('GRAPH LEARNING · V2','GRAPH LEARNING · EXPANDED REPORT')
    content=content.replace('확인된 FA 영입 후보 검증','외국인 선수 35명 영입 검토 순위')
    content=content.replace('<a href="#fa">FA 후보</a>','<a href="#ranking">확장 순위</a><a href="#scoring">점수 계산</a><a href="#interpretation">전술 해석</a>')
    content=content.replace('<span class="big">0명</span>보유 데이터에서 확인된 FA 후보','<span class="big">35명</span>계약 제한 없는 영입 검토 순위')
    content=content.replace('04 · 재현 가능한 검증 설계와 적용 한계','06 · 재현 가능한 검증 설계와 적용 한계').replace('05 · 발표·재현 파일','07 · 발표·재현 파일')
    content=content.replace('보고서·FA 필터 코드','이전 검증 보고서 코드')
    content=content.replace('현재 FA임을 명시한 구단/선수/에이전트의 최신 확인, 해당 선수의 경기 기록','구단/선수/에이전트의 최신 계약 조건 확인, 다른 리그 후보의 동일 기준 경기 기록')
    content=content.replace('전 세계 FA 탐색·다른 리그 성적 수집','전 세계 외국인 선수의 전수 탐색·다른 리그 성적 수집')
    content=content.replace('<code>python strengthen.py</code> → <code>python build_report.py</code>','<code>python strengthen.py</code> → <code>python build_report.py</code> (보고서 생성 시 확장 순위·재표집도 갱신)')
    content=content.replace('<a href="build_report_v2.py">이전 검증 보고서 코드</a>','<a href="build_report_v3.py">상세 보고서 코드</a> · <a href="expand_scouting.py">확장 순위 계산</a> · <a href="v2/expanded_summary.json">확장 검증 요약</a>')
    extra_css='''.controls{display:grid;grid-template-columns:1.1fr 1fr 1.2fr;gap:14px;margin:20px 0}.controls label{font-size:14px;font-weight:bold}.controls input,.controls select{display:block;width:100%;margin-top:6px;padding:11px;font:inherit;border:1px solid #718697;border-radius:6px;background:white;color:#142b40}.rank-table{min-width:1300px}.rank-table td:nth-child(2){min-width:200px}.rank-table td:nth-child(11){min-width:140px}.rank-table .score{font-weight:bold;font-size:18px}.player-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.player-card{padding:22px;border:1px solid #d9e1e8;border-radius:10px;background:#f8fafb}.player-card h3{font-size:22px;margin:6px 0}.small{font-size:13px}.formula{padding:20px;background:#e9f1f5;border-radius:8px;overflow-wrap:anywhere}.pill{display:inline-block;font-size:12px;padding:3px 8px;background:#e8f2ed;color:#1b5b43;border-radius:4px}.pill.other{background:#fff1e5;color:#885021}@media(max-width:700px){.controls,.player-grid{grid-template-columns:1fr}.player-card{padding:18px}}'''
    content=content.replace('</style>',extra_css+'</style>')
    # Replace the previous contract-only table script; all UI state is URL-backed.
    records=json.loads(d.to_json(orient='records'));payload=json.dumps(records,ensure_ascii=False).replace('</',r'<\/')
    js='''const candidates=DATA;const search=document.querySelector('#candidateSearch'),role=document.querySelector('#roleFilter'),mix=document.querySelector('#mix');const fmt=(v,n=1)=>v==null?'—':Number(v).toFixed(n);const safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    function draw(){const w=Number(mix.value)/100;let all=candidates.map(d=>({...d,current:w*d.quality_score+(1-w)*d.complement_score})).sort((a,b)=>b.current-a.current);all.forEach((d,i)=>d.currentRank=i+1);let q=search.value.trim().toLowerCase();const list=all.filter(d=>(role.value==='all'||(role.value==='role'?d.screen_pass:!d.screen_pass))&&(`${d.name} ${d.team_in_dataset}`.toLowerCase().includes(q)));document.querySelector('#candidateRows').innerHTML=list.map(d=>`<tr><td>${d.currentRank}</td><td><b>${safe(d.name)}</b><br><span class="muted">${safe(d.team_in_dataset)}<br>${fmt(d.height_cm,0)}cm · ${safe(d.position)}</span></td><td class="score">${fmt(d.current)}</td><td>${fmt(d.quality_score)} / ${fmt(d.complement_score)}</td><td><span class="pill ${d.screen_pass?'':'other'}">${d.screen_pass?'통과':'미충족'}</span></td><td>${fmt(d.minutes)}</td><td>${fmt(d.pts36)} / ${fmt(d.reb36)} / ${fmt(d.ast36)}</td><td>${fmt(100*d.ts)}%</td><td>${d.three_made}/${d.three_attempts}<br>${fmt(100*d.three_pct)}%</td><td>${fmt(d.score_lo)}–${fmt(d.score_hi)}<br><span class="muted">기준 순위 ${fmt(d.rank_lo)}–${fmt(d.rank_hi)}</span></td><td>${safe(d.status)}<br><span class="muted">2026-10-10</span><br>${d.source_url?`<a href="${safe(d.source_url)}" target="_blank" rel="noopener">근거</a>`:'확인 자료 없음'}</td></tr>`).join('');document.querySelector('#candidateCount').textContent=`${list.length}명 표시 / 전체 35명 · 기본 기여 ${mix.value}% + 보완 ${100-Number(mix.value)}%`;const u=new URL(location);for(const [k,v,def] of [['q',search.value,''],['role',role.value,'all'],['mix',mix.value,'60']])v===def?u.searchParams.delete(k):u.searchParams.set(k,v);history.replaceState(null,'',u)}
    const params=new URL(location).searchParams;search.value=params.get('q')||'';role.value=['all','role','other'].includes(params.get('role'))?params.get('role'):'all';mix.value=['40','60','80'].includes(params.get('mix'))?params.get('mix'):'60';search.addEventListener('input',draw);role.addEventListener('change',draw);mix.addEventListener('change',draw);draw();'''.replace('DATA',payload,1)
    content=re.sub(r'<script>.*?</script>','<script>'+js+'</script>',content,flags=re.S)
    assert '검증된 후보 0명' not in content
    from standalone_html import embed_images
    content,embedded_count=embed_images(content,P)
    assert embedded_count==8
    dest.write_text(content,encoding='utf-8')
    (V/'report_checks.json').write_text(json.dumps({'ranked_candidates':len(d),'role_candidates':int(d.screen_pass.sum()),'benchmark_only':len(bench),'contract_filter':False,'figures_used':8,'embedded_images':embedded_count,'standalone_images':True,'removed_typo_commentary':True},indent=2),encoding='utf-8')
    print('Expanded detailed report built:',len(d),'ranked candidates')
if __name__=='__main__':main()
