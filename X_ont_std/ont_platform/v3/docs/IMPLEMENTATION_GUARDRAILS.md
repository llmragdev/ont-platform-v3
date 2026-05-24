# ont_platform v3 구현 가드레일

> **목적**: Kodex(04_2, 04_3, 04_4) + Antigravity(03) 기술 분석을 설계 문서에 반영  
> **작성일**: 2026-05-24  
> **상태**: Phase 2.5 (PostgreSQL 마이그레이션) 진행 중

---

## 1. 현황 진단 (Antigravity)

### 1-1. 파일 기반 구조의 태생적 한계

| 문제 | 현재 v3 | 영향 |
|------|--------|------|
| **Mock SPARQL** | 정규식 기반 (규격 미달) | 실무 쿼리 지원 불가 |
| **O(N) 성능** | 100K 엔티티에서 분 단위 | 1M 규모 불가능 |
| **레이스 컨디션** | 파일 동시 쓰기 충돌 | 다중 프로세스 위험 |
| **메모리 누적** | 트리플 메모리 보관 | 서버 재시작 시 손실 |
| **보안 위조** | HTTP Header 신뢰 | 테넌트 격리 무력화 |

**결론**: 파일 기반 구조는 프로토타입 수준이며, 엔터프라이즈 환경은 불가능.

### 1-2. 해결 방향 (Kodex)

**PostgreSQL 하이브리드 아키텍처**:
```
JSON 파일         →    PostgreSQL (실제 저장)
Mock SPARQL       →    rdflib (표준 준수)
파일 동시성       →    TX 격리 레벨
메모리 휘발성     →    JSONB 영속성
헤더 위조         →    JWT 서명
```

**효과**: 구현 난이도 1/10, 확장성 100배

---

## 2. SPARQL 구현 범위 제한 (Kodex 04_3)

### 2-1. 삼분할 전략

모든 SPARQL 쿼리를 다음 3가지로 분류:

#### Tier 1: Supported (SQL 직접 번역)
```sparql
SELECT ?name ?type WHERE {
  ?s rdf:type ?type ;
     dc:title ?name .
  FILTER (?type = ex:Person)
}
```
→ SQL로 직접 변환 가능 (조인 안 함)

**구현 대상**:
- 단순 FILTER (=, >, <, LIKE)
- 단일 TYPE 매칭
- 속성 프로젝션

#### Tier 2: Fallback (rdflib 실행)
```sparql
SELECT ?name WHERE {
  ?person foaf:knows+ ?friend .  # Property Path (전이 관계)
  ?friend foaf:name ?name .
}
```
→ SQL로 번역 불가, rdflib 메모리 실행

**구현 대상**:
- Property Path (foaf:knows+)
- UNION / OPTIONAL
- 복잡한 서브쿼리

#### Tier 3: Unsupported (에러 반환)
```sparql
CONSTRUCT { ?s ?p ?o }  # CONSTRUCT 쿼리
WHERE { ... }
```
→ 지원하지 않음, 명확한 에러 메시지

**규칙**: "Unsupported"는 명시적으로 끝내고, 사용자에게 Tier 1/2 대안 제시.

### 2-2. 구현 체크리스트

```python
# v3/src/backend/app/services/sparql_engine.py

class SPARQLProfile:
    """SPARQL 쿼리 분류 및 실행"""
    
    def classify(self, query: str) -> Tier:
        """
        Returns: 
          - Tier.SUPPORTED (SQL 번역 가능)
          - Tier.FALLBACK (rdflib 메모리 실행)
          - Tier.UNSUPPORTED (에러)
        """
        
        # 1. AST 파싱 (정규식 금지, rdflib 파서 사용)
        parsed = rdflib.plugin.get('sparql')
        ast = parsed.parseQuery(query)
        
        # 2. 패턴 매칭
        if _is_simple_select(ast) and _has_only_filters(ast):
            return Tier.SUPPORTED
        elif _has_property_path(ast) or _has_union(ast):
            return Tier.FALLBACK
        else:
            return Tier.UNSUPPORTED
```

---

## 3. PostgreSQL 인덱싱 전략 (Kodex 04_4)

### 3-1. 인덱스 설정

**❌ 틀린 방법**: GiST (느림)
```sql
CREATE INDEX ON entities USING GiST (properties jsonb_path_ops);
```

**✅ 올바른 방법**: GIN (빠름)
```sql
-- JSONB 검색 인덱스
CREATE INDEX idx_entities_properties_gin 
  ON entities USING GIN (properties jsonb_ops);

-- Expression 인덱스 (자주 사용하는 경로)
CREATE INDEX idx_entities_type 
  ON entities ((properties->>'type'));

-- 다중 필드 인덱스
CREATE INDEX idx_entities_lookup 
  ON entities (entity_type, domain_id, tenant_id);
```

### 3-2. 성능 검증

```bash
# 마이그레이션 전후 성능 비교
EXPLAIN ANALYZE
SELECT * FROM entities 
WHERE properties->>'category' = 'SHIP' 
AND tenant_id = 'company_a';

-- GiST: ~500ms
-- GIN:  ~50ms    ← 10배 빠름
```

---

## 4. 트랜잭션 안전성 (Kodex 04_4)

### 4-1. SAVEPOINT 패턴

**문제**: psycopg2에서 에러 발생 시 다음 쿼리가 전부 실패

```python
# ❌ 틀린 방법
cursor.execute("INSERT INTO entities ...")
cursor.execute("INSERT INTO relationships ...")  # 이전 에러로 실패
```

**✅ 올바른 방법**: SAVEPOINT 사용
```python
def write_entity(conn, entity):
    with conn:  # 자동 롤백
        try:
            with conn.cursor() as cur:
                # SAVEPOINT 생성
                cur.execute("SAVEPOINT sp_entity")
                
                # Entity 삽입
                cur.execute("""
                    INSERT INTO entities (id, properties, tenant_id)
                    VALUES (%s, %s, %s)
                """, (entity.id, json.dumps(entity.props), entity.tenant_id))
                
                # Relationship 삽입
                cur.execute("""
                    INSERT INTO relationships (from_id, to_id, type)
                    VALUES (%s, %s, %s)
                """, (entity.id, target_id, rel_type))
                
        except IntegrityError:
            cur.execute("ROLLBACK TO SAVEPOINT sp_entity")
            # 개별 실패 처리
```

### 4-2. 격리 레벨 설정

```python
# Phase 3 (Write-back) 시 REPEATABLE READ 권장
conn = psycopg2.connect(
    dbname="ontology_v3",
    user="ont_user",
    password=os.getenv("DB_PASSWORD")
)
conn.isolation_level = psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ
```

---

## 5. 안정적 ID 생성 (Kodex 04_4)

### 5-1. 현재 문제

```python
# ❌ 불안정한 ID 조합
rel_id = f"{from_id}_{to_id}_{rel_type}"
# 문제: 순서 바뀌거나 문자 추가 시 충돌 가능
```

### 5-2. 해결책

```python
import uuid
import hashlib

def generate_stable_id(from_id: str, to_id: str, rel_type: str) -> str:
    """안정적 관계 ID 생성 (해시 기반)"""
    
    # 방법 1: UUID5 (해시 기반, 결정론적)
    namespace = uuid.NAMESPACE_DNS
    key = f"{from_id}|{to_id}|{rel_type}"
    return str(uuid.uuid5(namespace, key))
    
    # 방법 2: SHA256 (더 짧음)
    import hashlib
    key = f"{from_id}|{to_id}|{rel_type}".encode()
    return hashlib.sha256(key).hexdigest()[:16]
```

**이점**:
- 순서 무관 (동일 입력 = 동일 ID)
- 충돌 가능성 극소 (2^128 또는 2^128)
- 재현 가능 (같은 관계 = 같은 ID)

---

## 6. 보안 강화: JWT 기반 인증 (Antigravity 04)

### 6-1. 문제 진단

```python
# ❌ 현재 (헤더 기반, 위조 가능)
@app.get("/api/entities")
async def list_entities(
    request: Request,
    tenant_id: str = Header(None)  # 사용자가 직접 전송
):
    # tenant_id를 그대로 신뢰 → 위조 가능!
    return ontology_service.list_all(tenant_id)
```

**공격 시나리오**:
```bash
# 회사 B의 사용자가 회사 A 데이터 접근
curl -H "X-Tenant-ID: company_a" \
     -H "X-Role: admin" \
     http://api/entities
```

### 6-2. JWT 기반 해결책

```python
import jwt
from datetime import datetime, timedelta

# 1. 로그인 엔드포인트 (토큰 발급)
@app.post("/api/login")
async def login(credentials: LoginRequest):
    user = authenticate(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401)
    
    # JWT 토큰 생성 (서명됨)
    token = jwt.encode(
        {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=24),
        },
        os.getenv("JWT_SECRET"),
        algorithm="HS256"
    )
    return {"access_token": token}

# 2. 인증 미들웨어 (모든 엔드포인트)
@app.middleware("http")
async def verify_jwt(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401)
    
    try:
        scheme, token = auth_header.split()
        if scheme != "Bearer":
            raise ValueError()
        
        # JWT 검증 (서명 확인)
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        
        # 요청에 사용자 정보 추가
        request.state.user_id = payload["sub"]
        request.state.tenant_id = payload["tenant_id"]
        request.state.role = payload["role"]
        
    except (jwt.InvalidSignatureError, jwt.ExpiredSignatureError):
        raise HTTPException(status_code=401, detail="Invalid token")

# 3. 엔드포인트 (JWT에서 tenant_id 추출)
@app.get("/api/entities")
async def list_entities(request: Request):
    # tenant_id를 요청에서 추출 (JWT 서명됨)
    tenant_id = request.state.tenant_id
    return ontology_service.list_all(tenant_id)
```

### 6-3. 체크리스트

```python
# ✅ 구현 항목
□ JWT 발급 엔드포인트 (/api/login)
□ JWT 검증 미들웨어 (모든 엔드포인트)
□ 권한 체크 데코레이터 (@require_role)
□ 토큰 만료 시간 (24시간 권장)
□ 비밀키 관리 (.env)
□ HTTPS 강제 (프로덕션)
```

---

## 7. 감사 로그 완전 추적 (Kodex 04_4)

### 7-1. 감사 로그 스키마

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(255),
    operation VARCHAR(50),  -- CREATE, UPDATE, DELETE, ACTION
    old_state JSONB,
    new_state JSONB,
    actor VARCHAR(255),     -- user_id
    timestamp TIMESTAMP DEFAULT NOW(),
    reason TEXT,            -- "승인 요청" / "자재 발주" 등
    sync_status VARCHAR(20) DEFAULT 'pending'  -- pending, synced, failed
);

CREATE INDEX idx_audit_entity ON audit_log(entity_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
```

### 7-2. 구현

```python
def audit_log(entity_id: str, operation: str, old_state: dict, 
              new_state: dict, actor: str, reason: str):
    """모든 변경 이력 기록"""
    
    conn.execute("""
        INSERT INTO audit_log 
        (entity_id, operation, old_state, new_state, actor, reason)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        entity_id,
        operation,
        json.dumps(old_state),
        json.dumps(new_state),
        actor,
        reason
    ))
```

---

## 8. 구현 우선순위 (Phase 2.5)

| 순위 | 항목 | 난이도 | 영향 | 기간 |
|------|------|--------|------|------|
| **1** | PostgreSQL 마이그레이션 | 높음 | 🔴 Critical | 1주 |
| **2** | GIN 인덱스 + 성능 검증 | 중간 | 🔴 Critical | 3일 |
| **3** | SAVEPOINT 트랜잭션 | 중간 | 🟠 High | 2일 |
| **4** | JWT 기반 인증 | 중간 | 🟠 High | 3일 |
| **5** | SPARQL 범위 제한 | 중간 | 🟡 Medium | 2일 |
| **6** | 감사 로그 완전화 | 낮음 | 🟡 Medium | 1일 |

**병렬 작업 가능**:
- PostgreSQL + GIN 인덱스 (동시)
- JWT 인증 (동시)
- SPARQL 분류 (동시)

---

## 9. 마이그레이션 검증

### 9-1. 성능 기준

```bash
# 마이그레이션 후 성능 검증
현재 (JSON):           PostgreSQL 후:
- 1K 엔티티: 10ms     → 1ms
- 10K:      100ms     → 5ms
- 100K:     1s        → 50ms
- 1M:       불가능    → 500ms ✅

목표: 100K 엔티티 < 200ms 달성
```

### 9-2. 데이터 무결성

```python
# 마이그레이션 전후 검증
def validate_migration(old_json_path, db_connection):
    # 1. 엔티티 수 비교
    json_count = count_json_files(old_json_path)
    db_count = db_connection.execute(
        "SELECT COUNT(*) FROM entities"
    ).fetchone()[0]
    assert json_count == db_count, "Entity count mismatch"
    
    # 2. 관계 무결성
    json_relations = load_all_relationships(old_json_path)
    db_relations = db_connection.execute(
        "SELECT COUNT(*) FROM relationships"
    ).fetchone()[0]
    assert len(json_relations) == db_relations, "Relationship count mismatch"
    
    # 3. 샘플 데이터 검증
    for entity_id in sample_entities:
        json_entity = load_from_json(entity_id)
        db_entity = fetch_from_db(entity_id)
        assert json_entity.properties == db_entity.properties
```

---

## 10. 참고 문서

- [Kodex 04_2: 온톨로지 재제안 (하이브리드 아키텍처)](../cross-source-comparison/04_2_클로드코드_온톨로지_재제안.md)
- [Kodex 04_3: 기술방향 제한제시 (SPARQL 범위)](../cross-source-comparison/04_3_kodex_경쟁분석_기술방향_제한제시.md)
- [Kodex 04_4: 구현 가드레일 상세](../cross-source-comparison/04_4_1_kodex_기술_방향_제한제시.md)
- [Antigravity 03: 현황 진단 (파일 기반 한계)](../cross-source-comparison/03_안티그래피티_ont_platform_분석.md)

---

**Status**: ✅ Phase 2.5 구현 가이드 완성  
**다음**: Phase 2.5 (2주) → Phase 3 (6월 시작)
