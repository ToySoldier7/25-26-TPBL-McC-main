"""Generate portable Korean report and original SVG figures from computed CSVs."""
from pathlib import Path
from html import escape as E
import json
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent
F=P/'figures'; F.mkdir(exist_ok=True)
A=json.loads((P/'audit.json').read_text(encoding='utf-8'))
obs=pd.read_csv(P/'observed_partners.csv'); imports=obs[obs.imported==1].copy()
trans=pd.read_csv(P/'candidate_transfer.csv'); new=trans[~trans.observed_partner].copy()
metrics=pd.read_csv(P/'model_metrics.csv')
sens=pd.read_csv(P/'transfer_sensitivity.csv').groupby('player_id')['rank'].agg(['min','max'])
trans['rank_min']=trans.player_id.map(sens['min']); trans['rank_max']=trans.player_id.map(sens['max'])
BLUE='#225ac7'; TEAL='#087f78'; INK='#172739'; GRAY='#627084'; ORANGE='#ad5720'
def text(x,y,t,size=16,fill=INK,anchor='start',weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{E(str(t))}</text>'
def line(x1,y1,x2,y2,color='#dde3eb',width=1,dash=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def svg(content,h,title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {h}" role="img" aria-label="{E(title)}"><title>{E(title)}</title><rect width="1000" height="{h}" fill="white"/><g font-family="Malgun Gothic,Arial,sans-serif">{content}</g></svg>'
def save(name,content):
    (F/f'{name}.svg').write_text(content,encoding='utf-8'); return content

c=text(35,38,'GNN은 두 검증에서 모두 단순 기준보다 오차가 컸다',24,weight=700)
c+=text(35,67,'팀 득실 / 36분 예측 RMSE · 낮을수록 좋음 · 고정 설정의 탐색 실험',15,GRAY)
for panel,(split,label) in enumerate([('group_cv','경기별 5분할 · 24경기'),('temporal','시간순 검증 · 마지막 8경기')]):
    y0=112+panel*235; c+=text(35,y0,label,18,weight=700)
    for j,model in enumerate(['Mean','Ridge','No-edge NN','GNN']):
        val=float(metrics[(metrics.split==split)&(metrics.model==model)].net_rmse36.iloc[0]); y=y0+30+j*43
        c+=text(35,y+16,{'Mean':'단순 평균','Ridge':'Ridge','No-edge NN':'엣지 제거 NN','GNN':'관계형 GNN'}[model],16)
        c+=f'<rect x="200" y="{y}" width="{val*7.5}" height="25" rx="3" fill="{ORANGE if model=="GNN" else BLUE}" opacity="{1 if model=="GNN" else .72}"/>'
        c+=text(210+val*7.5,y+19,f'{val:.2f}',17,weight=700)
c+=text(35,577,'GNN의 외삽 순위는 주결론에서 제외. 신경망 전체의 불가능성을 뜻하지는 않음.',15,GRAY)
validation=save('01_model_validation',svg(c,610,'모델 검증: GNN 오차가 기준 모델보다 높음'))

c=text(35,38,'관측 외국인 동료: 디알로가 높지만 우열은 불확실',24,weight=700)
c+=text(35,68,'점 = 120분 사전값으로 축소한 팀 득실 / 36분 · 선 = 경기 부트스트랩 95% 구간',15,GRAY)
x=lambda v:260+(v+10)*22
for tick in [-10,-5,0,5,10,15,20]:
    c+=line(x(tick),100,x(tick),360,INK if tick==0 else '#e4e8ee',1.5 if tick==0 else 1)
    c+=text(x(tick),385,tick,14,GRAY,'middle')
for j,r in enumerate(imports.itertuples()):
    y=145+j*90; col=TEAL if j==0 else BLUE
    c+=text(35,y-7,r.name,18,weight=700)+text(35,y+20,f'{r.minutes:.1f}분 · {r.games}경기',14,GRAY)
    c+=line(x(r.shrunk_lo),y,x(r.shrunk_hi),y,col,4)+f'<circle cx="{x(r.shrunk_net36)}" cy="{y}" r="7" fill="{col}"/>'
    c+=text(x(r.shrunk_net36),y-17,f'{r.shrunk_net36:+.2f}',16,col,'middle',700)
    c+=text(955,y+30,f'[{r.shrunk_lo:.2f}, {r.shrunk_hi:.2f}]',14,GRAY,'end')
c+=text(35,427,'이 값은 동료의 독립적 효과가 아님: 나머지 라인업·상대·기용 상황이 함께 반영됨.',15,GRAY)
intervals=save('02_observed_partners',svg(c,460,'실제 외국인 파트너의 성과와 불확실성'))

c=text(35,38,'팀 득실과 맥컬러 개인 득점은 같은 목표가 아니다',24,weight=700)
c+=text(35,67,'필터를 통과한 실제 공출전 구간 · 축소하지 않은 관측값 · 인과효과 아님',15,GRAY)
xx=lambda v:160+(v-12)*49
yy=lambda v:365-(v+3)*17
for v in [12,15,18,21,24,27]:c+=line(xx(v),100,xx(v),365)+text(xx(v),392,v,14,GRAY,'middle')
for v in [-2,0,4,8,12]:c+=line(160,yy(v),895,yy(v),INK if v==0 else '#e4e8ee')+text(140,yy(v)+5,v,14,GRAY,'end')
for r in imports.itertuples():
    c+=f'<circle cx="{xx(r.mcc_points36)}" cy="{yy(r.net36)}" r="12" fill="{TEAL if r.name=="Cheick Diallo" else BLUE}" fill-opacity=".78"/>'
    c+=text(xx(r.mcc_points36)+22,yy(r.net36)-(30 if r.name=='Lasannah Kromah' else 12),r.name,16,weight=700)
    c+=text(xx(r.mcc_points36)+22,yy(r.net36)+13,f'TS {r.mcc_TS:.1%}',14,GRAY)
c+=text(160,96,'팀 득실 / 36분 ↑',15,GRAY)+text(520,430,'맥컬러 득점 / 36분 →',16,INK,'middle')
c+=text(35,473,'각 점은 실제 동료 1명과의 공출전 집계. 분·경기 수는 앞 그림과 표에서 확인.',14,GRAY)
trade=save('03_objective_tradeoff',svg(c,500,'팀 성과와 개인 득점의 상충관계'))

c=text(35,38,'실제 공출전 그래프에서 새 후보의 유형으로 확장',24,weight=700)
c+=text(35,67,'실선: 관측 공출전 시간 · 점선: 8개 특성의 유사도 가중치 · 경기력 예측선 아님',15,GRAY)
ay={int(r.player_id):155+j*150 for j,r in enumerate(imports.itertuples())}
newtop=new.head(5); cy={int(r.player_id):135+j*85 for j,r in enumerate(newtop.itertuples())}
ed=pd.read_csv(P/'transfer_edges.csv')
for r in imports.itertuples():
    c+=line(130,305,420,ay[r.player_id],TEAL,2+r.minutes/60)
    ly=(305+ay[r.player_id])/2-15
    c+=f'<rect x="228" y="{ly-17}" width="58" height="24" fill="white"/>'+text(235,ly,f'{r.minutes:.0f}분',14,GRAY)
for r in ed[ed.candidate.isin(cy)].itertuples():
    c+=line(437,ay[r.anchor],750,cy[r.candidate],'#8ca2c0',1+6*r.weight,'6 5')
c+=f'<circle cx="130" cy="305" r="21" fill="{INK}"/>'+text(35,350,'Chris McCullough',17,weight=700)
for r in imports.itertuples():
    labely=ay[r.player_id]+38 if r.name=='Lasannah Kromah' else ay[r.player_id]-24
    c+=f'<circle cx="420" cy="{ay[r.player_id]}" r="14" fill="{TEAL}"/>'+text(315,labely,r.name,16,weight=700)
for r in newtop.itertuples():
    c+=f'<circle cx="750" cy="{cy[r.player_id]}" r="9" fill="{BLUE}"/>'+text(770,cy[r.player_id]+5,r.name,16,weight=700)
c+=text(35,552,'관측 외국인 기준점은 3명뿐. 후보 순위는 유형 유사성에 기반한 탐색 목록이다.',15,GRAY)
network=save('04_transfer_graph',svg(c,585,'관측 공출전 관계와 후보 유형 전이의 차이'))

def table(df,columns,formats=None):
    h='<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+E(label)+'</th>' for key,label in columns)+'</tr></thead><tbody>'
    for _,r in df.iterrows():
        h+='<tr>'+''.join('<td>'+E(formats[key](r[key]) if formats and key in formats else str(r[key]))+'</td>' for key,label in columns)+'</tr>'
    return h+'</tbody></table></div>'
ot=table(imports,[('name','실제 동료'),('minutes','공출전 분'),('net36','팀 득실/36'),('mcc_points36','맥컬러 득점/36'),('mcc_TS','맥컬러 TS'),('assisted_share','도움받은 야투 비중')],{k:(lambda v:f'{v:.1f}') for k in ['minutes','net36','mcc_points36']}|{k:(lambda v:f'{v:.1%}') for k in ['mcc_TS','assisted_share']})
mt=table(metrics,[('split','검증'),('model','모델'),('net_rmse36','팀 득실 RMSE'),('mcc_rmse36','개인 득점 RMSE')],{k:(lambda v:f'{v:.2f}') for k in ['net_rmse36','mcc_rmse36']})
css='''*{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:#172739;font:16px/1.75 "Malgun Gothic",Arial,sans-serif}main{max-width:1120px;margin:auto;padding:42px 28px 80px}header{padding:24px 0 32px;border-bottom:3px solid #172739}.eyebrow{color:#087f78;font-size:13px;letter-spacing:2px;font-weight:700}h1{font-size:40px;line-height:1.35;letter-spacing:-1.5px;margin:16px 0}h2{font-size:25px;line-height:1.4;margin:0 0 18px}h3{font-size:19px;margin:24px 0 10px}p{margin:12px 0}.muted,figcaption{color:#627084;font-size:14px}.lead{font-size:19px;max-width:900px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:24px 0}.card{background:white;border:1px solid #dce3e9;border-radius:8px;padding:22px}.card strong{font-size:26px;display:block}.card span{font-size:14px;color:#627084}.note{border-left:4px solid #ad5720;background:#fff3e8;padding:18px 22px;margin:22px 0}.good{border-color:#087f78;background:#eef8f6}section{background:white;border:1px solid #dce3e9;border-radius:8px;padding:30px;margin:24px 0}figure{margin:24px 0}svg{display:block;width:100%;height:auto}figcaption{margin-top:10px}.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;white-space:nowrap}th{text-align:left;background:#eef2f6;padding:11px}td{padding:11px;border-bottom:1px solid #e2e7ed}a{color:#225ac7;text-underline-offset:3px}nav{display:flex;gap:18px;flex-wrap:wrap;margin-top:24px}label{display:inline-block;margin:8px 16px 8px 0}input,select{font:inherit;padding:8px 12px;max-width:100%;border:1px solid #aebaca;border-radius:5px}code{font-size:13px;overflow-wrap:anywhere}details{margin-top:18px;border-top:1px solid #ddd;padding:15px 0}summary{cursor:pointer;font-weight:bold}li{margin:9px 0}.tag{color:#ad5720;font-size:13px;font-weight:bold}@media(max-width:640px){main{padding:20px 14px}h1{font-size:28px}.lead{font-size:17px}.cards{grid-template-columns:1fr;gap:10px}.card{padding:16px}.card strong{font-size:23px}section{padding:20px 15px}.figure-scroll{overflow-x:auto}.figure-scroll svg{min-width:680px}h2{font-size:22px}nav{gap:12px}}@media print{body{background:white}main{padding:0}section{break-inside:avoid;border:none}nav,.controls{display:none}.figure-scroll{overflow:visible}.figure-scroll svg{min-width:0}}'''
html=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>맥컬러 파트너 분석 | GNN 검증과 그래프 전이</title><style>{css}</style></head><body><main>
<header><div class="eyebrow">SPORTS ANALYTICS · TPBL 2025–26 · 2026.10.04</div><h1>맥컬러에게 맞는 외국인 파트너,<br>데이터는 어디까지 말해 주는가?</h1><p class="lead"><b>팀 성과는 디알로형 빅맨, 개인 득점은 크로마형 플레이메이커가 탐색 가설입니다.</b> GNN은 실제 학습했으나 기준 모델을 이기지 못했습니다. 추천은 관측 공출전 그래프와 유형 전이로 제한합니다.</p><nav><a href="#verdict">핵심 결과</a><a href="#model">GNN 검증</a><a href="#observed">실제 동료</a><a href="#candidates">새 후보</a><a href="#method">재현 방법</a></nav></header>
<div class="cards"><div class="card"><strong>24경기 · 401구간</strong><span>분석 단위는 스틴트, 독립 표본은 경기</span></div><div class="card"><strong>617.8분</strong><span>정규시즌 맥컬러 출전, 30초 이상·가비지 제외</span></div><div class="card"><strong>3명 → 32명</strong><span>실제 외국인 동료 → 새 외국인 후보</span></div></div>
<div class="note"><b>삼성 썬더스 적용 범위</b><p>분석 원천은 삼성 경기가 아니라 TPBL 타오위안 레오파즈의 맥컬러(player_id 10860) 기록입니다. KBL은 외국인 2명 보유·1명 출전이므로 여기서 측정한 동시 출전 궁합을 삼성의 외국인 2인 조합 성과로 해석할 수 없습니다. 교대 운용·영입 결정에는 삼성 국내 선수와 맥컬러 비출전 구간 자료가 추가로 필요합니다. <a href="https://pegasus.kbl.or.kr/rule/operation">KBL 공식 규정</a> (2026-10-04 확인)</p></div>
<section id="verdict"><h2>01 · 확정 1위보다, 두 가지 역할 가설</h2><p><b>팀 득실을 기준으로 하면 Cheick Diallo가 관측 1위입니다.</b> 126.6분 공출전에서 팀 득실은 +9.38점/36분, 축소 후 +6.15입니다. 디알로는 리바운드·골밑 마무리에 강한 빅맨 유형으로 볼 수 있습니다. 다만 디알로–밀러 축소 성과 차이의 95% 재표집 구간은 −5.76~+11.80으로, 우월한 궁합이 확인된 것은 아닙니다.</p><p><b>맥컬러 개인 득점을 기준으로 하면 Lasannah Kromah가 관측 1위입니다.</b> 함께 뛸 때 맥컬러 득점은 23.04점/36분, TS는 55.7%, 어시스트를 받은 야투 비중은 62.9%입니다. 높은 어시스트 생산량의 볼핸들러·플레이메이커 유형이 개인 공격을 돕는다는 가설입니다. 팀 득실은 −0.85점/36분으로 목표 간 결과가 다릅니다.</p><p><b>새 후보는 Jordy Tshimanga를 먼저 확인할 수 있습니다.</b> 팀 성과 전이 점수가 새 후보 중 가장 높지만 정규시즌 표본은 226.6분뿐입니다. Brandon Gilbeck, Jason Washburn, Marko Todorovic도 함께 비교할 후보입니다. 이 순위는 실제 함께 뛰어본 결과나 이적 가능성 평가가 아닙니다.</p></section>
<section id="model"><h2>02 · GNN을 학습했고, 검증에서 채택하지 않았다</h2><p>선수 10명으로 구성한 스틴트 그래프에서 동료·상대 메시지를 따로 집계하는 관계형 GNN을 구현했습니다. 같은 경기의 구간은 항상 같은 검증 집합에 배정했습니다. 평가 전 고정한 설정을 사용했으며, 보고된 검증 오차를 보고 하이퍼파라미터를 조정하지 않았습니다.</p><figure><div class="figure-scroll">{validation}</div><figcaption>단순 평균은 학습 경기의 시간 가중 평균. Ridge는 선수 특성·시작 맥락의 선형 모델. 엣지 제거 NN은 같은 신경망에서 이웃 메시지를 0으로 만든 비교 모델입니다.</figcaption></figure>{mt}<div class="note"><b>판정: 이번 GNN의 추천을 믿을 검증 근거가 없습니다.</b> 경기별 교차검증에서 GNN−Ridge의 평균제곱오차 차이는 +1,388.60, 경기 부트스트랩 95% 구간은 +972.81~+1,841.60입니다. 단위는 (점/36분)²이며 양수는 GNN이 나쁨을 뜻합니다. 모델 간 차이에 대한 조건부 비교이지 모든 GNN 구조에 대한 결론은 아닙니다.</div><details><summary>모델 구조와 검증을 자세히 보기</summary><p><code>H = tanh(X Wself + Ateam X Wteam + Aopp X Wopp + b)</code></p><p>각 노드는 자신을 제외한 동료 4명, 상대 5명에게서 평균 메시지를 받습니다. 19개 입력 특성, 은닉 8차원, 1층 메시지 전달 후 맥컬러·동료 평균·상대 평균 임베딩과 시작 맥락을 연결해 두 결과를 회귀합니다. 전체 522개 학습 파라미터입니다. NumPy로 역전파와 Adam을 직접 구현했고 수치 미분 및 노드 순서 불변성을 검증했습니다.</p><p>목표는 팀 득실/36분, 맥컬러 득점/36분입니다. 지속시간 가중 MSE, 목표 스케일 40·25, 학습률 0.008, 220 epoch, L2 0.02, 검증별 seed 3개 평균을 사용했습니다. Ridge는 정규화 가중 손실에서 λ=1입니다. 포제션이 0인 구간의 분모 문제를 줄이기 위해 주 목표를 시간당 비율로 정의했습니다. 짧은 구간 비율은 변동성이 커 RMSE의 절대값도 큽니다.</p><p>그룹 교차검증은 24경기를 5개 묶음으로 분할한 후 검증 경기의 박스스코어를 선수 특성 계산에서 제외합니다. 다른 날짜의 미래 통계는 포함될 수 있는 <b>시즌 내 회고 검증</b>입니다. 별도로 마지막 8경기는 이전 16경기로 학습하고, 선수 특성도 해당 8경기 시작일 이전의 리그 기록만 사용한 시간순 검증을 수행했습니다. 테스트 라인업과 시작 점수 차를 알고 있는 조건부 예측이며 경기 전 예측은 아닙니다.</p><p>시즌 합계 z 특성, 전체 시즌 공출전 엣지, stint_nodes의 결과 스탯, 득실·포제션·최종 점수는 입력에 쓰지 않았습니다. 경기 종료 후 알 수 있는 구간 길이는 결과율 계산과 손실 가중치에만 사용했습니다. 선수 특성의 축소 사전값·표준화도 허용된 박스스코어로 재계산했습니다.</p></details></section>
<section id="observed"><h2>03 · 실제 파트너 성과와 목표의 차이</h2><figure><div class="figure-scroll">{intervals}</div><figcaption>24경기를 단위로 2,000회 복원추출해 산출한 분위수 구간. 120분 사전값은 분석 표본 전체의 평균 득실 +2.74점/36분이며, 매 재표집에서 다시 계산했습니다.</figcaption></figure>{ot}<figure><div class="figure-scroll">{trade}</div><figcaption>TS = 득점 ÷ [2 × (야투 시도 + 0.44 × 자유투 시도)]. 도움받은 야투 비중은 맥컬러 야투 성공 중 어시스트가 연결된 비중이며, 해당 동료가 직접 제공한 어시스트만 의미하지 않습니다.</figcaption></figure><p>30초 미만·가비지 구간까지 포함한 680.3분에서도 외국인 파트너의 팀 득실 순서는 디알로 → 밀러 → 크로마입니다. 그러나 관측 순서가 유지되는 것과 독립적인 파트너 효과를 입증하는 것은 다릅니다. 국내 동료는 함께 출전하는 경우가 겹치므로 단순 순위를 개인 기여도로 읽으면 안 됩니다.</p></section>
<section id="candidates"><h2>04 · 새로운 외국인 선수는 ‘검증 후보’로</h2><p>정규시즌 200분 이상 출전한 외국인 35명(맥컬러 제외)을 대상으로, 실제 파트너 3명과의 유형 유사성 그래프를 만들었습니다. 이 중 기존 동료를 제외한 새 후보는 32명입니다. 추천 범위는 파일에 있는 TPBL 선수이며 전 세계 외국인 선수 전체가 아닙니다.</p><figure><div class="figure-scroll">{network}</div><figcaption>노드 위치는 집단을 구분하기 위한 고정 배치입니다. 공간 거리는 선수 간 유사도를 나타내지 않습니다. 점선 굵기만 정규화된 유형 유사도 가중치를 나타냅니다.</figcaption></figure><div class="note good"><b>읽는 법</b><p>‘팀 전이 점수’는 비슷한 실제 파트너들의 축소 득실을 가중 평균한 값입니다. 후보가 합류했을 때의 예상 순득점으로 해석하지 마세요. 95% 범위는 기준점 3명의 경기 표본 변동만 반영하며, 후보 특성 추정 오차·이적 후 환경 변화는 반영하지 않습니다.</p></div>
<div class="controls"><label for="criterion">정렬 기준 <select id="criterion"><option value="team">팀 성과 유형 전이</option><option value="individual">맥컬러 개인 득점 유형 전이</option></select></label><label for="query">선수 검색 <input id="query" type="search" placeholder="영문 선수명"></label><label><input type="checkbox" id="existing"> 기존 동료 포함</label></div><p id="count" class="muted" aria-live="polite"></p><div class="tablewrap"><table><thead><tr><th>순서</th><th>선수</th><th>시즌 분</th><th>팀 전이 점수</th><th>팀 점수 95% 범위</th><th>개인 득점 전이</th><th>유사 기준점</th><th>설정별 순위 범위*</th></tr></thead><tbody id="candidateRows"></tbody></table></div><noscript>전체 후보는 <a href="candidate_transfer.csv">CSV</a>에서 확인할 수 있습니다. 새 후보 상위: Jordy Tshimanga, Brandon Gilbeck, Jason Washburn, Marko Todorovic.</noscript><p class="muted">* 사전 표본 60·120·240분 × 유사도 폭 0.5·1·2의 9개 설정에서, 기존 동료를 포함한 35명 중 팀 점수 순위 범위. 화면 정렬은 새 후보만 선택할 수 있어 표시 순서와 다를 수 있습니다.</p><p>티시망가는 전체 35명 중 설정별 2~4위이나 작은 시즌 표본을 갖고 있습니다. 길벡은 1~9위로 설정에 더 민감합니다. 높은 유사도는 실제 궁합을 보증하지 않으며, 순위 차이는 사전 스카우팅의 출발점입니다.</p></section>
<section id="method"><h2>05 · 분석 방법, 데이터 한계, 재현</h2><ol><li><b>데이터:</b> <code>25-26-TPBL-McC-main/GNN/output_data/gnn_dataset</code>의 스틴트·선수 메타데이터와 <code>GNN/input_data</code>의 경기별 박스스코어를 사용했습니다. 팀원의 HTML은 분석 구성 참고용이며 그 안의 집계치를 복사하지 않았습니다.</li><li><b>필터:</b> 정규시즌·맥컬러 출전·유효한 5대5·선수 ID 확인·30초 이상·가비지 제외. 526구간 680.3분에서 401구간 617.8분으로 축소했습니다. 프리시즌·플레이오프는 주분석에서 제외했습니다.</li><li><b>품질:</b> 제공된 PBP 검증 보고서는 42경기 점수와 1,118 선수-경기 기록이 일치한다고 보고합니다. 다만 라인업 밖 이벤트 87개, 시계 보간 이벤트 11개가 있어 정확한 시점 귀속은 완벽하지 않습니다. 본 분석은 ID 고유성·10명 중복 없음·득실 합산·그룹 분리·수치 미분을 별도로 점검했으며 원 API를 다시 수집하지 않았습니다.</li><li><b>그래프:</b> 맥컬러–동료 엣지는 실제 공출전 분입니다. 관측 팀 득실을 전체 평균으로 120분 축소한 뒤, 후보–기준 동료 간 특성 거리에서 가우시안 엣지 가중치를 만듭니다. 특성은 36분당 3점 시도·공격/수비 리바운드·어시스트·블록·턴오버 및 축소한 3점 성공률·TS입니다. 표준화 유클리드 거리의 제곱 평균, 폭 1을 사용합니다. 그래프 전이의 가중치는 학습된 궁합 계수가 아닙니다.</li><li><b>불확실성:</b> 경기 단위 부트스트랩 2,000회. 같은 경기 구간을 독립 표본으로 취급하지 않습니다. 기준 동료 3명만으로 생긴 외삽 순위를 검증할 독립적인 실제 파트너 라벨은 없습니다. 원시 온/오프 및 축소 성과에는 상대·감독 기용·다른 동료의 교란이 남습니다.</li><li><b>다음 자료:</b> 여러 팀·여러 시즌의 전체 PBP, 동일 외국인의 팀 이동 전후 기록, 삼성의 국내 선수별 구간과 맥컬러 비출전 라인업 성과를 확보해야 합니다. 이후 선수·시즌 외부 검증과 교대 외국인 모델을 별도로 평가해야 합니다.</li></ol><h3>재현 파일</h3><p><a href="README.md">한국어 분석 설명</a> · <a href="analyze.py">분석 코드</a> · <a href="build_report.py">보고서 생성 코드</a> · <a href="audit.json">데이터 지문·실행 설정</a> · <a href="model_metrics.csv">모델 지표</a> · <a href="observed_partners.csv">관측 동료</a> · <a href="candidate_transfer.csv">전체 후보</a> · <a href="gnn_hypotheses.csv">채택하지 않은 GNN 가상 교체 결과</a></p><p class="muted">GNN 가상 교체 결과는 검증 실패에 따라 추천 근거에서 제외했습니다. 파일의 min/max는 5개 경기 재표집 모델의 범위이며 95% 신뢰구간이 아닙니다.</p><h3>추가 GNN 시각화 9종</h3><p><a href="figures_gnn/index.html">그림 갤러리</a> · <a href="figures_gnn/00_gnn_overview.png">전체 미리보기 PNG</a> · <a href="mcc_gnn_visualizations_expanded.zip">PNG·SVG 묶음 ZIP</a></p><p class="muted">구조도, 라인업 메시지 관계망, 실제값–예측값, 경기별 오차, 잔차, 임베딩, 특성 민감도, 가상 교체, 학습 곡선. 2026-10-10 추가.</p><h3>원본 벡터 그림</h3><p><a href="figures/01_model_validation.svg">모델 검증</a> · <a href="figures/02_observed_partners.svg">관측 동료·불확실성</a> · <a href="figures/03_objective_tradeoff.svg">목표 지표 비교</a> · <a href="figures/04_transfer_graph.svg">전이 그래프</a></p><p class="muted">방법 참고: <a href="https://arxiv.org/abs/1703.06103">Schlichtkrull et al., Modeling Relational Data with Graph Convolutional Networks</a>. 여기서는 이 논문의 관계별 메시지 전달 아이디어를 사용한 소형 회귀 모델을 구현했으며 원 논문의 벤치마크 재현은 아닙니다.</p></section><footer class="muted">생성일 2026-10-04 · seed 20261004 · 데이터 구간 {A['game_dates'][0]}~{A['game_dates'][1]} · 온라인 서비스 없이 열리는 독립 HTML</footer></main>
<script id="data" type="application/json">{trans.to_json(orient='records',force_ascii=False).replace('</','<\\/')}</script>
<script>
const data=JSON.parse(document.getElementById('data').textContent);const q=document.getElementById('query'),criterion=document.getElementById('criterion'),existing=document.getElementById('existing');const params=new URLSearchParams(location.search);q.value=params.get('q')||'';criterion.value=params.get('criterion')==='individual'?'individual':'team';existing.checked=params.get('existing')==='1';
function render(){{let rows=data.filter(r=>(existing.checked||!r.observed_partner)&&r.name.toLowerCase().includes(q.value.toLowerCase()));let key=criterion.value==='team'?'transfer_score':'mcc_points_transfer';rows.sort((a,b)=>b[key]-a[key]);let body=document.getElementById('candidateRows');body.replaceChildren();rows.forEach((r,i)=>{{let tr=document.createElement('tr');[i+1,r.name+(r.observed_partner?' (기존)':''),r.minutes.toFixed(1),r.transfer_score.toFixed(2),'['+r.lo.toFixed(2)+', '+r.hi.toFixed(2)+']',r.mcc_points_transfer.toFixed(2),r.nearest_anchor,r.rank_min+'~'+r.rank_max].forEach(v=>{{let td=document.createElement('td');td.textContent=v;tr.append(td)}});body.append(tr)}});document.getElementById('count').textContent=rows.length+'명 표시 · 전이 점수는 탐색 지표이며 예측 성과가 아닙니다.';let p=new URLSearchParams();if(q.value)p.set('q',q.value);if(criterion.value!=='team')p.set('criterion',criterion.value);if(existing.checked)p.set('existing','1');try{{history.replaceState(null,'',location.pathname+(p.size?'?'+p.toString():'')+location.hash)}}catch(e){{}}}}
q.addEventListener('input',render);criterion.addEventListener('change',render);existing.addEventListener('change',render);render();
</script></body></html>'''
(P/'mcc_gnn_report.html').write_text(html,encoding='utf-8')
print('Report and four SVG figures written.')
