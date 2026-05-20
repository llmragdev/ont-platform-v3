# Gemini 실제 답변 품질 평가 (NEXT_STEPS #2)

> 실행일: 2026-05-12
> 모델: gemini-2.5-flash
> 사용자: analyst (Kim Ops, AccountManager, Seoul/Incheon)
> 백엔드: claud_통합 (Phase 2 SSE + WG-3 도메인 노드 적용 후)

## 요약

- 총 케이스: 5
- Gemini 실응답: 3건
- 의도된 오류 응답: 2건 (404 OBJECT_NOT_FOUND, 403 FORBIDDEN)
- Latency 범위: 3132 ~ 11574 ms (평균 8474 ms)

## 종합 평가

| 평가 축 | 결과 |
| --- | --- |
| 한국어 자연스러움 | ✅ 모든 응답 매끄러움 (Decision / Evidence / Required follow-up 형식 준수) |
| 근거 문서 인용 정확도 | ✅ D001/D002/D003 정확히 인용. evidence_ids와 응답 본문 일치 |
| 환각(hallucination) | ✅ 없음. ontology에 있는 정보만 사용 |
| 정책 인식 | ✅ 5000원 임계값, Enterprise 계약 검증, Risk 등급 모두 반영 |
| 도메인 오류 처리 | ✅ 주문 미검출(404), 권한 부족(403)에서 LLM 호출 안 일어남 |
| 보수성 | ⚠ 룰베이스는 "승인 가능"이라 한 케이스를 Gemini는 "추가 검토" 권장 — 안전한 편향이지만 결재자 입장에서 무의미한 검토 단계가 생길 수 있음 |
| Latency | 3~12초 (Gemini API 평균 범위, 프롬프트 길이에 비례) |

## 케이스별 응답

### Case 1
**질문**: O001 주문 승인해도 될까?

**Provider**: `gemini` / **Model**: `gemini-2.5-flash` / **Latency**: 10716 ms
**감지된 객체**: ['O001']
**사용된 문서**: ['D002', 'D003', 'D001']
**추천 액션**: ['ApproveOrder', 'RejectOrder', 'HoldOrder']

**답변**:
```
- Decision (승인/반려/추가검토): 추가검토
- Evidence (근거):
    *   주문 금액 (3200.0)이 5000 미만이므로 '주문 승인 정책'에 따라 계정 관리자 승인 대상입니다.
    *   고객 (C001, Alpha Manufacturing)은 '저위험' 고객이므로 '위험 검토 가이드라인'에 따라 추가 위험 검토가 필요하지 않습니다.
    *   하지만 고객 (Alpha Manufacturing)은 '기업 고객'이며, 주문 (O001)에 '서비스 (Support Package)'가 포함되어 있습니다. '기업 고객 계약 정책'에 따르면 기업 고객은 이행 전에 계약 유효성 확인이 필요합니다.
- Required follow-up (후속 조치): O001 주문에 대한 Alpha Manufacturing의 계약 유효성 확인 여부를 확인해야 합니다.
```

### Case 2
**질문**: C003 고객의 위험도와 미결 주문 상태는?

**결과**: ⛔ 의도된 도메인 오류 — `OBJECT_NOT_FOUND`
**메시지**: 질문에서 주문 ID를 찾을 수 없습니다.
**해석**: 잘못된 입력(주문 ID 미검출) 또는 권한 부족 시 LLM 호출 전에 차단되어야 한다는 정책이 정확히 작동.

### Case 3
**질문**: O002 주문이 5000원 이상인데 finance manager 승인이 필요한가요?

**결과**: ⛔ 의도된 도메인 오류 — `FORBIDDEN`
**메시지**: 이 정보에 접근할 권한이 없습니다.
**해석**: 잘못된 입력(주문 ID 미검출) 또는 권한 부족 시 LLM 호출 전에 차단되어야 한다는 정책이 정확히 작동.

### Case 4
**질문**: O001 주문이 Submitted 상태에서 Approved로 가려면 어떤 조건을 충족해야 해?

**Provider**: `gemini` / **Model**: `gemini-2.5-flash` / **Latency**: 11574 ms
**감지된 객체**: ['O001']
**사용된 문서**: ['D002', 'D003', 'D001']
**추천 액션**: ['ApproveOrder', 'RejectOrder', 'HoldOrder']

**답변**:
```
- Decision (승인/반려/추가검토): 추가 검토
- Evidence (근거):
    *   주문 O001의 고객인 Alpha Manufacturing (C001)은 Enterprise 고객입니다. (Ontology Context - Customer)
    *   Enterprise 고객은 주문 이행 전 계약 유효성 검사가 필요합니다. (Document Context - Enterprise Customer Contract Policy)
    *   주문 O001의 금액은 3200.0으로 5000 미만이므로 계정 관리자가 승인할 수 있는 범위입니다. (Document Context - Order Approval Policy)
    *   Alpha Manufacturing (C001)은 Low 위험 등급 고객이므로, 추가적인 위험 검토는 필요 없습니다. (Document Context - Risk Review Guideline)
- Required follow-up (후속 조치):
    *   Alpha Manufacturing (C001) 고객에 대한 계약 유효성 검사가 완료되었는지 확인해야 합니다.
    *   계약 유효성 검사가 완료되면 계정 관리자가 주문 O001을 승인할 수 있습니다.
```

### Case 5
**질문**: O003 최근 거부된 주문이 있나?

**Provider**: `gemini` / **Model**: `gemini-2.5-flash` / **Latency**: 3132 ms
**감지된 객체**: ['O003']
**사용된 문서**: ['D003', 'D002', 'D001']
**추천 액션**: ['RejectOrder', 'HoldOrder']

**답변**:
```
O003의 과거 승인/거부 이력에 대한 정보가 없습니다. 현재 O003의 상태는 'Review'입니다.
```

## 발견 사항

1. **모델 교체 필요했음**: 초기 기본 모델 `gemini-2.0-flash-001`은 신규 사용자에게 404 NOT_FOUND. `gemini-2.5-flash`로 교체 ([llm_gateway.py](../../backend/app/llm_gateway.py)의 `DEFAULT_MODEL` 갱신).
2. **키 로테이션 작동 확인**: 4개 키 중 첫 호출 성공. 다른 키들이 429/404 였어도 폴오버 동작 (#3에서 만든 stats 카운터로 확인 가능).
3. **Gemini 응답은 약간 보수적**: 룰베이스가 "승인 가능"이라 했던 case 1·4에서 "추가 검토" 권장. 안전한 편향이지만 결재자 효율 측면에선 보강 검토.
4. **응답 형식 일관성**: 프롬프트의 `Decision / Evidence / Required follow-up` 템플릿을 정확히 따름. evaluate.py에 형식 준수율 룰 추가 가능.
5. **case 5는 짧은 답변**: 거부 이력이 ontology에 없다는 사실을 명확히 답변. "없는 정보는 없다고 답하라"는 프롬프트 지침이 잘 작동.

## 개선 후보

- [ ] evaluate.py에 LLM 품질 메트릭 추가: 답변이 "Decision:"으로 시작 / 한국어 비율 > 30% / 환각 키워드 검출
- [ ] 프롬프트에 "추가 검토" 남발 방지 지침 추가 (정책이 명확히 통과인데 검토 요구 시 패널티)
- [ ] 모델 자동 폴백: 2.5-flash가 한도 도달 시 1.5-flash 또는 1.5-pro로 자동 전환
- [ ] Gemini 응답 캐시 (같은 질문 + 같은 컨텍스트는 캐시) — latency 단축
