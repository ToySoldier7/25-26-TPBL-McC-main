# McCullough 그래프 분석 · 확장 상세 보고서

현재 결과는 `mcc_gnn_report.html` 및 `v2/`입니다. 이전 분석과 시각화는 보존했으나 그 순위를 현재 영입 추천으로 사용하지 않습니다.

## 결과

- 정제 24경기, 385구간, 595.2분. 코트 밖 이벤트가 있는 16구간 제외.
- 네트워크 중심성·클러스터링 없이 속성 그래프 커널 회귀(Graph-KRR)를 적용.
- 기존 GNN 대비 팀 RMSE 개선: 경기 CV 86.78 → 69.81, 시간 평가 93.49 → 64.43.
- 단순 평균/Ridge 대비 우월성 및 선수 궁합 예측력은 입증하지 못함.
- 맥컬러 보완 가설: 효율·패스/실책·외곽 생산을 갖춘 빅맨. 리바운드는 강점.
- 현재 후보 범위: **계약 상태와 관계없이** 200분 이상 외국인 35명. 은퇴 보도 2명도 포함해 전체 35명에게 순위를 부여. 역할 조건은 선택 필터이며 통과 23명. 계약 정보는 점수에 반영하지 않음.
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
- `v2/expanded_scouting_ranking.csv`: **현재 사용하는 전체 35명 순위**, 새 후보군에서 500회 재표집한 점수/순위 구간, 역할순위, 계약 출처.
- `v2/expanded_weight_sensitivity.csv`: 전체 35명에 대한 40/60/80% 정책 순위.
- `v2/benchmark_only.csv`: 이전 참고자료 파일. 현재는 제외 선수 없이 헤더만 있으며, 두 선수 모두 전체 순위에 포함.
- `v2/expanded_summary.json`: 확장 범위·검증 요약.
- `v2/confirmed_fa_ranking.csv`: 이전 FA 제한 분석의 보관 파일이며 현재 순위에 사용하지 않음.
- `v2/figures/`: 현재 보고서에서 사용하는 PNG/SVG 8종. `fa_gate`는 이전 분석 그림이며 현재 보고서·그림 ZIP에 포함하지 않음.
- `build_report_v3.py`: 상세 보고서와 전체 후보 비교 UI.
- `expand_scouting.py`: 계약 제한 없는 순위·500회 경기 재표집. 기존 36명 백분위 척도를 유지하여 원래 점수와 일치 검증.
- `build_report_v2.py`: 모델 검증 부분을 재사용하는 이전 보고서 생성기. 최종 출력은 v3가 확장 보고서로 갱신.

## 검증과 한계

경기 전 날짜만 사용하고 시간 평가 특성은 첫 평가일 이전으로 동결. 학습 노드만 스케일링. 경기별 중첩 검증. 미래 데이터 변조 불변성·노드 순서 불변성·커널 PSD 확인. 시간 평가 8경기는 기존에 관찰했던 자료로 완전히 새로운 홀드아웃이 아닙니다.

후보와 계약 확인은 보유 데이터 35명 범위입니다. 다른 리그 전체 외국인을 전수 수집한 것은 아닙니다. 현재 순위는 계약 가능성 순위가 아닌 기술·역할 검토 우선순위입니다. 추가 리그 선수는 동일 정의의 기록이 확보되면 척도를 검증한 후 확장해야 합니다.

구버전 설명은 `README_v1.md`, 보고서는 `mcc_gnn_report_v1.html`, 생성기는 `build_report_v1.py`에 보관합니다.

현재 상세 HTML은 선수 검색, 역할 조건 필터, 기본/보완 비중 40/60/80% 변경을 지원하며 URL에 상태를 저장합니다. 전체 35명에 재표집을 다시 수행했으므로 예전 23명 집단의 순위 구간과 혼용하지 않습니다.

## HTML 단독 실행

`mcc_gnn_report.html`에는 그래프 8개가 내장되어 있습니다. 이 HTML 파일 하나만 다른 폴더나 컴퓨터로 옮겨도 인터넷 연결 없이 그래프·순위·검색·필터를 사용할 수 있습니다. 그림 PNG/SVG 다운로드도 내장되어 있습니다. 별도 CSV·코드 링크는 저장소 파일을 참조합니다.

생성기 `standalone_html.py`가 로컬 이미지와 그림 다운로드를 data URL로 포함합니다. `check_standalone.cjs`는 HTML만 임시 폴더에 복사해 오프라인 렌더링을 검증합니다.
