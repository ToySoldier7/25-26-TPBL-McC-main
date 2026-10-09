# 맥컬러 활용 분석

## 최신 그래프 분석 보고서

- [HTML 상세 보고서](mcc_gnn_analysis/mcc_gnn_report.html): 외국인 35명 전체 적합도 순위, 선수별 근거, 그래프 모델 검증, 가중치 변경·역할 필터.
- [35명 순위 CSV](mcc_gnn_analysis/v2/expanded_scouting_ranking.csv)
- [발표용 PNG·SVG 8종](mcc_gnn_analysis/mcc_graph_v2_figures.zip)
- [분석 방법과 재현 안내](mcc_gnn_analysis/README.md)

HTML 보고서는 그래프가 내장되어 있어 해당 HTML 파일 하나만 내려받아 브라우저에서 열어도 됩니다. 계약 및 은퇴 보도 상태와 관계없이 보유 표본의 외국인 35명을 같은 점수 기준으로 비교합니다. 점수는 기술·역할 스카우팅 정책이며, 검증된 선수 궁합이나 계약 가능 확률을 뜻하지 않습니다.

```bash
cd mcc_gnn_analysis
python -m pip install -r requirements.txt -r requirements_viz.txt
python strengthen.py
python build_report.py
```

분석 코드는 저장소의 `GNN/` 데이터를 사용합니다. 보고서 그림을 재생성하는 현재 기본 환경은 Windows의 맑은 고딕입니다. 완성된 HTML·CSV·PNG·SVG는 Python 실행 없이 확인할 수 있습니다.


## 1. 폴더 구조

| 폴더 | 내용 |
|---|---|
| `PBP_Crawling/` | Play-By-Play 수집 및 전처리 |
| `GNN/` | GNN용 데이터 생성 및 분석 |
| `Network/` | 네트워크 분석 |
| `Cluster/` | 클러스터 분석 |


## 2. 전체 흐름

1. **데이터 수집** (`PBP_Crawling/`)
   TPBL 공식 사이트에서 레오파즈 42경기 Play-by-Play 수집.
2. **모델링**
   - GNN: 선수 역할 임베딩, 조합별 성과 분석
   - Network: 공출전·어시스트 네트워크 분석
   - Cluster: 선수 역할 유형 군집
3. **인사이트 도출**
   분석 결과 종합 → 맥컬러 활용 방안 정리
