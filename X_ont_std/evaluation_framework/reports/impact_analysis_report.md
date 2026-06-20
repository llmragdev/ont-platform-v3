# Stage 3 영향도 분석 보고서

**생성일**: 2026-06-07 20:20:38

## 요약

| 항목 | 결과 |
|---|---:|
| 총 수정 | 8개 |
| 온톨로지 변경 | 4개 |
| RAG 변경 | 2개 |
| 평가 기준 변경 | 2개 |
| 전체 영향도 점수 | 0.37 |
| 위험도 | LOW |

## 온톨로지 변경점

### REMOVE_CONCEPTS
- 위험도: LOW
- 개념: rag
- 사유: 정답 수정으로 더 이상 필요 없음

### REMOVE_CONCEPTS
- 위험도: LOW
- 개념: knowledge, semantic, ontology
- 사유: 정답 수정으로 더 이상 필요 없음

### REMOVE_CONCEPTS
- 위험도: LOW
- 개념: rag, semantic
- 사유: 정답 수정으로 더 이상 필요 없음

### REMOVE_CONCEPTS
- 위험도: LOW
- 개념: metadata
- 사유: 정답 수정으로 더 이상 필요 없음

## RAG 변경점

### ADD_EXCLUSION_RULE
- 정답이 범위 외이므로 이 카테고리는 자동 제외

### ADJUST_SEARCH_WEIGHTS
- 정답 수정으로 검색 가중치 상향

## 구현 순서

1. [P2] ADD_EXCLUSION_RULE
   - 기한: 1일 이내

2. [P2] ADJUST_SEARCH_WEIGHTS
   - 기한: 1일 이내

3. [P3] REMOVE_CONCEPTS
   - 기한: 1주일 이내

4. [P3] REMOVE_CONCEPTS
   - 기한: 1주일 이내

5. [P3] REMOVE_CONCEPTS
   - 기한: 1주일 이내

6. [P3] REMOVE_CONCEPTS
   - 기한: 1주일 이내

