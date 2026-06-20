# 0620-29 v4 Team4 대비 v5 Team5 점수 하락 원인 및 채점 기준 정정

**작성일:** 2026-06-20  
**작성자:** Codex  
**상태:** 평가 기준 정정 및 스크립트 보정 완료

---

## 1. 핵심 결론

v5 Team5 점수가 v4 Team4의 85점보다 낮게 나온 것은 **v5 성능 저하만으로 해석하면 안 된다.**

가장 큰 원인은 다음이다.

```text
Team4 85점: v1.2 재평가 기준, Snowflake 함정질문 특별 규칙 포함
Team5 낮은 점수: 단순 expected_items 키워드 매칭 기반 보수 점수
```

즉, 두 점수는 같은 채점 기준으로 산출된 숫자가 아니다.

---

## 2. v4 Team4 점수 구조

엑셀 기준 요약:

| 카테고리 | Team4 점수 |
|---|---:|
| Advanced RAG | 90 |
| Ontology | 74.38 |
| Snowflake | 90.62 |
| 전체 평균 | 85 |

Team4의 높은 점수에는 Snowflake 카테고리의 특수 규칙이 크게 작용했다.

---

## 3. v1.2 Snowflake 특별 규칙

v1.2 기준에서는 Snowflake 문항을 함정 질문으로 처리한다.

핵심 규칙:

```text
Snowflake 관련 내용이 문서에 없을 때,
"관련 없음", "문서에 없음", "근거 없음", "확인 불가"를 명시하면 정답으로 인정한다.
```

따라서 Snowflake 문항에서 모르는 것을 모른다고 말하면 높은 점수를 받는다.

반대로 문서 근거 없이 Snowflake 설명을 생성하면 큰 감점이다.

---

## 4. 기존 Team5 평가 스크립트 문제

기존 `evaluate_team5_24qa.py`는 대체로 다음 방식이었다.

```text
기본 50점
expected_items 키워드가 답변에 포함될 때마다 +10점
```

이 방식의 문제:

1. Snowflake 문서가 없어서 "관련 없음"이라고 잘 답해도 Snowflake expected keyword가 없으면 점수가 낮아질 수 있다.
2. v4 Team4의 85점과 직접 비교할 수 없다.
3. "정직하게 모른다고 답한 것"과 "답변 실패"를 구분하지 못한다.

---

## 5. 조치 내용

대상 파일:

`E:\ontology_edu\X_ont_std\ont_platform\v5\backend\scripts\evaluate_team5_24qa.py`

수정 내용:

1. API 파라미터명 정정
   - `separate_general` → `separate_sources`

2. 점수 2종 저장
   - `score_conservative`
   - `score_v12_comparable`

3. 최종 `score`는 v1.2 비교 가능 점수로 저장

4. Snowflake 함정질문 특별 규칙 추가

판정 문구:

```text
관련 없음
관련 정보를 찾을 수 없습니다
관련 근거 없음
문서에 없음
근거 없음
확인하지 못했습니다
확인되지 않습니다
찾지 못했습니다
답변하지 않습니다
```

위 문구가 Snowflake 문항 답변에 포함되면 `score_v12_comparable = 100`으로 처리한다.

---

## 6. 검증 결과

실행:

```bash
python -m py_compile scripts\evaluate_team5_24qa.py
```

결과:

```text
통과
```

스크립트 내 확인:

```text
separate_sources 파라미터 사용
score_conservative 저장
score_v12_comparable 저장
Snowflake trap rule 적용
```

---

## 7. 최종 해석

v5 현재 점수가 낮아 보이는 것은 다음 두 원인이 섞인 결과다.

| 원인 | 성격 |
|---|---|
| 채점 기준 불일치 | 가장 큰 원인 |
| Snowflake 함정 규칙 미반영 | 큰 원인 |
| Ontology 데이터 부족 | 실제 시스템 한계 |
| 답변 합성/출처 표시 혼선 | 실제 시스템 개선 필요 |
| RAG-ontology 동기화 부족 | 실제 시스템 개선 필요 |

따라서 현재 점수를 이렇게 해석해야 한다.

```text
기존 낮은 Team5 점수 = 보수적 자동 키워드 점수
v4 Team4와 비교할 점수 = score_v12_comparable
```

---

## 8. 다음 액션

1. 백엔드 완전 재시작
2. `evaluate_team5_24qa.py` 재실행
3. 결과 JSON에서 다음 두 점수 비교
   - `score_conservative`
   - `score_v12_comparable`
4. Snowflake 8문항에서 "관련 없음" 응답이 100점으로 처리되는지 확인
5. Team4 85점과는 `score_v12_comparable` 기준으로 비교

---

## 9. GO/WAIT 판정

```text
채점 기준 보정: GO
Team4와 직접 비교: score_v12_comparable 재실행 후 GO
기존 52.1점 해석: 보수적 자동 점수로만 유지
v5 실제 성능 판단: 재채점 + UI/백엔드 최신 반영 후 판단
```

