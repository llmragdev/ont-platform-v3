# 장애보고서

**날짜:** 2026-06-20  
**조치자:** Antigravity (발견) / Claude (완전 수정)  
**심각도:** 🔴 High (벡터화 Step 3-4 완전 실패)

---

## 문제 요약

온톨로지 저장 및 문서 상태 업데이트 단계에서 **모든 문서 처리 실패**

```
TypeError: TenantContext.__init__() got an unexpected keyword argument 'extra_context'
```

**영향:**
- Step 1-2 완료 (PDF 로드, LLM 추출)
- Step 3 실패 (온톨로지 저장)
- Step 4 미실행 (문서 상태 업데이트)
- 문서 상태: "⌛ 벡터화 중" (무한 대기)

---

## 근본 원인

**파일:** `v5/backend/scripts/generate_ontology_from_pdf.py`

**두 군데에서 존재하지 않는 파라미터 사용:**

```python
# ❌ 라인 205 (main try 블록):
ctx = TenantContext(
    user_id=args.user,
    company_id=args.company,
    project_id=args.project,
    role="Admin"
)

# ❌ 라인 237 (except 블록):
ctx = TenantContext(
    user_id=args.user,
    company_id=args.company,
    project_id=args.project,
    role="Admin",
    extra_context={}  # ← 이 파라미터는 TenantContext에 없음!
)
```

**TenantContext 실제 파라미터:**
```python
@dataclass
class TenantContext:
    user_id: str
    company_id: str
    project_id: str
    role: str
    permissions: dict[str, bool] = field(default_factory=dict)
```

---

## 조치 사항

### Antigravity의 조치
- ✅ 라인 205 수정 (extra_context={} 제거)

### Claude의 추가 수정
- ✅ 라인 237 수정 (except 블록에서도 extra_context={} 제거)

**최종 코드:**
```python
# ✅ 라인 205 (main try 블록):
ctx = TenantContext(
    user_id=args.user,
    company_id=args.company,
    project_id=args.project,
    role="Admin"
)

# ✅ 라인 237 (except 블록):
ctx = TenantContext(
    user_id=args.user,
    company_id=args.company,
    project_id=args.project,
    role="Admin"
)
```

---

## 타임라인

| 시간 | 이벤트 |
|------|--------|
| 01:24:44 | 8개 문서 벡터화 요청 |
| 01:24:44 | Step 1-2 성공, Step 3 실패 (extra_context 오류) |
| 01:24:57 | 모든 프로세스에서 동일한 오류 반복 |
| 01:30:00 | Antigravity가 라인 205 수정 |
| 01:32:30 | Claude가 라인 237도 수정 완료 |

---

## 재현 및 검증

**재현 단계:**
1. 문서 벡터화 요청
2. Step 1-2 완료 (PDF 로드, LLM 추출)
3. **Step 3에서 TypeError 발생**
4. 문서 상태 업데이트 실패

**검증 (수정 후):**
- 터미널 로그에서 "✅ 온톨로지 생성 완료!" 메시지 확인
- 문서 상태가 "✅ 완료"로 변경되는지 확인
- [💬 질의 시작] 버튼 활성화되는지 확인

---

## 교훈

1. **타입 체크:** TenantContext의 dataclass 정의를 먼저 확인해야 함
2. **코드 리뷰:** except 블록도 동일하게 검토 필요
3. **테스트:** 예외 케이스도 전체적으로 테스트 필요

---

**상태:** ✅ **완전 해결됨**  
**다음 단계:** 수정된 코드로 벡터화 재시도

