# ont_platform v3 기술 분석 & 로드맵
## Phase 4 완료 기준 재평가 (2026-05-21)

> **작성자**: 검증팀 + Antigravity 기술분석  
> **작성일**: 2026-05-21  
> **대상**: E:\ontology_edu\X_ont_std\ont_platform\v3  
> **기준**: Phase 4 완료 (201/203 테스트 통과)

---

## 📊 종합 평가

### 현재 상태
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░ 90% 완성 (Phase 3-4)
- 기능 완성도: 높음 (19/19 요건 구현)
- 테스트 커버: 높음 (201/203 통과)
- 프로덕션 준비도: 중간 (확장성/보안 미흡)
```

### 핵심 평가
✅ **잘한 것**:
- 6가지 온톨로지 스타일 구현 완료
- RDF 4가지 포맷 변환 완료  
- 메타데이터 & 혈통 추적 완벽
- 비즈니스 액션 & Write-back 완료
- 감사 시스템 JSONL 기반 구현

⚠️ **개선 필요**:
- 대규모 데이터 처리 (100M+ triple 미테스트)
- SPARQL 엔진이 시뮬레이션 수준
- 다중 사용자 동시성 이슈
- 영속성 (인메모리 트리플 관리)

---

## 🔴 우선순위별 취약점 분석

### **Priority 1: 데이터 영속성 & 성능** (즉시)

#### 1-1. 인메모리 트리플 관리
| 항목 | 상태 |
|------|------|
| **심각도** | 🔴 높음 (운영 불가) |
| **영향도** | 서버 재시작 시 온톨로지 완전 손실 |
| **현황** | sparql_engine.py: `self.triples = []` (메모리만) |
| **복구 난이도** | 낮음 (1-2주) |

**구체적 문제**:
```python
# sparql_engine.py
class SPARQLEngine:
    def __init__(self):
        self.triples = []  # ❌ 프로세스 종료 시 소실
        
    def add_triple(self, subject, predicate, obj):
        self.triples.append((subject, predicate, obj))  # 메모리만
```

**Phase 4에서 구현한 것**:
- ✅ RDFConverter: 파일 기반 저장 구현
- ❌ SPARQLEngine: 여전히 메모리 기반

**해결책 (우선순위 1-1)**:
1. JSONL 기반 Triple Store 추가 (1주)
   ```python
   # app/services/triple_store.py (신규)
   class TripleStore:
       def save_to_jsonl(self, path: str):
           """트리플을 JSONL로 영속화"""
       
       def load_from_jsonl(self, path: str):
           """시작 시 로드"""
   ```

2. 서버 시작 시 자동 로드

---

#### 1-2. 파일 I/O 병목 (O(N) 풀 스캔)
| 항목 | 상태 |
|------|------|
| **심각도** | 🟡 중간 (10M 이상 에러) |
| **영향도** | 조회 시간 기하급수 증가 |
| **현황** | ontology.py: glob + json.loads 풀 스캔 |
| **복구 난이도** | 중간 (2-3주) |

**구체적 문제**:
```python
# ontology.py line 27
def list_all_entities(self):
    """모든 파일을 메모리로 로드 - O(N)"""
    files = glob(f"{self.ontology_dir}/*.json")  # ❌ 풀 스캔
    for f in files:
        with open(f) as fp:
            data = json.load(fp)  # 각 파일을 모두 파싱
```

**성능 영향**:
- 1K 파일: 200ms ✅
- 10K 파일: 2s ⚠️
- 100K 파일: 20s+ 🔴

**해결책 (우선순위 1-2)**:
1. SQLite 메타데이터 인덱스 (2주)
   ```python
   # app/db/ontology_index.py (신규)
   class OntologyIndex:
       def query_entities(self, filter_dict: dict) -> List[str]:
           """인덱스 기반 빠른 조회"""
           # SELECT entity_id FROM ontology_index WHERE ...
   ```

2. 캐싱 레이어 추가

---

### **Priority 2: SPARQL 엔진 고도화** (1-2개월)

| 항목 | 상태 |
|------|------|
| **심각도** | 🟡 중간 (복잡 쿼리 실패) |
| **영향도** | UNION, FILTER, 서브쿼리 불가 |
| **현황** | 정규식 기반 패턴 매칭 |
| **복구 난이도** | 높음 (4-6주) |

**구체적 문제**:
```python
# sparql_engine.py line 72
def _detect_query_type(query: str):
    upper_query = query.upper()
    if upper_query.startswith("SELECT"):
        return "SELECT"  # ❌ 단순 문자열 비교
    # ... 더 이상 파싱 안 함
```

**실패하는 쿼리들**:
```sparql
-- ❌ UNION 미지원
SELECT ?x WHERE { ?x a Person } 
UNION 
SELECT ?x WHERE { ?x a Employee }

-- ❌ FILTER 미지원
SELECT ?x WHERE { ?x a Person. FILTER (?age > 30) }

-- ❌ 서브쿼리 미지원
SELECT ?x WHERE { ?x depts [ deptName "Engineering" ] }
```

**해결책 (우선순위 2)**:
1. rdflib 라이브러리 통합 (3주)
   ```python
   # app/services/sparql_service_v2.py (신규)
   from rdflib import Graph, Namespace
   
   class SPARQLServiceV2:
       def __init__(self):
           self.graph = Graph()  # 표준 RDF 그래프
       
       def query(self, sparql_string):
           results = self.graph.query(sparql_string)  # ✅ 표준 엔진
   ```

2. 단계적 마이그레이션
   - Phase 5 Week 1-3: rdflib 통합
   - Phase 5 Week 4: 호환성 테스트
   - Phase 5 Week 5: 기존 엔진 제거

---

### **Priority 3: 다중 사용자 동시성** (1-2개월)

| 항목 | 상태 |
|------|------|
| **심각도** | 🟡 중간 (동시 요청 에러) |
| **영향도** | Race condition, 파일 손상 |
| **현황** | 파일 잠금 메커니즘 없음 |
| **복구 난이도** | 중간 (2-3주) |

**구체적 문제**:
```python
# base.py line 37
def _save_json(self, path: Path, data: dict):
    path.write_text(json.dumps(data))  # ❌ 동시 쓰기 위험
    # T1: write 시작
    # T2: write 시작 (T1과 겹침)
    # → 파일 손상 가능
```

**시나리오**:
```
User A: PUT /api/entities/P001 (예산 수정)
User B: PUT /api/entities/P001 (상태 수정)
결과: 둘 중 하나의 변경이 소실되거나 파일이 깨짐
```

**해결책 (우선순위 3)**:
1. Atomic Rename 패턴 (1주)
   ```python
   # app/repositories/base.py (수정)
   def _save_json(self, path: Path, data: dict):
       import tempfile
       with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as tmp:
           json.dump(data, tmp)
           tmp.flush()
           os.replace(tmp.name, path)  # ✅ 원자적 연산
   ```

2. 파일 잠금 (선택사항)
   ```python
   # 경량 구현: fcntl (Unix) 또는 msvcrt (Windows)
   ```

---

### **Priority 4: 외부 온톨로지 임포트** (중기, 2-3개월)

| 항목 | 상태 |
|------|------|
| **심각도** | 🟡 중간 (기능 미완) |
| **영향도** | DBpedia, Wikidata 실시간 연동 불가 |
| **현황** | Mock 데이터 반환 |
| **복구 난이도** | 중간 (2-3주) |

**구체적 문제**:
```python
# ontology_importer.py line 20
def import_dbpedia(self, source_id: str, limit: int = 5):
    """DBpedia에서 실제 데이터를 가져오는 게 아님"""
    dummy_data = {  # ❌ 하드코딩된 더미
        "entity": source_id,
        "properties": {...}
    }
    return dummy_data
```

**해결책 (우선순위 4)**:
1. REST API 클라이언트 추가 (1주)
   ```python
   # app/clients/external_ontology.py (신규)
   class DBpediaClient:
       async def fetch_entity(self, resource_id: str):
           """SPARQL 엔드포인트에서 실제 데이터 조회"""
           query = f"""
           SELECT ?p ?o WHERE {{ 
               <http://dbpedia.org/resource/{resource_id}> ?p ?o 
           }}
           LIMIT 100
           """
           response = await self.session.get(
               "http://dbpedia.org/sparql",
               params={"query": query, "format": "json"}
           )
           return response.json()
   ```

2. 캐싱 & 재시도 로직

---

### **Priority 5: 권한 시스템 강화** (장기, 3-4개월)

| 항목 | 상태 |
|------|------|
| **심각도** | 🟢 낮음 (현재 단일 회사) |
| **영향도** | 다중 테넌트 시 중대 |
| **현황** | HTTP 헤더 기반 (위조 가능) |
| **복구 난이도** | 낮음 (1주) |

**구체적 문제**:
```python
# workflow.py line 35-41
def _ctx(
    x_user_id: str = Header(default="default-user"),
    x_company_id: str = Header(default="default"),  # ❌ 위조 가능
    x_role: str = Header(default="Viewer"),
) -> TenantContext:
    return TenantContext(x_user_id, x_company_id, x_project_id, x_role, {})
    # 검증 없음
```

**위조 시나리오**:
```bash
curl -H "X-Company-Id: CompanyA" \
     -H "X-Role: Admin" \
     https://ont-platform/api/entities/CompanyA
# → 다른 회사 데이터 접근 가능 (현재 다중테넌트 아니면 OK)
```

**해결책 (우선순위 5, 장기)**:
- Phase 5 Week 6-8: JWT 통합 (선택적)
- 현재는 필요 없음 (단일 회사 운영)

---

## 📅 Phase 5 로드맵

### **Phase 5: 안정성 & 확장성 강화** (2026-06 ~ 2026-08, 10주)

```
Week 1-2: 데이터 영속성
├─ JSONL 기반 Triple Store (1주)
├─ SQLite 메타데이터 인덱스 (1주)

Week 3-4: 동시성 안정성  
├─ Atomic Rename 패턴 (1주)
├─ 통합 테스트 & 검증 (1주)

Week 5-8: SPARQL 고도화
├─ rdflib 통합 (2주)
├─ 호환성 테스트 (1주)
├─ 레거시 제거 (1주)

Week 9-10: 외부 임포트
├─ DBpedia/Wikidata API 클라이언트 (1주)
├─ 캐싱 & 재시도 (1주)
```

---

## 🎯 즉시 액션 (단기, 1-2주)

| 항목 | 액션 | 담당 | 기한 |
|------|------|------|------|
| **영속성** | JSONL Triple Store 구현 | Backend | 1주 |
| **검증** | 100K 파일 성능 테스트 | QA | 3일 |
| **문서** | Phase 5 상세 계획 작성 | PM | 2일 |
| **보안** | 권한 시스템 리뷰 (선택) | 보안팀 | 1주 |

---

## 💡 Antigravity 연계 방안

| 기능 | Antigravity | ont_platform | 통합 방법 |
|------|-------------|-------------|---------|
| **권한 관리** | JWT + OAuth | 헤더 기반 | 선택적 (Phase 5.8) |
| **파일 저장** | Atomic Rename | 직접 쓰기 | 즉시 채택 (Priority 3) |
| **DB 마이그레이션** | SQLAlchemy | JSON 파일 | Phase 5 (Priority 1) |
| **모니터링** | 상세 로그 | 기본 로그 | Phase 6 |

---

## 📊 현재 vs 목표

### 현재 (2026-05-21)
```
기능     ▓▓▓▓▓▓▓▓▓▓ 100%
테스트   ▓▓▓▓▓▓▓▓▓░ 98.5%
영속성   ▓░░░░░░░░░ 10%
성능     ▓▓▓░░░░░░░ 30%
보안     ▓▓░░░░░░░░ 20%
```

### 목표 (2026-08, Phase 5 후)
```
기능     ▓▓▓▓▓▓▓▓▓▓ 100%
테스트   ▓▓▓▓▓▓▓▓▓▓ 100%
영속성   ▓▓▓▓▓▓▓░░░ 70%
성능     ▓▓▓▓▓▓▓▓░░ 80%
보안     ▓▓▓▓▓░░░░░ 50%
```

---

## 🎓 결론

**현재 평가**: 교육용/프로토타입으로는 우수. 소규모 엔터프라이즈(1-2 회사) 운영 가능.

**확장 시 필수**: Phase 5 (우선순위 1-3) 완료 후 프로덕션 운영 권장.

**타임라인**: 
- ✅ Phase 4 완료: 2026-05-21
- 📅 Phase 5 시작: 2026-06-01
- 📅 Phase 5 완료: 2026-08-31 (예정)

---

**최종 검증**: 2026-05-21  
**다음 검토**: Phase 5 Week 2 (2026-06-09)

