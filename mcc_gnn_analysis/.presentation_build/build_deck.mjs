import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Presentation, PresentationFile } from 'file:///C:/Users/junhy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import { finalizePresentation, applyPresentationChartFont } from 'file:///C:/Users/junhy/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations/container_tools/artifact_tool_utils.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BUILD = path.join(ROOT, '.presentation_build');
const OUT = path.join(ROOT, 'PPT_발표자료');
const SKILL = 'C:/Users/junhy/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations';
const PY = 'C:/Users/junhy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
process.env.RUNTIME_NODE_MODULES='C:/Users/junhy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const FONT = 'Malgun Gothic';
const C = {ink:'#182C3A', teal:'#176A80', muted:'#586976', gray:'#AEBBC6', orange:'#BB6C36', bg:'#FFFFFF', faint:'#E8EEF2'};
await fs.mkdir(OUT, {recursive:true});
await fs.mkdir(path.join(OUT,'그림_원본'), {recursive:true});
await fs.mkdir(path.join(OUT,'슬라이드_PNG'), {recursive:true});

function parseCsv(raw) {
  const rows=[];let row=[],cell='',q=false;
  for(let i=0;i<raw.length;i++) {let c=raw[i];if(c==='"'){if(q&&raw[i+1]==='"'){cell+='"';i++;}else q=!q;}
    else if(c===','&&!q){row.push(cell);cell='';}else if((c==='\n'||c==='\r')&&!q){if(c==='\r'&&raw[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))rows.push(row);row=[];cell='';}else cell+=c;}
  if(cell||row.length){row.push(cell);rows.push(row);}const heads=rows.shift();heads[0]=heads[0].replace(/^\uFEFF/,'');
  return rows.map(r=>Object.fromEntries(heads.map((h,i)=>[h,r[i]])));
}
const csv=async f=>parseCsv(await fs.readFile(path.join(ROOT,f),'utf8'));
const metrics=await csv('v2/metrics.csv');
const candidates=await csv('v2/expanded_scouting_ranking.csv');
const policy=JSON.parse(await fs.readFile(path.join(ROOT,'v2/scouting_policy.json'),'utf8'));
const summary=JSON.parse(await fs.readFile(path.join(ROOT,'v2/run_summary.json'),'utf8'));
const top=['Drew Pember','Trey Thompkins III','Marko Todorovic'].map(n=>candidates.find(r=>r.name===n));
const n=(v,d=1)=>Number(v).toFixed(d);
const pres=Presentation.create({slideSize:{width:1280,height:720}});
pres.theme.defaultFont=FONT;
const scripts=[];

function text(slide,content,x,y,w,h,size=28,bold=false,color=C.ink) {
  const a=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  a.text=content;a.text.style={typeface:FONT,fontSize:size,bold,color};return a;
}
function page(title,foot='') {
  const s=pres.slides.add();s.background.fill=C.bg;
  text(s,title,64,42,1152,100,42,true);
  if(foot)text(s,foot,64,653,1108,45,17,false,C.muted);
  text(s,String(pres.slides.items.length).padStart(2,'0'),1185,660,42,30,16,false,C.muted);
  return s;
}
function note(s,title,body,sources) {
  s.speakerNotes.text=body+'\n\n근거 파일\n'+sources.map(f=>path.join(ROOT,f)).join('\n');
  scripts.push({title,body,sources});
}
function table(s,values,x,y,w,h,widths,size=26) {
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{typeface:FONT,fontSize:size,color:C.ink},margins:{left:16,right:12,top:13,bottom:10}});
  t.borders.assign({fill:C.faint,width:1,style:'solid'});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);cell.fill=r===0?C.teal:(r%2===0?'#F3F6F8':C.bg);
    cell.text.style={typeface:FONT,fontSize:size,bold:r===0,color:r===0?'#FFFFFF':C.ink};
  }
  return t;
}

// 1. Cover.
{
 const s=pres.slides.add();s.background.fill=C.bg;
 text(s,'맥컬러의 보완 유형과\n후보 검토',64,170,1120,190,66,true,C.ink);
 text(s,'TPBL 기록을 활용한 탐색적 분석',68,390,1090,58,31,false,C.teal);
 text(s,'모델 성능 검증과 역할 보완 기준',68,465,1080,52,28,false,C.muted);
 text(s,'분석 자료 기준 2026.10.10',68,647,900,34,18,false,C.muted);
 note(s,'맥컬러의 보완 유형과 후보 검토','이번 분석은 맥컬러의 기록에서 보완할 역할을 찾고, 그 기준으로 추가 검증 후보를 정리한 탐색적 분석입니다. 먼저 그래프 모형의 예측 성능을 확인했습니다. 실제 선수 궁합을 입증했는지와 후보 개인의 기록이 보완적인지는 구분해서 설명하겠습니다.',['README.md','v2/run_summary.json']);
}
// 2. Data and evaluation.
{
 const s=page('분석 자료와 검증 설계','자료: 정제된 맥컬러 출전 구간. 시간 평가 8경기는 이전 분석에서 확인한 자료.');
 text(s,'24경기',64,170,350,90,60,true,C.teal);text(s,'385구간',465,170,350,90,60,true,C.teal);text(s,'595.2분',875,170,340,90,60,true,C.teal);
 text(s,'분석 대상',66,275,350,40,26,true);text(s,'라인업 유지 구간',465,275,350,40,26,true);text(s,'정제 후 출전시간',875,275,340,40,26,true);
 text(s,'경기 단위 검증',64,375,400,48,30,true);
 text(s,'외부 5-fold 평가와 내부 3-fold 설정 선택',64,438,1100,48,28);
 text(s,'시간 순서 평가',64,513,400,48,30,true);
 text(s,'앞 16경기 학습, 뒤 8경기 평가\n평가 특성은 첫 평가일 이전으로 동결',64,568,1120,78,25);
 note(s,'분석 자료와 검증 설계','정제 후 자료는 24경기, 385구간, 595.2분입니다. 선수 이벤트와 코트 위 명단이 맞지 않는 16구간을 제외했습니다. 같은 경기의 구간이 학습과 평가에 섞이지 않도록 경기 단위로 나눴습니다. 무작위 경기 교차검증은 사후 비교에 가깝고, 미래 예측 해석은 시간 순서 평가를 우선합니다. 다만 뒤 8경기도 기존에 확인한 자료이므로 완전히 새로운 검증 자료는 아닙니다.',['v2/run_summary.json','v2/splits.csv','strengthen.py']);
}
// 3. Editable model comparison.
{
 const s=page('기존 GNN 대비 오차 감소, 기준선 대비 이득은 미확인','팀 순득점/36분의 출전시간 가중 RMSE. 낮을수록 좋음. 시간 평가 8경기는 재사용 자료.');
 const models=['GNN-v1','Graph-KRR','Mean','Ridge'];
 const chart=s.charts.add('bar',{position:{left:64,top:153,width:1150,height:350},categories:['기존 GNN','Graph-KRR','단순 평균','Ridge'],
  series:[{name:'경기 교차검증',values:models.map(m=>Number(n(metrics.find(r=>r.model===m&&r.split==='group_nested').net_rmse,2))),fill:C.gray},{name:'시간 순서 평가',values:models.map(m=>Number(n(metrics.find(r=>r.model===m&&r.split==='temporal_frozen').net_rmse,2))),fill:C.teal}],
  barOptions:{direction:'column',grouping:'clustered',gapWidth:90},hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:22}},
  xAxis:{textStyle:{fontSize:23},majorGridlines:null},yAxis:{min:0,max:110,majorUnit:20,textStyle:{fontSize:19},majorGridlines:{fill:C.faint,width:1}},
  dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:19,bold:true}},chartFill:C.bg,plotAreaFill:C.bg});
 applyPresentationChartFont(chart,{fontFamily:FONT});
 text(s,'기존 GNN 대비 RMSE 감소: 19.6% / 31.1%',64,526,1150,50,30,true,C.teal);
 text(s,'단순 평균과 비슷한 성능으로 조합 차이를 예측하는 능력은 입증하지 못함',64,589,1140,50,25);
 note(s,'모델 성능 검증','팀 순득점을 36분으로 환산한 목표를 예측했습니다. Graph-KRR는 기존 GNN보다 RMSE가 교차검증에서 19.6%, 시간 평가에서 31.1% 감소했습니다. 하지만 단순 평균이나 Ridge보다 잘 예측한다는 근거는 확보하지 못했습니다. 시간 평가의 Graph-KRR 예측은 약 5.78에서 5.88점으로 거의 일정했습니다. 오차 감소만으로 선수 조합 차이를 학습했다고 해석할 수 없습니다. 기존 GNN은 기존 구조와 고정 설정을 사용한 비교 대상입니다.',['v2/metrics.csv','v2/paired_comparisons.csv','v2/predictions.csv','strengthen.py']);
}
// 4. Editable profile.
{
 const s=page('리바운드는 강점, 효율과 공격 연결은 보완 과제','200분 이상 외국인 36명 내 축소 추정 백분위. 백분위는 실제 성공률과 다름.');
 const labels=['득점 효율 TS','패스/실책 AST/TOV','외곽 생산/36분','득점/36분','리바운드/36분'];
 const vals=['TS','creation','three_made36','points','rebounds'].map(k=>Number(n(policy.mcc_percentiles[k]*100,1)));
 const chart=s.charts.add('bar',{position:{left:64,top:150,width:1120,height:365},categories:labels,series:[{name:'백분위',values:vals,fill:C.teal,points:vals.map((v,i)=>({idx:i,fill:v<50?C.orange:C.teal}))}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:62},hasLegend:false,
  xAxis:{textStyle:{fontSize:23},majorGridlines:null},yAxis:{min:0,max:100,majorUnit:25,textStyle:{fontSize:19},majorGridlines:{fill:C.faint,width:1}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0',textStyle:{fontSize:23,bold:true}},chartFill:C.bg,plotAreaFill:C.bg});
 applyPresentationChartFont(chart,{fontFamily:FONT});
 text(s,'검토 가설: 효율과 패스, 외곽 생산을 갖춘 빅맨',64,541,1150,52,31,true,C.teal);
 text(s,'실제 공간 창출과 수비 적합성은 영상으로 확인 필요',64,601,1140,42,25);
 note(s,'맥컬러의 보완 유형','맥컬러의 축소 통계는 표본 내 리바운드 88.9백분위, 득점 61.1백분위입니다. 반면 TS는 11.1백분위, AST/TOV는 13.9, 외곽 생산은 27.8입니다. 리바운드가 약하다고 보고 리바운더만 더하는 설명은 맞지 않습니다. 효율과 공격 연결, 외곽 생산을 보완하는 빅맨을 검토할 수 있습니다. 이것은 기록에서 얻은 전술 가설이고, 실제 궁합을 검증한 결론은 아닙니다.',['v2/role_percentiles.csv','v2/scouting_policy.json']);
}
// 5. Policy.
{
 const s=page('후보 평가 기준','분석자가 정한 정책 점수. 개인 기록의 보완 가능성을 평가하며 실제 조합 효과는 검증하지 않음.');
 text(s,'기본 기여 60% + 맥컬러 보완 40%',64,160,1150,72,44,true,C.teal);
 text(s,'기본 기여',64,280,430,48,30,true);text(s,'효율 35% / 득점 20%\n리바운드 25% / AST/TOV 20%',64,349,560,102,28);
 text(s,'맥컬러 보완',700,280,450,48,30,true);text(s,'효율 40.0% / AST/TOV 37.1%\n외곽 생산 22.9%',700,349,520,102,26);
 text(s,'전체 비교: 200분 이상 외국인 35명',64,505,1140,48,28,true);
 text(s,'빅맨 역할 조건 통과: 23명\n400분 이상, 198cm 이상, 축소 리바운드/36분 8개 이상',64,568,1140,77,25);
 note(s,'후보 평가 기준','선수 순위는 그래프 모형이 산출한 궁합 순위가 아닙니다. 기본 기여 60%와 맥컬러 보완 40%의 정책 점수입니다. 각 항목은 출전량을 고려해 축소한 기록의 표본 내 백분위를 사용합니다. 보완 비중은 맥컬러가 표본 중위값에 못 미친 정도를 기준으로 정했습니다. 200분 이상 외국인 35명을 비교했고, 계약이나 은퇴 상태로 제외하지 않았습니다. 역할 필터는 분석자가 정한 조건입니다. 점수는 승률이나 영입 성공 확률이 아닙니다.',['v2/scouting_policy.json','v2/expanded_summary.json','strengthen.py','expand_scouting.py']);
}
// 6. Native candidate table.
{
 const s=page('빅맨 역할 조건 내 우선 검토 후보','점수는 60/40 정책 기준. TS와 3점은 실측 기록. 계약 가능성과 수비 적합성은 별도 확인 필요.');
 const values=[['후보','점수','TS','3점 성공/시도','검토 이유'],...top.map((r,i)=>[i===1?'Trey Thompkins\nIII':r.name,n(r.scout_score),n(Number(r.ts)*100)+'%',r.three_made+'/'+r.three_attempts,['효율과 외곽 생산,\n볼 연결의 균형','외곽과 패스를\n결합한 보완','득점과 리바운드\n기반의 기본 기여'][i]])];
 table(s,values,64,164,1152,300,[265,100,115,210,462],25);
 const p=top[0];text(s,`Pember의 경기 재표집 점수 범위: ${n(p.score_lo)}~${n(p.score_hi)}점`,64,503,1150,50,29,true,C.teal);
 text(s,'후보 간 점수 구간이 크게 겹치므로 확정적인 우열 판단은 어려움',64,565,1140,45,25);
 text(s,'전체 2위 Jalen Harris는 가드로 빅맨 후보와 구분',64,612,1140,35,23,false,C.muted);
 note(s,'우선 검토 후보','빅맨 역할 조건을 통과한 후보 중 Pember, Thompkins, Todorovic을 먼저 검토할 수 있습니다. Pember는 여러 보완 항목을 고르게 충족하지만 3점 성공률은 32.3%이므로 엘리트 슈터로 단정하지 않습니다. Thompkins는 외곽과 패스, Todorovic은 득점과 리바운드가 주된 검토 이유입니다. 전체 2위 Harris는 193cm 가드여서 빅맨 역할과 구분했습니다. Pember의 경기 재표집 점수 범위도 57.8에서 86.8로 넓고 후보 간 구간이 겹칩니다. 실제 계약 여부를 확인한 영입 추천 순위로 제시하지 않습니다.',['v2/expanded_scouting_ranking.csv','v2/expanded_summary.json']);
}
// 7. Conclusion.
{
 const s=page('보완 유형과 후보를 제시했으며 실제 궁합은 미검증','24경기 표본, 짧은 구간의 36분 환산 목표, 재사용 평가 자료가 일반화 판단을 제한함.');
 text(s,'현재 확보한 결과',64,170,530,50,32,true,C.teal);
 text(s,'맥컬러의 보완 역할 구체화\n일관된 평가 기준으로 후보 검토 순서 제시',64,245,1140,104,31);
 text(s,'실제 조합 판단에 필요한 검증',64,391,1120,50,32,true,C.teal);
 text(s,'동시 출전과 교대 출전의 라인업 성과\n스크린과 롤/팝, 수비 매치업 영상\n개인 능력 기준선 대비 조합 상호작용의 추가 예측력',64,465,1140,151,29);
 note(s,'결론과 후속 검증','이번 연구에서 실제로 확인한 성과는 맥컬러의 보완 역할을 구체화하고 후보 검토 기준을 명시한 것입니다. 좋은 조합을 찾았다는 결론까지 도달하지는 못했습니다. 385구간 가운데 약 76%가 2분 미만이어서 36분 환산 성과가 크게 흔들립니다. 후속 분석은 동시 출전과 교대 출전을 구분하고, 개인 능력만 반영한 기준선에 조합 상호작용을 추가했을 때 보지 않은 경기에서 성능이 좋아지는지 확인해야 합니다. 수비와 스크린은 영상으로 확인해야 합니다.',['v2/analysis_stints.csv','v2/metrics.csv','v2/graph_counterfactuals.csv','v2/type_sensitivity.csv']);
}
// 8. Appendix for metric question.
{
 const s=page('부록: MSE와 모델 설정 선택 기준','MSE와 RMSE는 모형 검증 지표. 선수 후보 순위는 별도의 60/40 정책 점수로 산출.');
 text(s,'실제값: 구간 팀 순득점 × 36 / 구간 시간(분)',64,168,1150,55,30,true);
 text(s,'MSE = Σ[출전시간 × (실제값 − 예측값)²] / Σ출전시간',64,280,1150,60,31,true,C.teal);
 text(s,'RMSE = √MSE',64,375,1150,65,39,true,C.teal);
 text(s,'내부 3-fold 검증 RMSE가 가장 작은 모델 설정 선택\n별도로 남겨둔 경기에서 최종 오차 평가',64,495,1150,103,28);
 note(s,'MSE 산출과 설정 선택','MSE는 구간의 실제 팀 순득점과 모델 예측의 차이를 제곱해 평균한 값입니다. 구간 길이가 달라 실제값을 36분으로 환산하고 출전시간으로 가중했습니다. 보고서에는 제곱근인 RMSE를 표시했습니다. 내부 3-fold에서 팀 순득점 RMSE가 가장 작은 설정을 골랐으며, MSE를 최소화하는 것과 선택 순서는 같습니다. 낮은 전체 오차만으로 조합 간 차이를 잘 예측한다고 결론낼 수는 없습니다.',['strengthen.py','v2/hyperparameters.csv','v2/metrics.csv']);
}

const candidatePath=path.join(BUILD,'candidate.pptx');
await (await PresentationFile.exportPptx(pres)).save(candidatePath);
console.log('DRAFT',candidatePath);
for(let i=0;i<pres.slides.items.length;i++){
  const blob=await pres.export({slide:pres.slides.items[i],format:'png',scale:1});
  await fs.writeFile(path.join(OUT,'슬라이드_PNG',`${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
  console.log('RENDERED',i+1);
}
await fs.writeFile(path.join(BUILD,'inspection.ndjson'),(await pres.inspect({kind:'slide,textbox,table,chart',maxChars:100000})).ndjson);
const finalPath=path.join(OUT,'맥컬러_분석_발표자료.pptx');
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath,finalPath,pythonExecutable:PY,
  integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','6'],
  requiredNativeTableOwnerSlides:[6],requiredNativeChartOwnerSlides:[3,4],materializeLiteralChartWorkbooks:true,
  fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation.json')});
console.log('FINAL',JSON.stringify(result));
for(const f of ['model_comparison','mcc_profile','candidate_profiles','expanded_uncertainty','expanded_ranking'])for(const ext of ['png','svg'])await fs.copyFile(path.join(ROOT,'v2/figures',f+'.'+ext),path.join(OUT,'그림_원본',f+'.'+ext));
const script='# 맥컬러 분석 발표 대본\n\n본편 7장과 MSE 부록 1장. 본편 발표 약 5~7분 기준.\n\n'+scripts.map((r,i)=>`## ${i+1}장. ${r.title}\n\n${r.body}\n`).join('\n');
await fs.writeFile(path.join(OUT,'발표대본.md'),script,'utf8');
await fs.writeFile(path.join(OUT,'자료안내.txt'),'맥컬러 분석 발표 자료\n\n맥컬러_분석_발표자료.pptx: 본편 7장 + MSE 부록 1장. 텍스트, 차트, 표 편집 가능. 발표자 노트에 대본과 근거 파일 경로 포함.\n발표대본.md: 슬라이드별 발표 대본.\n슬라이드_PNG: 8장 미리보기.\n그림_원본: 기존 분석 그림 PNG/SVG 5종.\n\n표현 기준: 좋은 조합을 검증했다는 주장을 하지 않으며, 보완 유형과 추가 검증 후보를 제시함. 후보 점수는 기본 기여 60% + 맥컬러 보완 40%의 분석자 정책 점수.\n','utf8');
