"""Build a portable Korean report from observed-pair analysis outputs."""
from pathlib import Path
import base64, html, json, zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parent;P=ROOT/'foreign_pair_analysis'
read=lambda f:pd.read_csv(P/f)
s=read('pair_summary.csv');c=read('pair_comparisons.csv');a=read('adjusted_contrasts.csv');t=read('target_role_profiles.csv');allp=read('tpbl_import_profiles_all48.csv');links=read('direct_assist_links.csv');prod=read('partner_production_in_pairs.csv');sens=read('filter_sensitivity.csv');audit=json.loads((P/'audit.json').read_text(encoding='utf8'))
order=['Lasannah Kromah','Malcolm Miller','Cheick Diallo']
s=s.set_index('partner').loc[order].reset_index();t=t.set_index('name').loc[order].reset_index();links=links.set_index('partner').loc[order].reset_index();prod=prod.set_index('partner').loc[order].reset_index()
f=lambda x:f'{float(x):.1f}'
sg=lambda x:f'{float(x):+.1f}'
interval=lambda r,k,scale=1:f"{float(r[k+'_lo'])*scale:.1f}~{float(r[k+'_hi'])*scale:.1f}"
def mdtable(head,rows):return '| '+' | '.join(head)+' |\n|'+'|'.join(['---']*len(head))+'|\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in rows)
def htable(head,rows):return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+html.escape(v)+'</th>' for v in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'

teamhead=['파트너','구간 / 경기','함께 뛴 분','팀 득점 / 실점','누적 득실','득점/100','실점/100','순득실/100']
teamrows=[[r.partner,f'{r.stints} / {r.games}',f(r.minutes),f'{int(r.leo_pts)} / {int(r.opp_pts)}',f'{int(r.margin):+d}',f(r.team_pts100),f(r.opponent_pts100),sg(r.net100)] for r in s.itertuples()]
mcch=['파트너','맥컬러 득점/36','맥컬러 TS','맥컬러 슛시도/36','어시스트 받은 야투 비율']
mccr=[[r.partner,f(r.mcc_pts36),f(100*r.mcc_ts)+'%',f(r.mcc_fga36),f(100*r.mcc_assisted_share)+'%'] for r in s.itertuples()]
otherh=['파트너','맥컬러 AST/36','맥컬러 REB/36','맥컬러 TOV/36']
otherr=[[r.partner,f(r.mcc_ast36),f(r.mcc_reb36),f(r.mcc_tov36)] for r in s.itertuples()]
uncertaintyh=['파트너','순득실/100 재표집 범위','맥컬러 득점/36 범위','맥컬러 TS 범위']
uncertaintyr=[[r['partner'],interval(r,'net100'),interval(r,'mcc_pts36'),interval(r,'mcc_ts',100)+'%'] for _,r in s.iterrows()]
wc=c[(c.method=='within_same_game_harmonic_weight')&(c.min_shared_minutes==2)&(c.metric=='mcc_pts36')]
wh=['같은 경기 내 비교','경기 수','맥컬러 득점 차이/36','재표집 95% 범위']
wr=[[r.a+' - '+r.b,int(r.games),sg(r.difference),f(r.lo)+'~'+f(r.hi)] for r in wc.itertuples()]
adj=a[(a.spec=='game_FE_context_domestic')&(a.metric=='mcc_pts36')]
adjh=['경기·맥락·국내 동료 보정','맥컬러 득점 차이/36','재표집 95% 범위']
adjr=[[r.a+' - '+r.b,sg(r.difference),f(r.lo)+'~'+f(r.hi)] for r in adj.itertuples()]
lh=['파트너','파트너가 도운 맥컬러 야투 성공','해당 득점','연결 야투/36','동시 출전 파트너 득점/36']
lr=[[r.partner,int(r.partner_to_mcc_fg_assists),int(r.partner_to_mcc_assisted_points),f(r.partner_to_mcc_fg_assists36),f(prod.set_index('partner').loc[r.partner,'partner_pts36'])] for r in links.itertuples()]
th=['선수','역할 해석','AST/36','REB/36','BLK/36','3점 성공/시도','TS']
tr=[[r['name'],r.target_interpretation,f(r.ast36),f(r.reb36),f(r.blk36),f'{int(r.three_PM)}/{int(r.three_PA)} ({100*r.three_pct:.1f}%)',f(100*r.ts)+'%'] for _,r in t.iterrows()]
ph=['선수','공격 전개','외곽 생산','리바운드','블록 기여','효율','슛 사용량','AST/TOV']
pr=[[r['name']]+[f(r[k+'_pctile']) for k in ['creation','shooting','rebounding','blocking','efficiency','shot_usage','ball_security']] for _,r in t.iterrows()]

sections=[
('분석 범위','''맥컬러와 크로마·밀러·디알로 각각의 **2인 조합 세 가지**를 비교했다. 네 외국인이 동시에 뛰는 조합을 뜻하지 않는다.

기존 v2와 동일한 2025–26 TPBL 정규시즌, 유효한 5대5, 코트 밖 선수 이벤트가 없는 구간 중 30초 이상·가비지 제외 조건을 적용했다. 맥컬러 출전 24경기·385구간·595.2분에서 단독 외국인 1구간·2.78분을 제외한 **384구간·592.42분**이 세 조합의 분석 대상이다. 단독 외국인 구간이 너무 적어, “파트너 없이 뛸 때보다 얼마나 끌어올렸는가”는 신뢰할 만하게 추정할 수 없다.

유형화 자료는 보유 정규시즌 선수 기록 7팀·126경기에서 확인한 외국인 **48명 전원**이다. 200분 이상 36명을 안정적인 비교 참조집단으로 사용하고, 200분 미만 12명도 프로필에 포함하되 낮은 표본임을 표시했다.'''),
('조합별 팀 득실',mdtable(teamhead,teamrows)+'''

득점/100과 실점/100은 양 팀 평균 추정 포제션을 공통 분모로 사용한다. 따라서 두 값의 차이가 순득실/100과 일치한다. 포제션은 정확한 공격 횟수 계수가 아니라 `FGA - OREB + TOV + 0.44 × FTA`의 박스스코어 추정치이다.

**팀 순득실은 디알로 조합이 가장 높다.** 디알로 조합은 득점/100이 111.8로 가장 높고, 밀러 조합은 실점/100이 93.1로 가장 낮다. 크로마 조합에서는 팀 순득실이 거의 중립이다. 상대·국내 동료·출전 시점의 차이를 포함한 관측 집계이며, 파트너가 그 성과를 만들었다는 인과 해석은 하지 않는다.'''),
('맥컬러 개인 성과',mdtable(mcch,mccr)+'''

**맥컬러 개인 득점과 TS는 크로마와 함께 뛴 구간에서 가장 높다.** 밀러 대비 득점은 +4.18점/36분, TS는 +4.81%p이고, 디알로 대비 득점은 +9.23점/36분, TS는 +11.55%p이다. 맥컬러의 슛 사용량도 크로마 조합에서 가장 높다.

이는 “개인 득점·효율이 가장 높은 조합”과 “팀 순득실이 가장 좋은 조합”이 다를 수 있음을 보여준다. 맥컬러에게 가장 좋은 파트너를 한 명으로 확정하려면 개인 성과와 팀 성과 중 무엇을 우선할지 정해야 한다.

'''+mdtable(otherh,otherr)+'''

맥컬러의 어시스트는 디알로 조합에서 가장 높다. 따라서 개인 성능 전체를 하나의 지표로 묶어 크로마가 모든 면에서 우월했다고 해석하지 않는다. 높은 득점·효율이라는 판단의 범위를 유지해야 한다.'''),
('경기 표본의 불확실성',mdtable(uncertaintyh,uncertaintyr)+'''

같은 경기의 구간을 독립 표본으로 취급하지 않고, 24경기를 단위로 5,000회 재표집하여 매번 합계의 비율을 다시 계산했다. 표시 구간은 재표집 분포의 2.5~97.5% 범위다. 모든 조합의 팀 순득실 구간이 0을 포함하며, 순위가 확정적인 것은 아니다. 여러 지표를 탐색했으므로 구간을 하나 골라 확증적인 통계 검정처럼 사용하지 않는다.'''),
('같은 경기에서 파트너가 달랐던 구간 비교',mdtable(wh,wr)+'''

두 조합이 모두 2분 초과 출전한 경기만 사용했다. 경기별 각 조합의 성과율 차이를 구하고, 두 조합 노출시간의 조화 가중치 `tA × tB / (tA + tB)`로 평균했다. 같은 경기를 비교하므로 상대 팀·홈/원정·날짜 수준의 차이를 줄이지만, 상대 라인업과 출전 시점이 완전히 같아지지는 않는다.

**크로마와 밀러의 차이는 전체 집계의 +4.18점에서 같은 경기 비교의 +0.52점으로 줄었다.** 비교 가능한 12경기의 재표집 구간은 -10.85~+12.07점으로, 크로마가 밀러보다 맥컬러 득점을 확실히 높였다고 말하기 어렵다.

크로마와 디알로의 동일 경기 비교에서는 맥컬러 득점이 크로마 쪽에서 +13.14점/36분 높았지만 비교 경기가 5개다. 같은 경기에서 팀 순득실은 오히려 크로마 쪽이 -22.69점/100으로 낮았다. 작은 표본에서 개인 공격과 팀 성과의 방향이 다른 결과이다.'''),
('추가 보정 비교',mdtable(adjh,adjr)+'''

경기 고정효과, 쿼터, 구간 시작 점수 차, 정규시간 잔여시간, 공출전 60분 이상 주요 국내 선수의 출전 여부를 포함한 시간 가중 선형모형도 추정했다. 가장 많이 뛴 국내 선수를 참조로 두었다. 24경기를 2,000회 재표집하고 회귀계수를 다시 추정했다.

**맥컬러 득점의 세 쌍 비교는 추가 보정 후 모두 0을 포함하는 넓은 구간을 보였다.** “크로마와 함께 뛸 때 관측 공격 성과가 가장 높았다”는 결론은 가능하지만, “크로마의 독립적인 상승 효과가 검증됐다”는 결론은 어렵다. 이 회귀는 관측 연관성을 비교하며 예측 성능이나 인과효과를 검증하는 모델이 아니다. 상대 선수 구성·피로·수비 전술 등은 보정하지 못했다.'''),
('직접 연결 기록과 역할 분담',mdtable(lh,lr)+'''

PBP에서 연결된 파트너 어시스트로 맥컬러가 성공한 야투는 크로마 19회, 밀러 12회, 디알로 1회이다. 출전시간을 보정해도 각각 2.77·1.90·0.30회/36분이다. 맥컬러 전체 야투 성공 중 동료 어시스트가 붙은 비율도 크로마 조합 62.9%, 밀러 53.1%, 디알로 29.4%이다. 앞의 19/12/1회는 해당 외국인 파트너의 직접 연결만 세고, 뒤의 비율은 국내 동료를 포함한 모든 어시스트를 센다.

디알로는 맥컬러와 함께 뛴 구간에서 본인이 25.51점/36분을 기록했고, 맥컬러는 14.27점이었다. 크로마 조합에서는 각각 21.17점과 23.51점이었다. 따라서 디알로 조합의 좋은 팀 득실을 맥컬러 개인 공격 상승으로 설명하면 맞지 않는다. 기록상 득점 역할 배분도 함께 달랐다. PBP 어시스트 연결은 정제 코드가 매칭한 기록이므로 전수 영상 확인을 마친 패스 품질 평가와는 구분한다.'''),
('TPBL 전체 외국인 기반 유형화',mdtable(th,tr)+'''

이 표의 개인 기록은 조합 구간 기록이 아닌 **각 선수의 정규시즌 전체 기록**이다. 유형은 시즌 기록을 리그 사전값으로 축소한 뒤, 200분 이상 외국인 36명 내 백분위로 해석했다. 아래 백분위는 성공률이나 승률이 아니다.

'''+mdtable(ph,pr)+'''

**크로마: 공격 전개와 슛 사용량이 큰 윙.** 축소 AST/36분은 36명 중 가장 높고, AST/TOV는 91.7백분위다. 3점은 37/123(30.1%), 외곽 생산은 38.9백분위여서, 슈팅 전문 선수라는 해석보다 공격 전개 역할이 자료에 더 잘 맞는다. 스틸 생산도 높지만 완전한 수비 능력을 뜻하지 않는다.

**밀러: 블록 기여가 크고 슛 사용량이 낮은 윙.** 블록은 94.4백분위이고 FGA/36분은 25.0백분위다. 공격 전개와 리바운드는 표본 중간 수준이다. 3점은 30/103(29.1%)이고 외곽 생산은 33.3백분위로, 외곽 전문 슈터로 분류할 근거는 약하다. 블록 기록만으로 수비 전반이 우수하다고 단정하지 않는다.

**디알로: 인사이드 마무리와 리바운드 중심 빅맨.** 축소 리바운드와 페인트존 슛 비중이 모두 100백분위이며, TS는 97.2백분위다. 3점은 0/1이고 AST/TOV는 8.3백분위로, 공간 창출과 공격 전개보다는 인사이드 마무리 성격이 강하다. 맥컬러와 일부 역할이 겹칠 수 있다는 가설을 세울 수 있지만, 역할 중복이 실제로 해롭다는 인과 결론은 아니다.'''),
('유형의 경계와 전체 48명 산출 방식','''유형 표시는 상위 사분위(75백분위 이상) 특성을 복수 태그로 붙이고, 슛 사용량 25백분위 이하는 별도로 표시했다. 모든 선수를 하나의 배타적인 유형에 억지로 넣지 않았다. 200분 미만 선수의 백분위는 고정된 36명 참조집단에 대한 경험분포 위치로 산출하고, 낮은 표본 표시를 유지했다. CSV에는 전체 48명 내 백분위도 별도 칼럼으로 제공한다.

보조적으로 36명에서 3점 시도 비중·페인트존 시도 비중·AST·REB·BLK·STL·FGA의 7축을 표준화해 K-means 2~6군집을 비교했다. 실루엣은 2군집 0.253, 3군집 0.248이었다. 뚜렷한 세 유형의 경계를 강하게 뒷받침하는 결과는 아니다. 선택된 2군집에서는 크로마가 공격 전개 중심 그룹에, 밀러와 디알로가 리바운드·인사이드 기여 그룹에 함께 속했다. 밀러와 디알로의 차이는 개별 프로필로 설명하는 편이 정확하다.

분당 기록은 리그 평균 200분의 사전값, 3점 성공률은 리그 평균 50시도의 사전값, TS는 분모 100의 사전값으로 축소했다. 전체 48명의 원자료·축소값·백분위·유형 태그·군집은 `tpbl_import_profiles_all48.csv`에 있다. 이 유형화는 선수의 관측 스타일을 설명하며 다른 조합의 성과를 예측하지 않는다.'''),
('필터 민감도와 남은 한계','''30초 미만 구간을 포함하거나 60초 이상만 남기거나 가비지 구간을 포함해도, 맥컬러 득점과 TS의 관측 순서는 크로마·밀러·디알로 순으로 유지됐다. 팀 순득실의 관측 순서는 디알로·밀러·크로마 순이었다. 다만 60초 이상 조건에서는 팀 순득실/100이 크로마 -9.8, 밀러 +5.1, 디알로 +7.0으로 바뀌어 효과 크기와 양·음 해석은 필터에 민감했다.

파트너 교체는 무작위 배정이 아니다. 감독의 선택, 상대 선수, 국내 동료, 파울, 피로, 경기 국면이 조합 성과와 함께 바뀐다. 경기 재표집은 이를 모두 해결하지 않는다. 단독 외국인 비교 기준도 2.78분뿐이다. 현재 자료는 세 파트너 사이의 관측 비교이며, 파트너가 없는 상태 대비의 검증된 상승 효과나 TPBL 전체 조합의 인과 순위를 제시하지 않는다.'''),
('발표용 핵심 문구','''“맥컬러의 개인 공격 성과는 크로마와 함께 뛸 때 가장 높았고, 팀 순득실은 디알로와 함께 뛸 때 가장 좋았다.”

“크로마는 TPBL 외국인 표본에서 공격 전개가 두드러지고, 맥컬러에게 직접 연결한 야투 어시스트도 가장 많았다. 그러나 동일 경기 비교와 추가 보정에서는 밀러 대비 우월성을 확정하지 못했다.”

“세 파트너를 비교한 관측 근거에서는 공격 전개 역할을 우선 검증할 가치가 있다. 슈팅 빅맨이 최적이라는 일반 결론이나 크로마형 선수의 성공 보장은 아직 제시할 수 없다.”'''),
('재현과 근거 파일','''재실행: `python analyze_foreign_pairs.py` 실행 후 `python build_foreign_pair_report.py`. 기존 `GNN` 원자료 폴더가 필요하다. numpy·pandas·matplotlib·scikit-learn을 사용한다. seed=20261010.

- `pair_summary.csv`: 조합별 합계·성과·경기 재표집 구간
- `pair_by_game.csv`, `within_game_details.csv`: 경기별 집계와 동일 경기 비교 근거
- `pair_comparisons.csv`, `adjusted_contrasts.csv`: 원집계·동일 경기·보정 비교
- `direct_assist_links.csv`, `partner_production_in_pairs.csv`: 직접 연결과 역할 배분
- `tpbl_import_profiles_all48.csv`, `target_role_profiles.csv`: 48명 전체 및 대상 프로필
- `cluster_selection.csv`, `cluster_centers_standardized.csv`, `role_neighbors.csv`: 보조 유형화
- `filter_sensitivity.csv`: 구간 필터 변경에 따른 결과
- `audit.json`: 자료 범위·조건·해시·회귀 식별성 검사
- `figures/`: 발표용 PNG/SVG 4종

원자료는 기존 프로젝트의 `GNN/output_data/gnn_dataset/`, `GNN/input_data/`, `GNN/pbp_tables/`에서 읽었다. 루트의 이전 `observed_partners.csv`는 401구간 기준이므로 이번 정제 385구간 결과와 섞지 않는다.''')]

intro='''# 맥컬러와 외국인 파트너 조합 분석

**관측상 맥컬러 개인 공격은 크로마 조합, 팀 순득실은 디알로 조합에서 가장 좋았다.** 다만 크로마가 밀러보다 맥컬러 성능을 독립적으로 높였다는 결론은 같은 경기 비교와 보정 분석에서 확정하지 못했다.

'''
md=intro+'\n\n'.join('## '+title+'\n\n'+body for title,body in sections)
(P/'외국인_조합_분석.md').write_text(md,encoding='utf8')

# Render the report from the same text; tables/figures remain visible without JS.
def inline(s):
    import re
    z=html.escape(s)
    z=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',z)
    z=re.sub(r'`(.+?)`',r'<code>\1</code>',z)
    return z
def body_html(body):
    result=[]
    for block in body.split('\n\n'):
        lines=block.splitlines()
        if lines and lines[0].startswith('|'):
            cells=[[v.strip() for v in line.strip('|').split('|')] for line in lines]
            result.append(htable(cells[0],cells[2:]))
        elif lines and all(line.startswith('- ') for line in lines):result.append('<ul>'+''.join('<li>'+inline(line[2:])+'</li>' for line in lines)+'</ul>')
        else:result.append('<p>'+inline(block)+'</p>')
    return ''.join(result)
figures={2:'01_pair_outcomes',4:'02_within_game_comparisons',7:'03_partner_role_profiles',8:'04_tpbl_role_map'}
contents=[]
for i,(title,body) in enumerate(sections):
    contents.append('<section><h2>'+html.escape(title)+'</h2>'+body_html(body))
    if i in figures:
        stem=figures[i];b64=base64.b64encode((P/'figures'/(stem+'.png')).read_bytes()).decode()
        contents.append(f'<figure><a href="data:image/png;base64,{b64}" download="{stem}.png"><img src="data:image/png;base64,{b64}" alt="{html.escape(title)}"></a><figcaption>이미지를 눌러 발표용 PNG 저장</figcaption></figure>')
    contents.append('</section>')

full=allp[['name','team','minutes','reference_200min','role_tags','exploratory_cluster_label']].copy()
full.columns=['선수','자료 당시 소속','출전분','200분 이상','역할 태그','보조 군집'];full['출전분']=full['출전분'].map(f);full['200분 이상']=full['200분 이상'].map({True:'예',False:'아니오: 낮은 표본'})
contents.append('<section><h2>외국인 48명 전체 프로필</h2><p>표본 내 스타일 비교이며 영입 추천 순위가 아닙니다. 세부 수치는 CSV에 있습니다.</p><div class="scroll">'+full.to_html(index=False,escape=True,border=0)+'</div></section>')
style='''body{font-family:"Malgun Gothic",sans-serif;margin:0;color:#20333f;background:#f4f6f7;line-height:1.8}main{max-width:1200px;margin:auto;padding:46px 36px;background:white}h1{font-size:36px;line-height:1.35}h2{font-size:25px;line-height:1.45;margin-top:44px;color:#176a80}p{font-size:17px;max-width:1050px}table{border-collapse:collapse;min-width:650px;width:100%;font-size:15px}th,td{padding:11px 13px;text-align:left;border-bottom:1px solid #dbe3e8;vertical-align:top}th{background:#eef3f5;white-space:nowrap}.scroll{overflow-x:auto}figure{margin:28px 0}img{width:100%;height:auto}figcaption{font-size:13px;color:#607481}code{background:#eef3f5;padding:2px 5px}strong{color:#176a80}@media(max-width:600px){main{padding:24px 18px}h1{font-size:29px}h2{font-size:23px}p{font-size:16px}}@media print{main{padding:0}body{background:white}figure,table{break-inside:avoid}h2{break-after:avoid}}'''
ht='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>맥컬러 외국인 조합 분석</title><style>'+style+'</style><main><h1>맥컬러와 외국인 파트너 조합 분석</h1><p><strong>관측상 개인 공격은 크로마 조합, 팀 순득실은 디알로 조합에서 가장 높습니다.</strong> 같은 경기 비교와 보정 분석에서는 크로마의 밀러 대비 우월성을 확정하지 못했습니다.</p>'+''.join(contents)+'</main></html>'
(P/'외국인_조합_분석.html').write_text(ht,encoding='utf8')

ppt='''# 외국인 조합 분석 발표용 문구

## 1장. 개인 공격 성과와 팀 순득실은 서로 다른 조합에서 가장 높음

'''+mdtable(['조합','팀 순득실/100','맥컬러 득점/36','맥컬러 TS'],[[r.partner,sg(r.net100),f(r.mcc_pts36),f(100*r.mcc_ts)+'%'] for r in s.itertuples()])+'''

발표: “맥컬러의 개인 공격은 크로마 조합에서 가장 좋았지만 팀 순득실은 디알로 조합에서 가장 좋았습니다. 개인 성과와 팀 성과를 구분해야 합니다.”

그림: `figures/01_pair_outcomes.png`

## 2장. 동일 경기 비교에서는 크로마와 밀러의 차이가 불확실

- 전체 집계 맥컬러 득점 차이: 크로마가 밀러보다 +4.18점/36분
- 두 조합이 모두 2분 초과 뛴 12경기 내 비교: +0.52점/36분
- 재표집 95% 범위: -10.85~+12.07점
- 경기·맥락·주요 국내 동료 추가 보정에서도 우월성 미확정

발표: “크로마 조합의 높은 관측 기록은 확인했지만, 파트너의 독립적인 상승 효과를 검증했다고 결론내리기는 어렵습니다.”

그림: `figures/02_within_game_comparisons.png`

## 3장. TPBL 전체 외국인 기록으로 해석한 세 파트너의 역할

- 크로마: 공격 전개와 슛 사용량이 큰 윙. AST 6.56/36분, 공격 전개 100백분위
- 밀러: 블록 기여가 크고 슛 사용량이 낮은 윙. BLK 1.60/36분, 블록 94.4백분위
- 디알로: 인사이드 마무리와 리바운드 중심 빅맨. REB 14.97/36분, 리바운드 100백분위
- 기록에 나타난 외국인 48명 전원 산출, 200분 이상 36명 비교 기준

발표: “세 선수를 각각 다른 역할로 설명할 수 있지만, 군집 분석이 세 개의 뚜렷한 경계를 입증한 것은 아닙니다. 따라서 다축 프로필로 유형을 해석했습니다.”

그림: `figures/03_partner_role_profiles.png`, `figures/04_tpbl_role_map.png`

## 4장. 공격 전개 역할을 우선 검증할 관측 근거

- 파트너 어시스트로 맥컬러가 성공한 야투: 크로마 19회, 밀러 12회, 디알로 1회
- 출전시간 보정: 2.77 / 1.90 / 0.30회/36분
- 크로마는 외곽 생산보다 공격 전개에서 두드러짐
- 실제 조합 효과는 상대 라인업·출전 국면·수비를 포함해 추가 검증 필요

발표: “현재 세 조합에서는 공격 전개를 보완하는 파트너를 우선 검증할 근거가 있습니다. 좋은 조합을 확정하거나 같은 유형 선수의 성공을 보장한 결과는 아닙니다.”
'''
(P/'발표용_핵심문구.md').write_text(ppt,encoding='utf8')

# Narrow numerical QA against independent equations, not model-fit quality tests.
assert s.stints.sum()==384
assert abs(s.minutes.sum()-592.4166666666666)<1e-8
assert (s.leo_pts-s.opp_pts==s.margin).all()
assert ((s.team_pts100-s.opponent_pts100-s.net100).abs()<1e-9).all()
assert len(allp)==48 and allp.reference_200min.sum()==36
assert all(r['full_rank_bootstrap_share']==1.0 for r in audit['regression_audit'])
assert not allp.name.duplicated().any()
qa={'pair_count':len(s),'pair_stints':int(s.stints.sum()),'pair_minutes':float(s.minutes.sum()),'all_imports':len(allp),'reference_imports':int(allp.reference_200min.sum()),'margin_and_rate_identities':'passed','game_bootstrap_regression_identification':'passed','figures':4}
(P/'report_checks.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf8')
zip_path=ROOT/'외국인_조합_분석자료.zip'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for item in P.rglob('*'):
        if item.is_file():z.write(item,item.relative_to(ROOT))
    for script in ['analyze_foreign_pairs.py','build_foreign_pair_report.py']:z.write(ROOT/script,script)
print('REPORT',P/'외국인_조합_분석.html')
print('PACKAGE',zip_path)
print(json.dumps(qa,ensure_ascii=False))
