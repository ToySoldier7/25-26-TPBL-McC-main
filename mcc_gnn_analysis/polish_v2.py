from pathlib import Path
P=Path(__file__).resolve().parent
f=P/'build_report_v2.py';s=f.read_text(encoding='utf-8')
s=s.replace("'Graph-KRR − 비교 모델의 MSE", "'Graph-KRR - 비교 모델의 MSE")
s=s.replace("assert len(review)==35 and not eligible.shape[0]","assert len(review)==35 and eligible.available_confirmed.all()")
s=s.replace('<figure><img src="v2/figures/{name}.svg" alt="{alt}" loading="lazy">','<figure><div class="chart-scroll" tabindex="0" aria-label="그래프: 작은 화면에서 좌우 스크롤"><img src="v2/figures/{name}.svg" alt="{alt}" loading="lazy"></div>')
s=s.replace('img{{display:block;width:100%;height:auto}}','img{{display:block;width:100%;height:auto}}.chart-scroll{{overflow-x:auto}}.chart-scroll img{{min-width:640px}}')
s=s.replace('PNG</a> / <a href="v2/figures/{name}.svg">SVG</a>','PNG</a> / <a href="v2/figures/{name}.svg">SVG</a> · 작은 화면에서는 그래프를 좌우로 스크롤하세요')
s=s.replace('개선율은 이번 기존 GNN 구현과의 비교이며 모든 GNN보다 우수하다는 뜻은 아닙니다.','기존 GNN은 기존 하이퍼파라미터를 유지한 3개 시드 평균이며, 새 커널 모형처럼 재튜닝하지 않았습니다. 개선율은 이 기존 구현과의 비교이며 모든 GNN보다 우수하다는 뜻은 아닙니다.')
s=s.replace('교차검증은 사후 평가이며 시간 순서를 보장하는 것은 별도 시간 분할입니다.','교차검증은 사후 평가입니다. 무작위 경기 fold에서는 평가 경기의 박스스코어가 그 이후 학습 경기의 사전 누적 통계에 반영될 수 있으므로 완전히 독립된 미래 예측 검증으로 해석하지 않습니다. 시간 순서 분할에서는 학습일이 모두 평가일보다 앞서고 평가 특성을 동결하여 이 경로를 막았습니다. 실전 예측 해석은 시간 평가를 우선합니다.')
f.write_text(s,encoding='utf-8')
