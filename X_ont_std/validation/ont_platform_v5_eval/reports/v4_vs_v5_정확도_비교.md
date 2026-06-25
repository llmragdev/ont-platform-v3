# v4 vs v5 정확도 비교

## 기준

- v4 공식 평가: `validation/ont_platform_v4_eval/reports/4팀_정확도_비교.xlsx`
- v5 평가: `validation/ont_platform_v5_eval/reports/5팀_정확도_비교_v5.xlsx`

## 요약

| 기준 | v4 Team4 | v5 Team5 |
|---|---:|---:|
| 기존 24문항 예상답변 기준 | 67.50% | 49.38% |
| STD-S 카테고리 무관 보정 기준 | 48.12% | 75.21% |

## 해석

v5는 no-answer 정책을 도입해 STD-S 일부 문항에서 LLM 호출을 차단했다. 다만 모든 STD-S 문항을 잡지는 못했으므로, PHASE8 다음 단계는 QuestionAnalyzer와 answer policy 매칭 범위를 강화하는 것이다.
