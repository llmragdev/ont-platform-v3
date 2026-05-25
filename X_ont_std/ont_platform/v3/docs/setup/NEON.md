# Neon.tech PostgreSQL 환경 설정 가이드

> **프로젝트**: ont_platform v3  
> **데이터베이스**: Neon.tech PostgreSQL  
> **설정일**: 2026-05-24  

---

## 🎯 빠른 시작 (5분)

### 1단계: 환경 파일 준비

```bash
# .env.neon 파일 이미 생성됨 (확인)
cat .env.neon

# 출력 예:
# DATABASE_URL=postgresql://neondb_owner:npg_Z4XO3lMLGyRs@ep-muddy-moon-aobi6rvr...
# DB_HOST=ep-muddy-moon-aobi6rvr-pooler.c-2.ap-southeast-1.aws.neon.tech
```

### 2단계: 스키마 생성

```bash
# Python 초기화 스크립트 실행
python scripts/setup_database.py

# 출력 예:
# 🔌 Neon.tech PostgreSQL 연결 중...
# ✅ 연결 성공!
# 📄 SQL 파일 실행: init_schema.sql
# ✅ init_schema.sql 실행 완료
# 🔍 스키마 검증 중...
# ✅ 테이블 (5개):
#    - entities: 1 rows
#    - relationships: 0 rows
#    - audit_log: 0 rows
#    - ontology_metadata: 1 rows
```

### 3단계: 환경 변수 활성화

```bash
# .env.neon을 .env로 복사
cp .env.neon .env

# 또는 PowerShell
Copy-Item .env.neon .env
```

---

## 📋 설정 정보

### Neon.tech 프로젝트 정보

| 항목 | 값 |
|------|-----|
| **프로젝트** | ont_platform |
| **데이터베이스** | ont_db |
| **사용자** | neondb_owner |
| **호스트** | ep-muddy-moon-aobi6rvr-pooler.c-2.ap-southeast-1.aws.neon.tech |
| **리전** | ap-southeast-1 (싱가포르) |
| **SSL** | 필수 (sslmode=require) |

### 연결 문자열

```
postgresql://neondb_owner:npg_Z4XO3lMLGyRs@ep-muddy-moon-aobi6rvr-pooler.c-2.ap-southeast-1.aws.neon.tech/ont_db?sslmode=require&channel_binding=require
```

---

## 🗃️ 생성된 스키마

### 테이블 (5개)

```sql
1. entities (엔티티 저장)
   - id: VARCHAR(255) PRIMARY KEY
   - entity_type: VARCHAR(100)
   - domain_id: VARCHAR(100)
   - properties: JSONB
   - version: INT (낙관적 잠금)
   - created_at, updated_at: TIMESTAMP

2. relationships (관계 저장)
   - id: VARCHAR(255) PRIMARY KEY
   - from_entity_id, to_entity_id: FK to entities
   - relation_type: VARCHAR(100)
   - properties: JSONB
   - weight: DECIMAL(10,2)

3. audit_log (감사 추적)
   - id: SERIAL PRIMARY KEY
   - domain_id, entity_id: VARCHAR
   - operation: VARCHAR (INSERT/UPDATE/DELETE/QUERY)
   - old_state, new_state: JSONB
   - actor, actor_ip: VARCHAR
   - timestamp: TIMESTAMP

4. ontology_metadata (메타데이터)
   - domain_id: VARCHAR(100) PRIMARY KEY
   - entity_count, relationship_count: INT
   - ontology_version, schema_version: VARCHAR/INT

5. ontology_triples (VIEW)
   - 엔티티 속성 + 관계를 RDF 트리플 형태로 시뮬레이션
```

### 인덱스 (12개)

```
entities:
├─ idx_entities_type
├─ idx_entities_domain
├─ idx_entities_doc
├─ idx_entities_properties (GiST)
└─ idx_entities_created

relationships:
├─ idx_relationships_from
├─ idx_relationships_to
├─ idx_relationships_type
├─ idx_relationships_domain
├─ idx_relationships_from_type (복합)
└─ idx_relationships_to_type (복합)

audit_log:
├─ idx_audit_domain
├─ idx_audit_entity
├─ idx_audit_timestamp
└─ idx_audit_operation
```

---

## ✅ 검증 방법

### 1️⃣ Python에서 연결 테스트

```python
# scripts/test_connection.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('.env.neon')

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

# 테이블 확인
cursor.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema='public'
""")

tables = cursor.fetchall()
print(f"테이블: {tables}")

cursor.close()
conn.close()
```

### 2️⃣ SQL 명령어로 직접 연결

```bash
# psql로 연결 (설치되어 있으면)
psql "postgresql://neondb_owner:npg_Z4XO3lMLGyRs@ep-muddy-moon-aobi6rvr-pooler.c-2.ap-southeast-1.aws.neon.tech/ont_db?sslmode=require"

# 또는
psql -h ep-muddy-moon-aobi6rvr-pooler.c-2.ap-southeast-1.aws.neon.tech \
     -U neondb_owner \
     -d ont_db \
     -c "SELECT COUNT(*) FROM entities;"
```

### 3️⃣ sqlalchemy로 테스트

```python
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv('.env.neon')

engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM entities"))
    count = result.fetchone()[0]
    print(f"엔티티 수: {count}")
```

---

## 📁 파일 구조

```
ont_platform/v3/
├── .env.neon                    ← 환경 설정 (Neon.tech)
├── .env.example                 ← 템플릿
├── .env                         ← 활성화 파일 (생성 필요)
├── SETUP_NEON.md               ← 이 파일
├── scripts/
│   ├── init_schema.sql         ← 스키마 DDL
│   ├── setup_database.py       ← 초기화 스크립트
│   └── test_connection.py      ← 연결 테스트
├── docs/
│   ├── POSTGRES_MIGRATION_ROADMAP.md
│   ├── SPARQL_TRANSLATOR_DESIGN.md
│   ├── SCHEMA_DESIGN.md
│   └── MIGRATION_SCRIPTS.md
└── src/
    └── ... (애플리케이션 코드)
```

---

## 🚀 다음 단계

### Week 1 Task 1-1: rdflib 통합

```bash
# 1. 환경 활성화
cp .env.neon .env

# 2. 기존 테스트 실행
pytest tests/integration/test_sparql_full_suite.py -v

# 3. 30개 SPARQL 쿼리 테스트 통과 확인
```

### Week 1 Task 1-2: Alembic 마이그레이션

```bash
# 1. Alembic 초기화 (미실행 시)
alembic init app/db/migrations

# 2. 현재 스키마 상태 기록
alembic revision --autogenerate -m "Initial schema from Neon.tech"

# 3. 마이그레이션 적용 (필요 시)
alembic upgrade head
```

---

## ⚠️ 주의사항

### 1️⃣ 보안
- ✅ SSL 필수 (sslmode=require)
- ✅ 암호는 .env.neon에만 저장 (Git 커밋 금지!)
- ✅ .gitignore에 `.env` 추가

### 2️⃣ 성능
- ⚠️ Neon.tech은 풀링 사용 (커넥션 제한)
- ⚠️ 개발 중: Neon.tech (편의)
- ✅ 벤치마크: 로컬 PostgreSQL (정확한 성능)

### 3️⃣ 비용
- ✅ 무료 tier: 5GB, 3개 프로젝트
- ⚠️ 용량 초과 시 추가 비용

---

## 🔧 문제 해결

### "연결 타임아웃" 오류

```
Error: could not translate host name "ep-muddy-moon-aobi6rvr..."
```

**해결책**:
```bash
# 인터넷 연결 확인
ping google.com

# Neon.tech 상태 확인
# https://status.neon.tech
```

### "인증 실패" 오류

```
FATAL: password authentication failed for user "neondb_owner"
```

**해결책**:
```bash
# .env.neon의 암호 재확인
cat .env.neon | grep DB_PASSWORD

# Neon.tech 콘솔에서 암호 리셋
# https://console.neon.tech → Settings → Security
```

### "SSL 오류"

```
SSL SYSCALL error: EOF detected
```

**해결책**:
```bash
# .env.neon에서 SSL 모드 확인
grep sslmode .env.neon
# 출력: sslmode=require (필수)

# 로컬 테스트 시 sslmode=disable로 변경 불가
```

---

## 📞 참고 자료

- **Neon.tech 공식**: https://neon.tech
- **PostgreSQL 문서**: https://www.postgresql.org/docs/14/
- **psycopg2 문서**: https://www.psycopg.org/psycopg2/docs/

---

## ✅ 체크리스트

- [x] .env.neon 파일 생성 (연결 정보 포함)
- [x] .env.example 생성 (템플릿)
- [x] init_schema.sql 작성 (스키마 DDL)
- [x] setup_database.py 작성 (초기화 스크립트)
- [ ] python scripts/setup_database.py 실행 ← **지금 해야 함**
- [ ] cp .env.neon .env 실행
- [ ] 연결 테스트
- [ ] Week 1 Task 시작

---

**준비됨**: 스키마 생성 준비 완료. 이제 `python scripts/setup_database.py` 실행하세요!
