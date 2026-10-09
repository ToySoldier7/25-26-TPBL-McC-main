from pathlib import Path
P=Path(__file__).resolve().parent
f=P/'build_report_v2.py';s=f.read_text(encoding='utf-8')
s=s.replace('이 유형은 맥컬러와 교대할 때 공격 선택지를 넓히는 로테이션 가설입니다.','이 유형은 2·3쿼터 동시 출전에서 공간·패스 선택지를 늘리고, 1·4쿼터 교대에서도 공격 기여를 유지한다는 전술 가설입니다. 두 역할의 효과를 개별적으로 검증한 결과는 아닙니다.')
s=s.replace('KBL은 외국인 2명 보유·1명 출전 규정이 적용됩니다(<a href="https://kbl.or.kr/rule/player">KBL 선수 규정</a>). TPBL에서 두 외국인이 함께 뛴 구간의 궁합을 KBL 동시 출전 효과로 해석할 수 없습니다.','2026–27 KBL은 외국인 2명 보유, 2·3쿼터 최대 2명 동시 출전, 1·4쿼터 1명 출전으로 변경됐습니다(<a href="https://v.daum.net/v/20260115151652686?f=p">KBL 이사회 결정 보도</a>, <a href="https://www.yna.co.kr/view/AKR20260928079300007">시즌 개막 시점 재확인</a>). 동시 출전 궁합이 이번 시즌에는 실제 전술 질문입니다. 다만 리그·국내 동료·쿼터·경기 속도가 달라 TPBL 성과를 삼성 성과로 그대로 옮길 수 없습니다.')
s=s.replace('따라서 KBL 교대 운용 성능을 직접 학습할 근거도 매우 부족합니다.','따라서 두 외국인 동시 출전 맥락의 학습에 비해, 1·4쿼터에 필요한 외국인 1명 운용 성능을 직접 학습할 근거는 특히 부족합니다.')
s=s.replace('KBL 외국인 1명 운용 라인업·포제션·영상 데이터','KBL 외국인 1명 및 2명 운용을 구분한 라인업·포제션·영상 데이터')
f.write_text(s,encoding='utf-8')
(P/'build_report.py').write_text('"""Current report entry point. V1 builder is archived separately."""\nfrom build_report_v2 import main\nif __name__ == "__main__":\n    main()\n',encoding='utf-8')
readme=P/'README.md';old=readme.read_text(encoding='utf-8')
if not (P/'README_v1.md').exists():(P/'README_v1.md').write_text(old,encoding='utf-8')
readme.write_text('''# McCullough 그래프 분석 V2

현재 결과는 `mcc_gnn_report.html` 및 `v2/`입니다. 이전 분석과 시각화는 보존했으나 그 순위를 현재 영입 추천으로 사용하지 않습니다.

## 결과

- 정제 24경기, 385구간, 595.2분. 코트 밖 이벤트가 있는 16구간 제외.
- 네트워크 중심성·클러스터링 없이 속성 그래프 커널 회귀(Graph-KRR)를 적용.
- 기존 GNN 대비 팀 RMSE 개선: 경기 CV 86.78 → 69.81, 시간 평가 93.49 → 64.43.
- 단순 평균/Ridge 대비 우월성 및 선수 궁합 예측력은 입증하지 못함.
- 맥컬러 보완 가설: 효율·패스/실책·외곽 생산을 갖춘 빅맨. 리바운드는 강점.
- 사용자 조건: **확인된 자유계약 선수만**. 데이터 내 35명에서 확인된 FA 0명. `confirmed_fa_ranking.csv`는 헤더만 있으며 계약 미확인을 영입 가능으로 취급하지 않음.
- KBL 2026–27은 2·3쿼터 외국인 2명 동시 출전, 1·4쿼터 1명. 동시 출전 및 교대 운용 모두 관련 있으나 KBL 성과 검증 없음.

## 실행

Python, numpy, pandas, matplotlib가 필요합니다. 기존 `requirements.txt`와 `requirements_viz.txt`를 참고하세요. 보고서는 Windows 맑은 고딕을 사용합니다.

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:PYTHONIOENCODING='utf-8'
python strengthen.py
python build_report.py
```

분석은 `analyze.py`의 자료 로더를 재사용합니다. 원래 입력 폴더를 유지해야 합니다. seed=20261010. 입력 해시는 `v2/run_summary.json`에 있습니다. 전부 재실행하면 수 분 걸릴 수 있습니다.

## 산출물 해석

- `v2/metrics.csv`, `predictions.csv`, `splits.csv`, `hyperparameters.csv`: 외부 평가·분할·내부 튜닝.
- `v2/paired_comparisons.csv`: 경기별 고정 예측 2,000회 bootstrap; 전체 재학습 구간 아님.
- `v2/type_sensitivity.csv`, `graph_counterfactuals.csv`: 동일 맥락 비교·100회 계수 재추정. 인과효과 아님.
- `v2/scouting_ranking.csv`: 전체 TPBL 표본의 **내부 역할 정책 점수**. conditional_rank는 FA 영입 순위가 아님. availability 칼럼은 이 파일에서 갱신하지 않으므로 최신 상태는 availability_review.csv만 사용.
- `v2/scout_bootstrap.csv`: 리그 경기 500회 재표집, 고정 선별집단의 점수·순위 변동.
- `v2/availability_review.csv`: 2026-10-10 공개 자료 확인표. 구단 발표/로스터와 영입 보도는 구분. 미확인은 FA가 아님. 계약서 법률 감사가 아님.
- `v2/confirmed_fa_ranking.csv`: 확인된 FA 및 분석자 선별 조건 모두 통과한 선수만 출력. 현재 0행.
- `v2/figures/`: 발표에 사용할 PNG/SVG 5종.
- `build_report_v2.py`: 출처 기록, 엄격한 FA 필터, 그림, 보고서 생성.

## 검증과 한계

경기 전 날짜만 사용하고 시간 평가 특성은 첫 평가일 이전으로 동결. 학습 노드만 스케일링. 경기별 중첩 검증. 미래 데이터 변조 불변성·노드 순서 불변성·커널 PSD 확인. 시간 평가 8경기는 기존에 관찰했던 자료로 완전히 새로운 홀드아웃이 아닙니다.

계약 확인은 보유 데이터 35명 범위입니다. 전 세계 FA 전체 목록을 확보한 것이 아닙니다. 추가 리그 기록 없이 외부 FA를 기존 후보와 동일 척도로 수치 순위화하지 않습니다. FA 확인 증거와 선수 기록이 추가되면 필터와 평가를 확장해야 합니다.

구버전 설명은 `README_v1.md`, 보고서는 `mcc_gnn_report_v1.html`, 생성기는 `build_report_v1.py`에 보관합니다.
''',encoding='utf-8')
