# Team0 vs ont_platform RAG 엔진 비교 작업지시서

작성일: 2026-06-08  
작업 위치: `E:\ontology_edu\X_ont_std\validation\rag_engine_comparison`  
목적: Team0 RAG 소스와 `ont_platform` v4/v5의 RAG 엔진 성능을 같은 기준으로 비교한다.

## 1. 핵심 원칙

이번 작업은 단순 답변 정확도 비교가 아니다.

반드시 다음 두 층을 분리한다.

```text
1. 답변 품질 비교
   - 최종 답변이 예상 답변과 얼마나 맞는가
   - 기존 Team0/Team1/Team2/v4/v5 정확도 비교

2. RAG 엔진 성능 비교
   - chunking
   - metadata
   - embedding
   - vector retrieval
   - ranking
   - grounding
   - no-answer
   - latency
   - API/token 효율
```

최종 보고서에서는 두 결과를 섞지 않는다.

## 2. 비교 대상

### 2.1 Team0

소스/평가 위치:

```text
validation\comparison_team0_phase1
```

주요 분석 대상:

```text
config.py
extractors\chunk_extractor.py
extractors\metadata_extractor.py
builders\vector_builder.py
builders\ontology_builder.py
clients\team0_client.py
evaluators\accuracy_evaluator.py
evaluators\performance_evaluator.py
results\
```

### 2.2 ont_platform v4

소스 위치:

```text
ont_platform\v4
```

평가 결과:

```text
validation\ont_platform_v4_eval
```

주요 분석 대상:

```text
backend\app\services\document.py
backend\app\services\vector_search.py
backend\app\services\query_planner.py
backend\app\services\hybrid_synthesizer.py
backend\app\services\llm_client.py
```

### 2.3 ont_platform v5

소스 위치:

```text
ont_platform\v5
```

평가 결과:

```text
validation\ont_platform_v5_eval
```

추가 분석 대상:

```text
backend\app\services\evidence_gate.py
backend\app\services\question_analyzer.py
config\answer_policies.jsonl
```

## 3. 입력 데이터

### 3.1 문서

기존 평가와 동일한 PDF 8개를 기준으로 한다.

```text
E:\ai_lab_SIT\target_doc\*.pdf
```

### 3.2 질문셋

동일 24문항 기준:

```text
validation\ont_platform_v5_eval\data\3팀_정확도_비교.xlsx
```

보조 질문셋:

```text
validation\comparison_team0_phase1\test_queries.json
```

## 4. 산출 폴더 구조

```text
validation\rag_engine_comparison
├─ data
├─ reports
├─ results
├─ src
├─ TASK_INSTRUCTION.md
└─ PROGRESS_REPORT.md
```

역할:

| 폴더 | 역할 |
|---|---|
| `data` | 비교에 필요한 입력 복사본 또는 참조 메타데이터 |
| `results` | 코드 분석 JSON, 지표 계산 JSON, 중간 산출물 |
| `reports` | 최종 Markdown/Excel 보고서 |
| `src` | 비교 분석 스크립트 |

## 5. 비교 축

### 5.1 문서 처리

비교 항목:

```text
chunk size
chunk overlap
chunk 단위
총 chunk 수
page/source metadata 보존 여부
category metadata 보존 여부
document id 추적 여부
```

질문:

```text
Team0와 ont_platform은 같은 PDF에서 비슷한 수의 chunk를 만드는가?
page/source 정보가 답변 근거로 보존되는가?
나중에 근거 페이지 hit@k를 계산할 수 있는 구조인가?
```

### 5.2 임베딩/인덱싱

비교 항목:

```text
embedding model
embedding API 호출 방식
batch 처리 여부
concurrency
vector store
index build time
token/API 효율
```

주의:

Team0의 기존 분석에서 Gemini batch endpoint 미사용 및 개별 호출/동시성 문제가 지적된 바 있다. 이번 비교에서는 실제 코드 기준으로 다시 확인한다.

### 5.3 검색/Retrieval

비교 항목:

```text
top_k
score semantics
distance vs similarity
검색 후보 수
정답 근거 hit@k
retrieval_miss
ranking_issue
category-aware retrieval 여부
```

중요:

`score`가 distance인지 similarity인지 시스템별로 다를 수 있다. 수치를 직접 비교하기 전에 의미를 확인한다.

### 5.4 답변 합성/LLM

비교 항목:

```text
LLM model
prompt grounding
citation format
문서 근거 외 일반론 생성 방지
fallback behavior
no-answer behavior
```

v5는 no-answer 시 LLM 호출이 차단되어야 한다.

### 5.5 no-answer / hallucination 방지

비교 항목:

```text
out-of-domain 질문 감지
category mismatch 감지
no-answer 정확도
no-answer 시 llm_used=False 여부
hallucinated answer count
```

STD-S 보정 기준:

```text
질문은 해당 카테고리 문서와 관련이 없습니다.
```

### 5.6 운영 성능

비교 항목:

```text
API success rate
avg latency
p50/p95/p99 latency
upload/index time
cache/fallback 여부
error type
```

## 6. 기존 결과 활용 원칙

기존에 이미 생성된 결과는 재활용한다.

### 6.1 Team0 관련

확인 대상:

```text
validation\comparison_team0_phase1\results
```

주의:

Team0 결과는 파일 간 수치 불일치가 있었으므로, 어떤 파일을 기준으로 삼는지 명시한다.

기존 확인된 이슈:

```text
validation_report.md / detailed_results.json: Team0 30%, API success 0%
summary.txt: Team0 58.54%, API success 100%
```

따라서 최종 보고서에서는 Team0 수치를 다음처럼 구분한다.

```text
Team0 reported summary score
Team0 failed API run score
Team0 source-level RAG design score
```

### 6.2 ont_platform v4

기존 결과:

```text
validation\ont_platform_v4_eval\reports\4팀_정확도_비교.xlsx
validation\ont_platform_v4_eval\results\same24\same24_team4_results.json
```

주의:

v4는 동일 24문항 기준 `67.50%`였으나, STD-S 카테고리 무관 보정 기준에서는 더 낮게 해석해야 한다.

### 6.3 ont_platform v5

기존 결과:

```text
validation\ont_platform_v5_eval\reports\5팀_정확도_비교_v5.xlsx
validation\ont_platform_v5_eval\results\same24_auto\v5_same24_auto_results.json
```

기존 확인:

```text
기존 예상답변 기준: Team5 49.38%
STD-S 보정 기준: Team5 75.21%
STD-S/Snowflake: Team5 87.50%
```

## 7. 추가 실행 여부 판단

먼저 기존 결과로 1차 비교 보고서를 만든다.

추가 실행은 다음 경우에만 한다.

```text
retrieval hit@k 계산에 필요한 근거 page 정보가 부족한 경우
Team0 결과의 API 성공/실패 기준이 불명확한 경우
v5 search_mode별 비교가 필요한 경우
latency p95/p99가 기존 결과에 없는 경우
```

추가 실행 후보:

```text
Team0 재실행
v4 재실행
v5 search_mode별 실행
retrieval-only 평가
```

## 8. 작업 단계

### Step 1: 코드 구조 분석

산출물:

```text
results\source_structure_analysis.json
reports\source_structure_analysis.md
```

내용:

```text
Team0/v4/v5의 chunking, embedding, retrieval, synthesis, no-answer 구조 비교
```

### Step 2: 기존 결과 통합

산출물:

```text
results\existing_metrics_summary.json
```

내용:

```text
정확도
latency
API success
llm_used
no_answer
vector_hits
ontology_hits
```

### Step 3: RAG 엔진 지표 산정

산출물:

```text
results\rag_engine_metrics.json
```

내용:

```text
chunk count
embedding call pattern
retrieval top_k
metadata richness
grounding support
no-answer support
```

### Step 4: 보고서 작성

산출물:

```text
reports\team0_vs_ont_platform_rag_comparison.md
reports\team0_vs_ont_platform_rag_comparison.xlsx
```

## 9. 최종 보고서 구조

최종 보고서는 다음 구조로 작성한다.

```text
1. Executive Summary
2. 비교 대상과 입력 데이터
3. 소스 구조 비교
4. 문서 처리/chunking 비교
5. embedding/indexing 비교
6. retrieval/ranking 비교
7. answer synthesis 비교
8. no-answer/hallucination 비교
9. latency/API 안정성 비교
10. 정확도 비교
11. 결론
12. 개선 권고
```

## 10. 판정 기준

각 시스템은 다음 관점으로 판정한다.

| 관점 | 판정 질문 |
|---|---|
| 검색 품질 | 정답 근거를 잘 찾는가 |
| 답변 품질 | 찾은 근거로 정확히 답하는가 |
| 근거성 | 답변과 citation이 연결되는가 |
| 안전성 | 모르면 모른다고 하는가 |
| 운영성 | 빠르고 안정적인가 |
| 확장성 | metadata/policy/routing 확장이 쉬운가 |

## 11. 주의사항

1. Team0 수치는 파일 간 불일치가 있으므로 단일 숫자로 단정하지 않는다.
2. v4와 v5는 정답 기준이 다른 평가를 섞지 않는다.
3. RAG 엔진 비교에서 “정확도 1위”만으로 엔진 우수성을 판단하지 않는다.
4. no-answer는 실패가 아니라 정확도의 일부다.
5. v5는 아직 P0 구현이므로 RRF/score calibration 미완성 상태임을 명시한다.

## 12. 성공 기준

이 작업은 다음 산출물이 생성되면 완료로 본다.

```text
validation\rag_engine_comparison\reports\team0_vs_ont_platform_rag_comparison.md
validation\rag_engine_comparison\reports\team0_vs_ont_platform_rag_comparison.xlsx
validation\rag_engine_comparison\results\source_structure_analysis.json
validation\rag_engine_comparison\results\existing_metrics_summary.json
```

최종 결론에는 반드시 다음을 포함한다.

```text
Team0의 강점/약점
ont_platform v4의 강점/약점
ont_platform v5의 강점/약점
RAG 엔진 관점 최종 권고
다음 개발 우선순위
```
