"""Nine publication-size GNN diagnostics, using saved analysis and NumPy model.
Reproduces original folds to measure permutation sensitivity; never tunes on tests.
"""
from pathlib import Path
import os,sys,json,zipfile
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'_viz_packages'))
os.environ.setdefault('MPLCONFIGDIR',str(P/'_mpl_cache'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch,Patch
from matplotlib.lines import Line2D
from matplotlib import font_manager
from PIL import Image,ImageOps,ImageDraw,ImageFont
import analyze as a

OUT=P/'figures_gnn';OUT.mkdir(exist_ok=True)
FONT=Path('C:/Windows/Fonts/malgun.ttf')
font_manager.fontManager.addfont(str(FONT))
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':12,'axes.unicode_minus':False,
 'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#33465c',
 'text.color':'#172739','axes.titleweight':'bold','figure.facecolor':'white',
 'savefig.facecolor':'white','svg.fonttype':'none'})
BLUE='#225ac7';TEAL='#087f78';ORANGE='#ac5524';GRAY='#6c7b8e';LIGHT='#e4e9f0';INK='#172739'
files=[]; checks={}
pred=pd.read_csv(P/'predictions.csv',dtype={'game_id':str})
cv=pred[pred.split=='group_cv']
def panel(title,subtitle,nrows=1,ncols=1,size=(13.5,7.5)):
    fig,axs=plt.subplots(nrows,ncols,figsize=size,squeeze=False)
    fig.suptitle(title,x=.055,y=.96,ha='left',fontsize=22,fontweight='bold')
    fig.text(.055,.90,subtitle,ha='left',fontsize=11,color=GRAY)
    fig.subplots_adjust(left=.09,right=.96,top=.81,bottom=.18,wspace=.28,hspace=.4)
    return fig,axs
def finish(fig,name,caption):
    fig.text(.055,.055,caption,fontsize=10,color=GRAY,ha='left',va='bottom',linespacing=1.6)
    for ext in ['png','svg']:fig.savefig(OUT/f'{name}.{ext}',dpi=220)
    files.append({'file':name,'title':fig._suptitle.get_text(),'caption':caption})
    plt.close(fig)
def grids(ax,which='y'):
    ax.grid(axis=which,color=LIGHT,zorder=0);ax.set_axisbelow(True)

# 05: architecture mirrors the implemented formula, dimensions and readout.
fig,axs=panel('GNN은 선수의 특성과 관계를 어떻게 결합하는가?',
 '구현된 1층 관계형 GNN · 노드 10명 · 특성 19개 · 은닉 8차원 · 파라미터 522개')
ax=axs[0,0];ax.set_xlim(-3,103);ax.set_ylim(0,100);ax.axis('off')
def box(x,y,w,h,label,color=BLUE):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.5,rounding_size=2',ec=color,fc='white',lw=1.8))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=12,color=color,linespacing=1.7)
def arrow(x1,y1,x2,y2,color=GRAY):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=15,color=color,lw=1.5))
box(0,34,17,29,'선수 특성 X\n10 × 19\n박스스코어·신체')
for y,label in [(72,'자기 특성\nX Wself'),(40,'동료 4명 평균\nAteam X Wteam'),(8,'상대 5명 평균\nAopp X Wopp')]:
    box(24,y,23,21,label,TEAL if y==40 else BLUE);arrow(17,49,24,y+10)
    arrow(47,y+10,55,49)
box(55,34,17,29,'합산 + tanh\n노드 표현 H\n10 × 8',TEAL)
arrow(72,49,79,49);box(79,32,21,33,'역할별 읽기\n맥컬러 + 동료 + 상대\n+ 시작 맥락 4개')
ax.text(89,16,'팀 득실 / 36분\n맥컬러 득점 / 36분',ha='center',fontsize=12,fontweight='bold')
arrow(89,32,89,24)
finish(fig,'05_gnn_architecture','관계별 가중치는 학습하며, 동료·상대 집계는 각각 1/4·1/5의 고정 평균입니다.\n출처: analyze.py의 GNN.forward·design·POOL. 구조도는 예측 성능을 뜻하지 않습니다.')

# 06: actual observed lineup ego-message graph, relation weight shown faithfully.
idx=int(np.argmax(a.s.duration_sec.values)); r=a.s.iloc[idx]; lineup=a.SIDS[idx];m=a.MID[idx]
fig,axs=panel('실제 라인업에서 맥컬러가 받는 두 종류의 메시지',
 f'관측 예시: game {r.game_id} · {r.stint_id} · {r.duration_sec/60:.2f}분 · 맥컬러 중심 수신 관계')
ax=axs[0,0];ax.axis('off');ax.set_xlim(-1.6,1.65);ax.set_ylim(-1.35,1.3)
coords={int(lineup[m]):np.array([0,0])}
mates=[int(v) for j,v in enumerate(lineup[:5]) if j!=m]
for j,v in enumerate(mates):coords[v]=np.array([-.95,1.02-j*.68])
for j,v in enumerate(lineup[5:]):coords[int(v)]=np.array([.95,1.02-j*.51])
for v in mates+list(lineup[5:]):
    xy=coords[int(v)];is_mate=int(v) in mates;c=TEAL if is_mate else BLUE
    ax.annotate('',xy=(xy*.12),xytext=xy*.90,arrowprops={'arrowstyle':'-|>','lw':2,'color':c,'linestyle':'-' if is_mate else '--','alpha':.72})
    ax.scatter(*xy,s=380,c=c,zorder=3,edgecolors='white',linewidths=2)
    ax.text(xy[0]+(-.10 if is_mate else .10),xy[1],a.name[a.ids[int(v)]],ha='right' if is_mate else 'left',va='center',fontsize=10.5)
ax.scatter(0,0,s=1100,c=INK,zorder=5);ax.text(0,-.24,'Chris McCullough',ha='center',fontweight='bold',fontsize=13,bbox={'facecolor':'white','edgecolor':'none','pad':2},zorder=6)
ax.text(-.95,1.21,'동료 평균 · 각 0.25',ha='center',color=TEAL,fontweight='bold')
ax.text(.95,1.21,'상대 평균 · 각 0.20',ha='center',color=BLUE,fontweight='bold')
finish(fig,'06_lineup_message_graph','화살표는 메시지의 수신 방향이며 어시스트·패스 기록이 아닙니다. 실제 모델에서는 모든 노드가 메시지를 받습니다.\n그림은 맥컬러의 수신 엣지만 표시합니다. 노드 위치는 도식적 배치입니다.')

# 07: out-of-fold predictions, no outcome clipping or jitter.
fig,axs=panel('검증 구간에서 실제값과 예측값은 얼마나 일치하는가?',
 '경기별 5분할의 GNN 검증 예측 401개 · 점 크기 = 구간 지속시간 · 점선 = 완벽한 예측',ncols=2)
g=cv[cv.model=='GNN']
for ax,target,title in zip(axs[0],['net','mcc'],['팀 득실 / 36분','맥컬러 득점 / 36분']):
    x=g[f'{target}_actual'].values;y=g[f'{target}_pred'].values
    lo=min(x.min(),y.min());hi=max(x.max(),y.max());pad=(hi-lo)*.08
    ax.scatter(x,y,s=12+g.weight.values*16,c=BLUE,alpha=.45,edgecolors='none')
    ax.plot([lo-pad,hi+pad],[lo-pad,hi+pad],ls='--',c=GRAY,lw=1)
    ax.set(xlim=(lo-pad,hi+pad),ylim=(lo-pad,hi+pad),xlabel='실제값',ylabel='GNN 예측값',title=title)
    ax.set_aspect('equal',adjustable='box');grids(ax,'both')
    rmse=a.metric(x[:,None],y[:,None],g.weight.values)[0]
    ax.text(.04,.95,f'시간 가중 RMSE {rmse:.2f}',transform=ax.transAxes,va='top',fontsize=11,bbox={'facecolor':'white','edgecolor':LIGHT,'pad':6})
finish(fig,'07_actual_vs_predicted','원시 구간 결과를 36분으로 환산해 큰 값이 생길 수 있습니다. 축을 잘라내지 않았습니다.\n출처: predictions.csv, split=group_cv, model=GNN. 각 구간은 해당 경기를 제외하고 학습한 모델의 예측입니다.')

# 08: date-ordered game errors.
rows=[]
for (gid,model),v in cv.groupby(['game_id','model']):
    rows.append({'game_id':gid,'date':a.dates[gid],'model':model,'rmse':a.metric(v[['net_actual']].values,v[['net_pred']].values,v.weight)[0]})
gm=pd.DataFrame(rows);gs=gm[['game_id','date']].drop_duplicates().sort_values('date');order=gs.game_id.tolist()
fig,axs=panel('경기별로 봐도 GNN의 오차가 대체로 더 크다',
 '팀 득실/36분의 경기별 시간 가중 RMSE · 같은 경기 안에서 모델을 비교 · 낮을수록 좋음',size=(14.5,7.5))
ax=axs[0,0]
for mod,c,marker in [('Ridge',TEAL,'s'),('GNN',ORANGE,'o')]:
    y=gm[gm.model==mod].set_index('game_id').loc[order].rmse.values
    ax.plot(range(len(y)),y,color=c,marker=marker,lw=1.8,ms=5,label=mod)
ax.set_xticks(range(len(order)),[d[5:] for d in gs.date],rotation=55,ha='right',fontsize=9)
ax.set(ylabel='경기별 RMSE',xlabel='경기일 (월–일, 날짜순)');ax.legend(frameon=False);grids(ax)
fig.subplots_adjust(bottom=.26)
pd.DataFrame(rows).to_csv(OUT/'game_rmse.csv',index=False)
finish(fig,'08_game_error_timeline','날짜 순서로 그렸지만 이 그림의 예측은 경기 그룹 교차검증입니다. 시간순 미래 예측 그래프가 아닙니다.\n출처: predictions.csv. 전체 경기의 RMSE 단순 평균과 전체 구간의 시간 가중 RMSE는 다릅니다.')

# 09: duration-weighted residual distributions, all values retained.
fig,axs=panel('오차 분포는 어느 쪽으로 얼마나 퍼져 있는가?',
 '잔차 = 예측 - 실제 · 지속시간으로 가중한 분포 · 세로 점선 = 오차 0',ncols=2)
for ax,target,title in zip(axs[0],['net','mcc'],['팀 득실 잔차','맥컬러 득점 잔차']):
    residuals=[(cv[cv.model==mod][f'{target}_pred']-cv[cv.model==mod][f'{target}_actual']).values for mod in ['GNN','Ridge']]
    bins=np.linspace(min(v.min() for v in residuals),max(v.max() for v in residuals),24)
    for mod,c,v in zip(['GNN','Ridge'],[ORANGE,TEAL],residuals):
        vv=cv[cv.model==mod];ww=vv.weight.values/vv.weight.sum()*100
        ax.hist(v,bins=bins,weights=ww,histtype='step',lw=2,label=mod,color=c)
    ax.axvline(0,color=GRAY,ls='--',lw=1);ax.set(title=title,xlabel='예측 오차 (점/36분)',ylabel='전체 출전시간 중 비중 (%)');ax.legend(frameon=False);grids(ax)
finish(fig,'09_residual_distribution','두 모델에 동일한 구간·분모·히스토그램 경계를 사용했습니다. 전체 값이 포함되어 있습니다.\n출처: predictions.csv의 경기 그룹 검증. 양의 잔차는 실제값보다 높게 예측했다는 뜻입니다.')

# 10: contextual hidden states from one explicitly identified saved model.
state=np.load(P/'final_feature_state.npz');x=state['x'];assert np.allclose(x,a.features()[0])
model=a.GNN(x.shape[1]*3);model.p={k:v.copy() for k,v in np.load(P/'gnn_model_0.npz').items()}
_,(h,q)=model.forward(a.design(x),a.POOL,a.CTX)
total=np.zeros((len(a.nodes),8));expo=np.zeros(len(a.nodes))
for j in range(10):
    np.add.at(total,a.SIDS[:,j],h[:,j,:]*a.W[:,None]);np.add.at(expo,a.SIDS[:,j],a.W)
seen=np.flatnonzero(expo>=30);hidden=total[seen]/expo[seen,None]
center=hidden.mean(0);u,sv,vt=np.linalg.svd(hidden-center,full_matrices=False);xy=(hidden-center)@vt[:2].T
var=sv[:2]**2/(sv**2).sum()
embed=pd.DataFrame({'player_id':a.nodes.iloc[seen].player_id.values,'name':[a.name[a.ids[i]] for i in seen],'minutes_in_context':expo[seen],'PC1':xy[:,0],'PC2':xy[:,1]})
embed.to_csv(OUT/'context_embeddings.csv',index=False)
fig,axs=panel('GNN 내부 선수 표현을 2차원으로 펼쳐 보기',
 f'저장 모델 0의 은닉 8차원 → PCA 2차원 · 표시 {len(seen)}명 · 해당 라인업 관측 30분 이상',size=(13.5,8.5))
ax=axs[0,0];imported=a.nodes.iloc[seen].is_imported.values==1
for mask,c,label,mark in [(~imported,'#a6b0bd','국내 선수','o'),(imported,BLUE,'외국인 선수','^')]:
    ax.scatter(xy[mask,0],xy[mask,1],c=c,marker=mark,s=45,alpha=.62,label=label)
highlight={'10860':(12,18),'10861':(12,18),'16':(12,-26),'68':(12,18),'10868':(-12,-26),'106':(12,18),'34':(12,-26),'8889':(-12,18)}
for pid,offset in highlight.items():
    if pid not in embed.player_id.values:continue
    e=embed[embed.player_id==pid].iloc[0];color=ORANGE if pid=='10860' else TEAL
    ax.scatter(e.PC1,e.PC2,s=90,c=color,zorder=4,edgecolors='white')
    ax.annotate(e['name'],(e.PC1,e.PC2),xytext=offset,textcoords='offset points',fontsize=10,fontweight='bold',ha='right' if offset[0]<0 else 'left',arrowprops={'arrowstyle':'-','color':GRAY,'lw':.7},bbox={'facecolor':'white','edgecolor':'none','alpha':.85,'pad':2})
ax.set(xlabel=f'PC1 ({var[0]:.1%} 분산 설명)',ylabel=f'PC2 ({var[1]:.1%} 분산 설명)');ax.margins(.23);ax.legend(frameon=False,loc='upper left');grids(ax,'both')
finish(fig,'10_context_embedding_pca','전체 분석 표본으로 학습한 1개 모델의 회고 표현이며, 경기 상황·동료·상대의 영향이 함께 반영됩니다.\n가까운 점은 해당 표현이 비슷하다는 뜻입니다. 파트너 궁합·군집·외부 예측력이 검증됐다는 뜻은 아닙니다.')

# 11: replay exact CV models, then perturb one feature over all league nodes.
print('Replaying folds for feature sensitivity...',flush=True)
manifest=pd.read_csv(P/'split_manifest.csv',dtype={'game_id':str});REPS=5
changes=np.zeros((REPS,len(a.FEATURES)));denom=0
for fold in range(5):
    testg=manifest[(manifest.split=='group_cv')&(manifest.fold==fold)&(manifest.role=='test')].game_id.unique()
    te=np.flatnonzero(a.s.game_id.isin(testg));tr=np.flatnonzero(~a.s.game_id.isin(testg));xx,_,_=a.features(testg)
    zz=a.design(xx);models=[]
    for seed in range(3):models.append(a.GNN(zz.shape[-1],a.SEED+seed).fit(zz[tr],a.POOL[tr],a.CTX[tr],a.Y[tr]/a.SCALE,a.W[tr]))
    base=np.mean([m.forward(zz[te],a.POOL[te],a.CTX[te])[0] for m in models],axis=0)*a.SCALE
    saved=cv[(cv.model=='GNN')&(cv.fold==fold)].set_index('stint_id').loc[a.s.stint_id.iloc[te]].net_pred.values
    assert np.allclose(base[:,0],saved,rtol=1e-9,atol=1e-7)
    baseerr=(base[:,0]-a.Y[te,0])**2;denom+=a.W[te].sum()
    for rep in range(REPS):
        rng=np.random.default_rng(a.SEED+fold*100+rep)
        for j in range(len(a.FEATURES)):
            xp=xx.copy();xp[:,j]=xp[rng.permutation(len(xp)),j];zp=a.design(xp)[te]
            v=np.mean([m.forward(zp,a.POOL[te],a.CTX[te])[0] for m in models],axis=0)*a.SCALE
            changes[rep,j]+=np.sum(a.W[te]*((v[:,0]-a.Y[te,0])**2-baseerr))
changes/=denom
imp=pd.DataFrame({'feature':a.FEATURES,'mean_mse_change':changes.mean(0),'min':changes.min(0),'max':changes.max(0)}).sort_values('mean_mse_change',ascending=False)
imp.to_csv(OUT/'feature_sensitivity.csv',index=False)
labels={'points':'득점/36','FGA':'야투 시도/36','three_PA':'3점 시도/36','FTA':'자유투 시도/36','OREB':'공격 리바운드/36','DREB':'수비 리바운드/36','AST':'어시스트/36','STL':'스틸/36','BLK':'블록/36','TOV':'턴오버/36','three_pct':'3점 성공률','TS':'TS','height':'신장','is_imported':'외국인 여부'}
fig,axs=panel('어떤 입력을 섞었을 때 GNN의 검증 오차가 변하는가?',
 '선수 간 특성 1개씩 순열 · 팀 득실 MSE 변화 · 경기 그룹 검증 · 점=5회 평균, 선=5회 최소~최대',size=(13.5,9))
ax=axs[0,0];z=imp.sort_values('mean_mse_change');ys=np.arange(len(z));cs=[ORANGE if v<0 else BLUE for v in z.mean_mse_change]
ax.hlines(ys,z['min'],z['max'],color=cs,lw=2);ax.scatter(z.mean_mse_change,ys,c=cs,s=35,zorder=3)
ax.axvline(0,c=GRAY,ls='--');ax.set_yticks(ys,[labels.get(f,f.replace('pos_','포지션 ')) for f in z.feature],fontsize=10)
ax.set(xlabel='원래 검증 오차 대비 MSE 변화 ((점/36분)²)');grids(ax,'x')
fig.subplots_adjust(left=.22)
finish(fig,'11_feature_permutation_sensitivity','양수: 섞으면 오차 증가. 음수: 섞으면 오차 감소. 선은 신뢰구간이 아닌 5개 순열 실험 범위입니다.\n공선성·비현실적인 선수 특성 조합의 영향을 받을 수 있으며, 기여도·인과효과·유효한 추천 근거는 아닙니다.')
checks['original_cv_predictions_reproduced']=True

# 12: explicitly exploratory hypotheses already saved, includes entire ensemble range.
hyp=pd.read_csv(P/'gnn_hypotheses.csv');hh=hyp.head(10).iloc[::-1]
fig,axs=panel('가상 파트너 교체: 평균보다 넓은 모델 간 변동',
 '탐색 전용 · 기존 외국인 파트너를 후보로 바꾼 GNN 출력 변화 · 검증 성능 우위 없음',size=(13.5,8.5))
ax=axs[0,0];ys=np.arange(len(hh));ax.hlines(ys,hh.net_min,hh.net_max,color='#91a5c7',lw=3)
ax.scatter(hh.net_delta36,ys,c=ORANGE,s=50,zorder=4)
ax.set_yticks(ys,[f'{r.name}  (n={r.contexts})' for r in hh.itertuples()],fontsize=11)
ax.axvline(0,color=GRAY,ls='--');ax.set(xlabel='기존 라인업 대비 팀 득실 출력 변화 (점/36분)');grids(ax,'x');fig.subplots_adjust(left=.27)
finish(fig,'12_hypothetical_partner_ranges','점=5개 경기 재표집 모델 평균 · 선=5개 모델의 최소~최대. 95% 신뢰구간·예상 영입 효과가 아닙니다.\n후보별 평가 맥락 수(n)가 다릅니다. GNN 검증 실패로 이 순위를 추천 근거에 채택하지 않았습니다.')

# 13: exact original temporal training, logs for diagnosis only.
gids=sorted(a.s.game_id.unique(),key=lambda g:a.dates[g]);cut=a.dates[gids[-8]]
te=np.flatnonzero(a.s.game_id.isin(gids[-8:]));tr=np.flatnonzero(~a.s.game_id.isin(gids[-8:]))
xx,_,_=a.features(before=cut);zz=a.design(xx);models=[];hist=[]
for seed in range(3):
    mm=a.GNN(zz.shape[-1],a.SEED+seed);models.append(mm)
    mom={k:np.zeros_like(v) for k,v in mm.p.items()};vel={k:v.copy() for k,v in mom.items()};trajectory=[]
    for t in range(1,221):
        _,grad=mm.loss_grad(zz[tr],a.POOL[tr],a.CTX[tr],a.Y[tr]/a.SCALE,a.W[tr])
        for key in mm.p:
            mom[key]=.9*mom[key]+.1*grad[key];vel[key]=.999*vel[key]+.001*grad[key]**2
            mm.p[key]-=.008*(mom[key]/(1-.9**t))/(np.sqrt(vel[key]/(1-.999**t))+1e-8)
        if t==1 or t%5==0:trajectory.append(mm.forward(zz,a.POOL,a.CTX)[0]*a.SCALE)
    hist.append(trajectory)
history=np.mean(hist,axis=0);epochs=[1]+list(range(5,221,5));curve=[]
for ep,pp in zip(epochs,history):
    for role,ix in [('train',tr),('test',te)]:
        metric=a.metric(a.Y[ix],pp[ix],a.W[ix]);curve.append({'epoch':ep,'role':role,'net_rmse36':metric[0],'mcc_rmse36':metric[1]})
curve=pd.DataFrame(curve);curve.to_csv(OUT/'temporal_learning_curve.csv',index=False)
saved=pred[(pred.split=='temporal')&(pred.model=='GNN')].set_index('stint_id').loc[a.s.stint_id.iloc[te]]
assert np.allclose(history[-1][te,0],saved.net_pred,atol=1e-7)
checks['original_temporal_predictions_reproduced']=True
fig,axs=panel('학습이 진행돼도 테스트 오차가 함께 줄지는 않는다',
 '기존 시간순 실험을 그대로 재현 · 앞 16경기 학습 / 마지막 8경기 테스트 · 3개 seed 예측 평균',ncols=2)
for ax,key,title in zip(axs[0],['net_rmse36','mcc_rmse36'],['팀 득실 / 36분','맥컬러 득점 / 36분']):
    for role,c,label in [('train',TEAL,'학습'),('test',ORANGE,'테스트')]:
        v=curve[curve.role==role];ax.plot(v.epoch,v[key],c=c,lw=2,label=label)
    ax.set(title=title,xlabel='학습 epoch',ylabel='시간 가중 RMSE');ax.legend(frameon=False);grids(ax)
finish(fig,'13_temporal_learning_curves','사후 진단용 곡선입니다. 이 테스트 곡선으로 학습 중단 시점·설정을 선택하거나 성능을 다시 보고하지 않았습니다.\n최종 epoch 220 예측은 기존 predictions.csv의 시간순 GNN 예측과 수치적으로 일치합니다.')

# Text guides, portable image gallery, contact sheet and package.
guide=['# 추가 GNN 시각화 9종','',
 '생성일: 2026-10-10. 원래 분석·추천 결과는 변경하지 않았습니다.',
 'PNG는 220 dpi로 저장했으며 SVG도 함께 제공합니다.','',
 '임베딩·특성 민감도·가상 교체 결과는 탐색용입니다. GNN은 기존 검증에서 기준 모델보다 오차가 컸습니다.','']
for f in files:guide+=['## '+f['title'],'',f['file']+'.png','',f['caption'],'']
guide+=['## 재현','','기존 분석 산출물과 입력 데이터가 있는 상태에서 build_gnn_figures.py를 실행합니다.',
 'NumPy, pandas, Matplotlib, Pillow가 필요합니다. 프로젝트의 _viz_packages가 있으면 우선 사용합니다.',
 '추가 학습은 기존 설정을 재현해 특성 민감도·학습 곡선을 계산하는 용도입니다. 하이퍼파라미터 튜닝은 하지 않습니다.']
(OUT/'README.md').write_text('\n'.join(guide),encoding='utf-8')
cards=''.join(f'<article><h2>{f["title"]}</h2><a href="{f["file"]}.png"><img src="{f["file"]}.png" alt="{f["title"]}" loading="lazy"></a><p>{f["caption"].replace(chr(10),"<br>")}</p><a href="{f["file"]}.png" download>PNG</a> · <a href="{f["file"]}.svg" download>SVG</a></article>' for f in files)
(OUT/'index.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GNN 추가 시각화</title><style>body{font:16px/1.7 "Malgun Gothic",sans-serif;color:#172739;background:#f3f5f8;margin:0}main{max-width:1200px;margin:auto;padding:30px}article{background:white;border:1px solid #ddd;padding:24px;margin:24px 0}img{max-width:100%;height:auto}h1{font-size:30px}h2{font-size:22px}p{color:#627084}a{color:#225ac7}@media(max-width:600px){main{padding:12px}article{padding:12px}}</style><main><h1>GNN을 살펴보는 9가지 그림</h1><p>구조 · 검증 · 내부 표현 · 민감도 · 가상 실험. 각 PNG를 클릭하면 원본 크기로 볼 수 있습니다.</p>'+cards+'</main></html>',encoding='utf-8')
thumbs=[];tilew=800;tileh=550
for f in files:
    im=Image.open(OUT/(f['file']+'.png')).convert('RGB');im.thumbnail((tilew,tileh-45))
    tile=Image.new('RGB',(tilew,tileh),'white');tile.paste(im,((tilew-im.width)//2,35))
    ImageDraw.Draw(tile).text((18,8),f['file'],fill=INK,font=ImageFont.truetype(str(FONT),19));thumbs.append(tile)
sheet=Image.new('RGB',(tilew*3,tileh*3),'#e4e9f0')
for i,tile in enumerate(thumbs):sheet.paste(tile,((i%3)*tilew,(i//3)*tileh))
sheet.save(OUT/'00_gnn_overview.png')
checks['figures']=len(files);checks['seed']=a.SEED;checks['pca_explained_variance']=var.tolist();checks['embedding_players']=len(seen)
checks['png_dimensions']={f['file']:list(Image.open(OUT/(f['file']+'.png')).size) for f in files}
(OUT/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
with zipfile.ZipFile(P/'mcc_gnn_visualizations_expanded.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.iterdir()):z.write(f,'gnn_visualizations/'+f.name)
    z.write(__file__,'build_gnn_figures.py')
print(json.dumps(checks,indent=2),flush=True)
