from pathlib import Path
P=Path(__file__).resolve().parent
# Remove the obsolete typo commentary from our report source and archived report.
for name in ['build_report_v2.py','mcc_gnn_report_v1.html','build_report_v1.py']:
    p=P/name;s=p.read_text(encoding='utf-8')
    s=s.replace(' · 대상 구단은 KBO가 아닌 KBL 서울 삼성 썬더스',' · 서울 삼성 썬더스')
    p.write_text(s,encoding='utf-8')
r=P/'README.md';s=r.read_text(encoding='utf-8')
s=s.replace('# McCullough 그래프 분석 V2','# McCullough 그래프 분석 · 확장 상세 보고서')
s=s.replace('- 사용자 조건: **확인된 자유계약 선수만**. 데이터 내 35명에서 확인된 FA 0명. `confirmed_fa_ranking.csv`는 헤더만 있으며 계약 미확인을 영입 가능으로 취급하지 않음.','- 현재 후보 범위: **계약 상태와 관계없이** 200분 이상 외국인 35명. 은퇴 보도 2명은 참고자료로 두고 33명에게 순위를 부여. 역할 조건은 선택 필터이며 통과 22명. 계약 정보는 점수에 반영하지 않음.')
s=s.replace('- `v2/confirmed_fa_ranking.csv`: 확인된 FA 및 분석자 선별 조건 모두 통과한 선수만 출력. 현재 0행.','- `v2/expanded_scouting_ranking.csv`: **현재 사용하는 전체 33명 순위**, 새 후보군에서 500회 재표집한 점수/순위 구간, 역할순위, 계약 출처.\n- `v2/expanded_weight_sensitivity.csv`: 전체 33명에 대한 40/60/80% 정책 순위.\n- `v2/benchmark_only.csv`: 은퇴 보도 2명 참고 통계.\n- `v2/expanded_summary.json`: 확장 범위·검증 요약.\n- `v2/confirmed_fa_ranking.csv`: 이전 FA 제한 분석의 보관 파일이며 현재 순위에 사용하지 않음.')
s=s.replace('- `v2/figures/`: 발표에 사용할 PNG/SVG 5종.','- `v2/figures/`: 현재 보고서에서 사용하는 PNG/SVG 8종. `fa_gate`는 이전 분석 그림이며 현재 보고서·그림 ZIP에 포함하지 않음.')
s=s.replace('- `build_report_v2.py`: 출처 기록, 엄격한 FA 필터, 그림, 보고서 생성.','- `build_report_v3.py`: 상세 보고서와 전체 후보 비교 UI.\n- `expand_scouting.py`: 계약 제한 없는 순위·500회 경기 재표집. 기존 36명 백분위 척도를 유지하여 원래 점수와 일치 검증.\n- `build_report_v2.py`: 모델 검증 부분을 재사용하는 이전 보고서 생성기. 최종 출력은 v3가 확장 보고서로 갱신.')
s=s.replace('계약 확인은 보유 데이터 35명 범위입니다. 전 세계 FA 전체 목록을 확보한 것이 아닙니다. 추가 리그 기록 없이 외부 FA를 기존 후보와 동일 척도로 수치 순위화하지 않습니다. FA 확인 증거와 선수 기록이 추가되면 필터와 평가를 확장해야 합니다.','후보와 계약 확인은 보유 데이터 35명 범위입니다. 다른 리그 전체 외국인을 전수 수집한 것은 아닙니다. 현재 순위는 계약 가능성 순위가 아닌 기술·역할 검토 우선순위입니다. 추가 리그 선수는 동일 정의의 기록이 확보되면 척도를 검증한 후 확장해야 합니다.')
s+='\n현재 상세 HTML은 선수 검색, 역할 조건 필터, 기본/보완 비중 40/60/80% 변경을 지원하며 URL에 상태를 저장합니다. 전체 33명에 재표집을 다시 수행했으므로 예전 23명 집단의 순위 구간과 혼용하지 않습니다.\n'
r.write_text(s,encoding='utf-8')
