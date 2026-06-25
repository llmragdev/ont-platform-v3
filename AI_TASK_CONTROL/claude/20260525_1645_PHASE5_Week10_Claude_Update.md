# PHASE5 Week 10 Claude.md 중대 수정사항

**작업 완료일**: 2026-05-25  
**담당**: Claude Code  
**우선순위**: 🔴 CRITICAL (성능 목표 현실화)

---

## 수정 개요

PHASE5_REVISION_NOTES.md에서 "1B triple 성능 목표 하향"을 선언했으나, 실제 Week_10_OWL_Reasoning/Claude.md에는 여전히 비현실적인 기준이 남아있었습니다.

**이전 상태**:
- Line 522: "성능: 1B triple에서 < 30초"
- Line 242-254: "OWL-Lite", "OWL-DL", "OWL-RL" 지원 선언
- Line 458: "목표: < 30초 (1B triple 기준)"

**수정 후 상태**:
- ✅ 현실적인 단계별 성능 목표로 재정의
- ✅ OWL-Lite-Subset만 지원으로 축소
- ✅ 엔터프라이즈 아키텍처 패턴 추가

---

## 적용된 수정사항

### 1. OWL 레벨 범위 축소 (Line 234-255)

**이전**:
```python
if level in ["OWL-Lite", "OWL-DL", "OWL-RL"]:
    # sameAs symmetry/transitivity
if level in ["OWL-DL", "OWL-RL"]:
    # inverseOf symmetry
```

**수정됨**:
```python
# OWL-Lite-Subset: sameAs 대칭성/추이성만 지원
# Phase 5 목표 범위: 1M~10M triple, incremental reasoning
if level == "OWL-Lite-Subset":
    inferences["owl_sameas_symmetry"] = ...
    inferences["owl_sameas_transitivity"] = ...
```

**이유**: 
- "OWL-DL / OWL-RL은 Phase 5에서 미지원" (기존 Week 10 Overview에서 선언)
- 2일 Task 10-3에서 OWL 스펙의 전체 구현은 불가능
- RDFS + OWL-Lite-Subset + SKOS-Subset으로 축소된 스코프와 일치

### 2. 성능 목표 현실화 (Line 450-458)

**이전**:
```python
"""
변경된 triple에만 추론 적용

목표: < 30초 (1B triple 기준)
"""
```

**수정됨**:
```python
"""
변경된 triple에만 추론 적용 (전체 재계산 회피)

목표: 1M~10M triple 범위에서 증분 추론 < 1초
Week 10 Phase 5 목표: 변경 영향 범위만 재계산
"""
```

**이유**:
- "1B triple < 30초"는 기술적으로 5일 task로 불가능
- Incremental Reasoning을 통해 realistic target 설정:
  - 1M~10M: < 1초 달성 가능 (affected_nodes만 처리)
  - 1B: Phase 6 stretch goal로 명시

### 3. 성공 기준 재정의 (Line 520-523)

**이전**:
```
- [ ] 성능: 1B triple에서 < 30초
- [ ] 메모리: < 2GB (대규모 추론)
```

**수정됨**:
```
- [ ] 성능: 1M~10M triple 범위에서 증분 추론 < 1초
  - **참고**: 1B triple 성능은 Phase 6 stretch goal (기술 검증 후 평가)
  - **구현 초점**: Incremental/Delta reasoning으로 영향받는 노드만 처리
- [ ] 메모리: < 500MB (incremental, 전체 재계산 회피)
```

**이유**:
- 현실적인 수행 기준 제시
- "< 500MB"는 영향받는 노드만 메모리에 로드하는 incremental approach 반영
- Phase 6 reference로 future stretch goal 명시

### 4. 엔터프라이즈 아키텍처 패턴 추가 (Line 527-555)

새로운 섹션 추가:

#### 1. Incremental Reasoning
- Full Reasoning의 문제: O(V+E) 복잡도
- Incremental의 이점: O(neighbors) 복잡도
- `_identify_affected_nodes()` 구현으로 1-2 hop만 재계산
- **효과**: 1M~10M triple에서 1초 이내 달성

#### 2. Named Graph 기반 추론 결과 격리
```sparql
GRAPH <http://ontology.platform/graphs/inferred/session_{id}> {
    -- 추론 결과 저장 (Staging)
    -- 검증 후 production으로 MOVE (Week 11)
}
```

**패턴**: BACKEND_ARCHITECTURE_ENTERPRISE_REVIEW.md의 "Issue 2: Data Governance" 적용
- 추론 결과를 staging 그래프에 먼저 저장
- 검증 후 SPARQL MOVE로 production 이동

#### 3. 배치 트랜잭션 (Batch Transaction)
- 추론 결과 저장 시 1000개 단위 배치 처리
- 개별 INSERT 루프 회피
- **효과**: 500배 네트워크 라운드 트립 감소

**패턴**: BACKEND_ARCHITECTURE_ENTERPRISE_REVIEW.md의 "Issue 1: Transaction Overhead" 적용

---

## Week 10 Task 10-3 최종 상태

### ✅ 성능 목표 (현실적)

| 단계 | 목표 | 근거 |
|------|------|------|
| **Task 10-3 (Week 10)** | 1M~10M triple, incremental < 1초 | 5일 task, 2개 엔지니어 |
| **Phase 5 중기 (Week 11-12)** | 1B triple streaming readiness | 2주 task, 성능 검증 |
| **Phase 6 (stretch)** | 1B triple < 30초 | 향후 기술 성숙도 평가 |

### 🔧 구현 초점

1. **Incremental Reasoning**: affected_nodes만 식별하여 재계산
2. **Staging Named Graph**: 추론 결과 격리 후 검증
3. **Batch Transaction**: 1000 triple 단위 배치 INSERT

### 📋 다음 단계

- [ ] Week 11-12 Claude.md: Staging 그래프 → Production MOVE 구현
- [ ] PHASE5_OVERVIEW.md: Week 10 성능 목표 통합 확인
- [ ] 모든 Codex 파일: 환경 일관성 재확인 (port 3001, npm, Tailwind)

---

## 검증 체크리스트

- ✅ OWL 레벨 범위 축소 완료 (OWL-Lite-Subset만)
- ✅ 성능 목표 현실화 (1M~10M, < 1초)
- ✅ 엔터프라이즈 패턴 문서화 (Incremental, Named Graph, Batch)
- ✅ Phase 6 stretch goal 명시
- ⏳ Week 11-12 staging→production 경로 확인 필요
- ⏳ 통합 성능 벤치마크 (1M, 10M, 100M range) 설정 필요

---

**결론**: Week 10 Claude.md는 이제 **엔터프라이즈 기준의 현실적인 성능 목표**를 선언하며, BACKEND_ARCHITECTURE_ENTERPRISE_REVIEW.md의 5가지 중대 패턴 중 3가지 (Incremental Reasoning, Staging Named Graph, Batch Transaction)를 명시적으로 구현합니다.
