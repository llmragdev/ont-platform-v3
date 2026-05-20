# 댓글: Codex의 「클로드코드_완성_지시_가이드」

> 원문 출처: **Codex** (외부 평가자)
> 원문 위치: [../Codex의_claud에 대한 총평/클로드코드_완성_지시_가이드.md](../../../Codex의_claud에%20대한%20총평/클로드코드_완성_지시_가이드.md)
> 작성일: 2026-05-12
> 댓글 작성자: Claude (claud_통합 작업 담당)
> 성격: 분석 코멘트 (코드/문서 변경 없음, 작업 시작 전 사실관계와 위험 정리)
> 같은 폴더 참조: [Antigravity의_claud_integration_review_댓글.md](Antigravity의_claud_integration_review_댓글.md)

---

## 1. 이 문서의 정체

외부 평가자(Codex)가 작성한 **다음 단계 작업 지시서**. 현재 `claud_통합` 상태에 대해 "교육용 데모 → 설정 가능한 온톨로지 기반 워크플로우 콘솔"로 끌어올리라는 요구를 담고 있다.

## 2. 사실관계 점검 (Codex 인식 vs 실제 상태)

| Codex 인식 | 실제 우리 상태 | 비고 |
| --- | --- | --- |
| ✅ FastAPI + Next.js 통합 | 맞음 | — |
| ✅ 7개 도메인 서비스 분리 | 맞음 | — |
| ✅ pytest + scenarios + evaluate + E2E | 맞음 | 36/5/10/6 통과 |
| ✅ "JWT 백엔드, Repository, Docker, Telemetry 보강 흔적" | 맞음 | NEXT_STEPS #6~#9 |
| ❌ "온톨로지 스키마가 ontology.py에 하드코딩" | 사실 | — |
| ❌ "워크플로우 전이가 workflow.py에 하드코딩" | 사실 | — |
| ❌ "정책 조건이 코드 중심" | 사실 | — |
| ❌ "프론트 JWT 통합은 남은 작업" | 사실 | NEXT_STEPS #7b로 분리해둠 |
| ⚠ "문서가 루트 기준과 docs/ 기준 섞임" | **이미 해결됨** | Codex 작성 시점에 docs/ 분리 중이었을 듯 |
| ⚠ "PROGRESS.md의 17 passed 같은 오래된 문구" | **이미 36 passed로 갱신됨** | — |

결론: Codex의 진단은 대체로 정확. 다만 "문서 정합성" 지적은 작성 시점의 스냅샷이라 일부는 이미 해결된 상태.

## 3. 요구하는 작업의 본질

핵심은 **하드코딩 → 선언형 설정 이동**. 세 영역 모두 같은 패턴:

```
backend/app/ontology.py 의 _build_registry() 하드코딩
  → backend/config/ontology.default.json + JSON Schema

backend/app/workflow.py 의 _build_engine() 하드코딩
  → backend/config/workflow.order.json + JSON Schema

backend/app/policy.py 의 if amount < 5000, risk == "High" 하드코딩
  → backend/config/policy.default.json
```

단순 리팩토링이 아니라 **"관리자가 코드 수정 없이 비즈니스 규칙을 바꿀 수 있는 상태"**가 목표.

## 4. 우선순위 분석 (Codex 권장 8단계)

| 순서 | 항목 | 성격 | 사람 기준 / 내 기준 |
| --- | --- | --- | --- |
| 1 | 문서 정합성 정리 | 검증/정리 | 30분 / 이미 거의 완료 |
| 2 | 온톨로지 스키마 외부화 | 구조 변경 | 1일 / ~1시간 |
| 3 | 워크플로우 정의 외부화 | 구조 변경 | 1일 / ~1시간 |
| 4 | 정책 규칙 설정화 | 구조 변경 | 4시간 / ~40분 |
| 5 | 프론트 JWT 통합 | 풀스택 추가 | 1일 / ~1.5시간 |
| 6 | Gemini 실제 응답 평가 | 검증 | 30분 / **외부 의존 (키 한도)** |
| 7 | Repository·Docker 운영성 | 검증/보강 | 4시간 / ~30분 |
| 8 | 관측성·감사 로그 보강 | 보강 | 1일 / ~30분 |

**2~4번이 핵심**. 외부화 작업은 기존 API/E2E 깨질 위험이 있어 회귀 검증을 매 단계 돌려야 한다.

## 5. 위험 요소

| 영역 | 위험 | 완화 방안 |
| --- | --- | --- |
| 온톨로지 외부화 | OntologyService 생성자 시그니처 변화 → 11 테스트 + scenarios + evaluate 전체 영향 | 기본 설정을 `fresh_raw_data()`와 동일하게 만들어 회귀 없이 시작 |
| 워크플로우 외부화 | `condition_key` → PolicyEngine 함수 매핑 설계 난이도 | 조건을 표현식 언어(`amount<5000 and risk!="High"`)로 둘지, 명명된 함수 키로 둘지 사전 결정 필요 |
| 정책 외부화 | 4가지(금액·역할·리스크·지역)가 얽혀 있어 일부만 외부화하면 복잡도 증가 | 한 번에 다 외부화하거나, 임계값만 분리하는 식으로 명확히 선택 |
| 프론트 JWT | 사용자 셀렉터 UX와 충돌. 셀렉터 제거 vs "데모 모드"로 명시 결정 필요 | 현재 셀렉터는 교육 시나리오의 핵심이라 **유지 + 셀렉터 변경 시 JWT 자동 발급** 권장 |
| Gemini 실제 평가 | API 키 한도 회복이 외부 의존 | 회복 안 되면 1~2건 수동 캡처로 `LLM_EVAL.md` 만드는 식으로 우회 |

## 6. 모호함 / 사전 결정 필요한 지점

Codex 가이드가 명시하지 않아 우리가 결정해야 하는 것:

1. **워크플로우 조건 표현법**
   - 옵션 A: `condition_key: "policy_allows"` (간단, 함수 매핑)
   - 옵션 B: `condition: "amount<5000 AND risk!=High"` (선언형 표현식, 미니 파서 필요)

2. **JSON Schema 강제 정도**
   - 옵션 A: 단순 dict 로딩 + Pydantic 검증
   - 옵션 B: 별도 `*.schema.json` 파일로 외부 도구(`ajv` 등) 검증 가능

3. **설정 파일 위치**
   - Codex는 `backend/config/` 권장 (코드와 함께 버전 관리)
   - 대안: `backend/data/` (런타임 데이터 영역)

4. **정책 외부화 범위**
   - 임계값(5000, 역할 목록)만 분리할지
   - 전체 분기 로직(`can_execute_action`)까지 분리할지

5. **프론트 JWT 도입 시 셀렉터 처리**
   - 제거 / "데모 모드" 토글로 유지 / "관리자가 사용자 가장(impersonate)" 형태

## 7. 현재 NEXT_STEPS.md 와의 차이

`claud_통합/docs/NEXT_STEPS.md`에 남아 있는 항목:
- #2 Gemini 답변 검증 ⏸
- #7b 프론트 JWT 통합

Codex 가이드가 새로 요구하는 항목 (5개):
- 온톨로지 외부화 (가이드 §3.1)
- 워크플로우 외부화 (가이드 §3.2)
- 정책 설정화 (가이드 §3.3)
- Repository 운영성 보강 (§5.1)
- 관측성·감사 로그 보강 (§5.2)

→ 작업 진행 시 NEXT_STEPS.md에 5건 추가 필요.

## 8. 추천 진행 전략 (분석 결과)

작업한다고 가정할 때 합리적 순서:

```
[A] 문서 정합성 점검 (이미 거의 됨, 5분 확인만)
 ↓
[B] 정책 외부화부터 시작 (가장 작은 변화, 회귀 위험 낮음)
 ↓
[C] 워크플로우 외부화 (B 결과로 condition 키 인터페이스 확정 후)
 ↓
[D] 온톨로지 외부화 (가장 큰 변화이지만 마지막에 하면 안전)
 ↓
[E] 회귀 검증 (pytest + scenarios + evaluate + Playwright)
 ↓
[F] 프론트 JWT 통합 (별도 풀스택 작업)
 ↓
[G] Gemini 검증 (외부 의존)
 ↓
[H] Repository / 관측성 보강 (마무리)
```

Codex 권장 순서(온톨로지 → 워크플로우 → 정책)와 반대. 이유:
- 정책이 가장 작은 변화 → 회귀 위험 낮음
- Codex 순서는 "이후 모든 운영성 개선의 기반"이라는 논리이지만, 설정 파일 인터페이스를 정책에서 먼저 확정하면 나머지가 따라옴

## 9. 명확한 한 가지 권고

분석 단계에서 보이는 명백한 사실:
**Codex가 요구한 "문서 정합성 정리"는 이미 docs/ 분리 + FINAL_REPORT.md 작성으로 거의 끝낸 상태.** Codex 검증 시점(2026-05-12 17 passed)과 그 후 우리 작업(36 passed + docs/ 분리)이 엇갈렸을 뿐이다. 다시 손댈 부분은 README의 일부 표현이 36/5/10/6 카운트와 일치하는지 한 번 확인하는 정도.

## 10. 작업 시작 전 권장 단계

1. 가이드의 8단계 우선순위에 대해 사용자 합의 (Codex 순서 따를지, 위 §8의 대안 순서로 갈지)
2. §6의 모호한 결정 5건에 대한 사전 답변 확보
3. 새 NEXT_STEPS 항목 5건 추가
4. 그 후 첫 항목(정책 또는 온톨로지) 착수

---

## 별첨: Codex 가이드 §8의 짧은 지시문에 대해

가이드 마지막에 "클로드 코드에 전달할 짧은 지시문"이 있다:

```
... 모든 변경 후 backend pytest, eval.scenarios, evaluate.py, frontend build, Playwright E2E를 실행해서
결과를 docs/PROGRESS.md와 docs/CHANGELOG.md에 반영해줘.
```

→ 이 회귀 검증 묶음은 우리도 이미 자율 모드에서 따르고 있던 패턴. 그대로 진행하면 자연스럽게 일치.
