# Phase 5 지시서 검토 및 수정사항

**검토 일시**: 2026-05-25  
**상태**: ✅ 수정 완료

---

## 📋 주요 수정사항

### 1. ✅ Codex 환경 기준 업데이트 (v3 → v4)

**문제점**:
- Week 10, 11-12 Codex 지시서가 v3 기준 (포트 3002, npm test, antd)
- 현재 v4 프론트는 포트 3001, npm run build, Tailwind + 자체 UI 패턴

**수정사항**:
- `Week_10_OWL_Reasoning/Codex.md` 수정
  - 포트 3002 → 3001
  - npm test → npm run build, npm run lint, npm run cypress:run
  - antd 컴포넌트 → Tailwind CSS 기반으로 재구현

- `Week_11_12_Streaming_Production/Codex.md` 수정
  - antd Modal.confirm → window.confirm
  - antd message → alert 또는 toast notification
  - antd Button/Card 제거

---

### 2. ✅ 완료 체크 현실화

**문제점**:
- 모든 지시서의 성공 기준이 [x] (완료)로 되어있음
- 지시서는 실행 전 문서이므로 [ ] (미완료)가 맞음

**수정사항**:
- [ ] ✅ → [ ] 로 변경 (모든 주간 파일)
  - `Week_9_Automatic_Alignment/` (Claude, Codex, Antigravity)
  - `Week_10_OWL_Reasoning/` (Claude, Codex, Antigravity)
  - `Week_11_12_Streaming_Production/` (Claude, Codex, Antigravity)
  - `README.md` 산출물 체크리스트

---

### 3. ✅ 성과 목표 현실화

**문제점**:
- 1B triple < 30초 (Week 10 목표)
- 1B triple < 5분 (Week 12 목표)
- 99.9% SLA
- 이들은 "프로덕션 인증" 수준이며, 1주일 내 달성 불가능

**수정사항**:

#### PHASE5_Overview.md
- **Week 10**: 1B triple < 30초 → **1M~10M triple 처리 최적화** (Week 10 목표)
  - 1B는 **Phase 5 최종 stretch goal** (벤치마크 시나리오)
  
- **Week 12**: 1B triple < 5분, 99.9% SLA → **Production Readiness Candidate**
  - 실제 SLA 인증은 **Phase 6 운영 파일럿**으로 분리

#### README.md 성공 지표
| 지표 | 기존 | 수정됨 | 비고 |
|------|------|-------|------|
| 처리 규모 | 1B triple | 1M~10M (Week 10), 1B는 Phase 5 stretch goal | 벤치마크용 |
| 추론 완료 | < 30초 | - | stretch goal에 포함 |
| 응답 시간 (P95) | < 50ms | < 200ms (캐시 미스 포함) | 현실적 기준 |
| SLA | 99.9% | Production Readiness Candidate | Phase 6로 연기 |

---

### 4. ✅ OWL 추론 범위 제한

**문제점**:
- "OWL Level 2" 전체는 범위가 너무 큼
- 실제 구현 가능한 subset만 필요

**수정사항**:

#### Week_10_OWL_Reasoning/Claude.md
- **OWL 레벨 변경**: OWL-RL → OWL-Lite-Subset (기본값)
- **지원 규칙 명시**:
  - RDFS: subClassOf, subPropertyOf, domain, range
  - OWL: sameAs, inverseOf, TransitiveProperty
  - SKOS: broader, narrower, exactMatch, closeMatch
- **제외 규칙**: OWL DL, OWL Full의 복잡한 제약들

#### PHASE5_Overview.md
- "추론 능력: OWL Level 2" → **"RDFS + OWL subset + SKOS subset"**

---

### 5. ✅ 기술 의존성 분리

**문제점**:
- Kafka, Spark, Redis Cluster, GraphDB 모두 준비 단계 필수화
- 개발 진입 장벽이 너무 높음

**수정사항**:

#### README.md 준비 단계 재구성

**🟢 로컬 기본 환경** (Week 9-10 개발 필수)
- Conda 환경
- PostgreSQL
- Redis 단일 인스턴스
- Mock stream (Kafka 대체)

**🟡 고급 성능 환경** (Week 11 선택)
- Apache Kafka (선택)
- Spark 클러스터 4+ workers (선택)
- GraphDB (선택)

**🔴 대규모 검증 환경** (Week 12, Antigravity 전용)
- Distributed Spark cluster (8+ workers)
- Redis Cluster
- 프로덕션급 GraphDB

#### Antigravity 지시서 수정
- **Week 10 환경**: Spark 불필수, 로컬 개발 기준
- **선택 구간**: "[선택] Spark 분산 처리 (Week 12 대규모 벤치마크용)"

---

## 📊 수정 전후 비교

| 항목 | 기존 (과격) | 수정됨 (현실적) |
|------|-----------|-------------|
| **처리 규모** | 1B triple < 30초 | Week 10: 1M~10M, stretch goal: 1B |
| **OWL 추론** | OWL Level 2 전체 | RDFS + OWL subset + SKOS subset |
| **필수 기술** | Kafka, Spark, GraphDB, Redis Cluster 모두 | PostgreSQL + Redis 기본, 나머지 선택 |
| **SLA** | 99.9% (Week 12 완료) | Production Readiness Candidate (Phase 6 검증) |
| **Codex 기준** | v3 (antd, 포트 3002) | v4 (Tailwind, 포트 3001) |
| **체크리스트** | [x] (완료) | [ ] (미완료) |

---

## ⚠️ 영향 범위

### 에이전트 작업 기준
- **Week 9**: 변경 없음 (자동 매핑 범위 동일)
- **Week 10**: 1M~10M 규모 테스트 집중, Spark는 Week 12로 미연기
- **Week 11-12**: 
  - 기본 환경만으로 완료 가능
  - Spark/GraphDB는 "대규모 벤치마크" 섹션으로 분리

### 진입 장벽
- 기존: 모든 복잡 기술 필수 (개발 시작 어려움)
- **수정 후**: 로컬 PostgreSQL + Redis로 시작 가능 (쉬움)

---

## 🔍 검증 항목

다음 항목들은 Week 9 착수 전 최종 확인:

- [ ] Codex v4 환경이 실제 개발 환경과 일치하는지 확인
- [ ] mock stream 구현 계획 (Kafka 대체용)
- [ ] 1M~10M triple 테스트 데이터셋 준비
- [ ] RDFS + OWL subset의 구체적 범위 문서화
- [ ] gold set (자동 매핑 평가 데이터) 준비

---

## 💬 주요 변경 철학

1. **비전과 실행의 분리**:
   - Phase 5 비전: 1B triple, 자동화, 운영급 안정성
   - Phase 5 실행: 1M~10M, RDFS/OWL subset, 로컬 환경
   - 나머지는 Phase 6 또는 벤치마크 시나리오로 분리

2. **개발 진입성 우선**:
   - "모든 기술 필수" → "로컬 기본 + 선택 고급"
   - 첫 일주일 안에 개발 시작 가능하도록

3. **현실적 SLA 약속**:
   - "인증된 99.9% SLA"는 최소 한 달 운영 관측 필요
   - 현재 단계는 "모니터링 대시보드 + synthetic checks"

---

**다음 단계**: Week 9 착수 전 에이전트 팀과 최종 확인
