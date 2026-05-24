# Week 3 Task 1: Changelog 모델 구현 지시서

**작성일**: 2026-05-25  
**시작일**: 2026-05-25 (미리 시작)  
**마감일**: 2026-06-10 (Week 3 시작 전 완료)  
**담당**: Claude (Backend)  
**소요시간**: 3~4시간  
**우선순위**: 🔴 High

---

## 🎯 목표

**Changelog 저장소 구현** — 모든 액션 실행 기록을 추적 가능하도록 하기

```
액션 실행
  ↓
Changelog 자동 생성 (DB + JSONL)
  ↓
Write-back Worker가 SAP 동기화
  ↓
최종적으로 Audit Log에 기록
```

---

## 📋 요구사항 (Technical Spec)

### 1. Changelog의 역할

- ✅ **모든 액션 실행 기록 추적**
- ✅ **상태 변화 히스토리** (Before/After)
- ✅ **누가 언제 어떤 액션을 했는지** 기록
- ✅ **SAP 동기화 여부 추적** (sync_status)
- ✅ **재시도 로직 지원** (retry_count)

### 2. Changelog 데이터 구조

```python
class ChangeLog(Base):
    # PK
    id: str                  # "chg_20260525_001"
    
    # 엔티티 정보
    entity_id: str          # "proj_001" (FK to entities.id)
    entity_type: str        # "Project"
    domain_id: str          # "ai-voucher-2025"
    
    # 액션 정보
    action_type: str        # "APPROVE_PROJECT", "REJECT_PROJECT", ...
    actor: str              # "pm@example.com" (누가)
    timestamp: datetime     # "2026-05-25 15:30:45.123456" (언제)
    source: str             # "web_ui", "api", "batch"
    
    # 상태 변화
    old_status: str | None  # "UnderReview"
    new_status: str | None  # "Approved"
    
    # Write-back 추적
    sync_status: str        # "PENDING" | "SYNCED" | "FAILED"
    target_system: str      # "SAP", "ERP", "NOTIFICATION"
    sync_timestamp: datetime | None
    retry_count: int        # 0, 1, 2, ...
    error_message: str | None
```

### 3. 저장 위치

**Database**: SQLite (on-disk)
```
ontology.db
  ├── changelog (테이블)
  │   ├── id
  │   ├── entity_id
  │   ├── action_type
  │   ├── timestamp
  │   └── ...
```

**File System**: JSONL (아카이브 용)
```
storage/demo-co/proj-01/changelog/
  └── ai-voucher-2025_changes.jsonl

# 파일 내용 예시:
{"id":"chg_20260525_001","entity_id":"proj_001","action_type":"APPROVE_PROJECT","actor":"pm@example.com","timestamp":"2026-05-25T15:30:45Z","old_status":"UnderReview","new_status":"Approved","sync_status":"PENDING"}
{"id":"chg_20260525_002","entity_id":"proj_002","action_type":"REJECT_PROJECT","actor":"pm@example.com","timestamp":"2026-05-25T15:31:20Z","old_status":"UnderReview","new_status":"Rejected","sync_status":"PENDING"}
```

---

## 📍 작업 위치

### 생성/수정할 파일들

```
ont_platform/v3/src/backend/
├── app/db/models.py
│   └── ChangeLog 클래스 추가 (약 40줄)
├── app/services/
│   └── changelog_service.py (신규, 약 60줄)
└── tests/
    └── test_changelog_model.py (신규, 약 80줄)
```

---

## 🔧 구현 단계

### Step 1: models.py 에서 ChangeLog ORM 모델 정의 (30분)

**파일**: `app/db/models.py`

**추가 코드**:
```python
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship

class ChangeLog(Base):
    """액션 실행 이력 추적"""
    __tablename__ = "changelog"

    # Primary Key
    id = Column(String, primary_key=True)  # "chg_20260525_001"
    
    # Entity 정보
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)  # "Project"
    domain_id = Column(String, nullable=False, index=True)  # "ai-voucher-2025"
    
    # Action 정보
    action_type = Column(String, nullable=False, index=True)  # "APPROVE_PROJECT"
    actor = Column(String, nullable=False)  # "pm@example.com"
    source = Column(String, nullable=False)  # "web_ui", "api"
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 상태 변화
    old_status = Column(String, nullable=True)  # "UnderReview"
    new_status = Column(String, nullable=True)  # "Approved"
    
    # Write-back 추적
    sync_status = Column(String, default="PENDING", nullable=False, index=True)  
    # PENDING | SYNCED | FAILED
    target_system = Column(String, nullable=True)  # "SAP", "ERP", "NOTIFICATION"
    sync_timestamp = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    entity = relationship("Entity", foreign_keys=[entity_id])
    
    __table_args__ = (
        CheckConstraint("sync_status IN ('PENDING', 'SYNCED', 'FAILED')", name="valid_sync_status"),
    )
```

**체크리스트**:
- [ ] ChangeLog 클래스 정의됨
- [ ] 모든 필드가 correct type
- [ ] PK, FK, Index 설정됨
- [ ] CheckConstraint 추가됨
- [ ] Entity relationship 설정됨

---

### Step 2: ChangeLogService 구현 (1시간)

**파일**: `app/services/changelog_service.py` (신규 생성)

**코드**:
```python
"""Changelog 서비스 — 액션 실행 이력 저장"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session
from pathlib import Path
import json

from app.db.models import ChangeLog


class ChangeLogService:
    """Changelog 관리 서비스"""
    
    CHANGELOG_DIR = Path("storage/demo-co/proj-01/changelog")
    
    @staticmethod
    def create_changelog(
        db: Session,
        entity_id: str,
        entity_type: str,
        domain_id: str,
        action_type: str,
        actor: str,
        old_status: str | None,
        new_status: str | None,
        source: str = "web_ui",
        target_system: str | None = None
    ) -> ChangeLog:
        """
        Changelog 레코드 생성
        
        Args:
            db: 데이터베이스 세션
            entity_id: 엔티티 ID (e.g., "proj_001")
            entity_type: 엔티티 타입 (e.g., "Project")
            domain_id: 도메인 ID (e.g., "ai-voucher-2025")
            action_type: 액션 종류 (e.g., "APPROVE_PROJECT")
            actor: 실행자 (e.g., "pm@example.com")
            old_status: 변경 전 상태
            new_status: 변경 후 상태
            source: 요청 출처 ("web_ui", "api", "batch")
            target_system: 동기화 대상 시스템 ("SAP", "ERP", "NOTIFICATION")
        
        Returns:
            생성된 ChangeLog 객체
        """
        changelog = ChangeLog(
            id=f"chg_{uuid4().hex[:12]}",
            entity_id=entity_id,
            entity_type=entity_type,
            domain_id=domain_id,
            action_type=action_type,
            actor=actor,
            source=source,
            timestamp=datetime.utcnow(),
            old_status=old_status,
            new_status=new_status,
            sync_status="PENDING",
            target_system=target_system,
            retry_count=0
        )
        db.add(changelog)
        db.flush()  # ID를 얻기 위해 flush
        
        # JSONL 파일에도 저장
        ChangeLogService._save_to_jsonl(changelog)
        
        return changelog
    
    @staticmethod
    def _save_to_jsonl(changelog: ChangeLog):
        """JSONL 파일에 저장"""
        ChangeLogService.CHANGELOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # 파일명: {domain_id}_changes.jsonl
        file_path = ChangeLogService.CHANGELOG_DIR / f"{changelog.domain_id}_changes.jsonl"
        
        # JSON 직렬화
        record = {
            "id": changelog.id,
            "entity_id": changelog.entity_id,
            "entity_type": changelog.entity_type,
            "domain_id": changelog.domain_id,
            "action_type": changelog.action_type,
            "actor": changelog.actor,
            "source": changelog.source,
            "timestamp": changelog.timestamp.isoformat(),
            "old_status": changelog.old_status,
            "new_status": changelog.new_status,
            "sync_status": changelog.sync_status,
            "target_system": changelog.target_system,
            "retry_count": changelog.retry_count,
            "error_message": changelog.error_message
        }
        
        # 파일에 추가 (append)
        with open(file_path, "a") as f:
            f.write(json.dumps(record) + "\n")
    
    @staticmethod
    def mark_synced(db: Session, changelog_id: str):
        """changelog를 SYNCED로 표시"""
        changelog = db.query(ChangeLog).filter(ChangeLog.id == changelog_id).first()
        if changelog:
            changelog.sync_status = "SYNCED"
            changelog.sync_timestamp = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def mark_failed(db: Session, changelog_id: str, error_message: str, retry_count: int = 0):
        """changelog를 FAILED로 표시 (재시도 불가)"""
        changelog = db.query(ChangeLog).filter(ChangeLog.id == changelog_id).first()
        if changelog:
            changelog.sync_status = "FAILED"
            changelog.error_message = error_message
            changelog.retry_count = retry_count
            db.commit()
    
    @staticmethod
    def increment_retry(db: Session, changelog_id: str):
        """재시도 횟수 증가"""
        changelog = db.query(ChangeLog).filter(ChangeLog.id == changelog_id).first()
        if changelog:
            changelog.retry_count += 1
            db.commit()
    
    @staticmethod
    def get_pending_changes(db: Session, domain_id: str) -> list[ChangeLog]:
        """PENDING 상태의 changelog 조회"""
        return db.query(ChangeLog).filter(
            ChangeLog.domain_id == domain_id,
            ChangeLog.sync_status == "PENDING"
        ).all()
    
    @staticmethod
    def get_change_history(db: Session, entity_id: str) -> list[ChangeLog]:
        """특정 엔티티의 변경 이력 조회"""
        return db.query(ChangeLog).filter(
            ChangeLog.entity_id == entity_id
        ).order_by(ChangeLog.timestamp.desc()).all()
```

**체크리스트**:
- [ ] create_changelog() 메서드 구현됨
- [ ] _save_to_jsonl() 메서드 구현됨
- [ ] mark_synced() 메서드 구현됨
- [ ] mark_failed() 메서드 구현됨
- [ ] increment_retry() 메서드 구현됨
- [ ] get_pending_changes() 메서드 구현됨
- [ ] get_change_history() 메서드 구현됨

---

### Step 3: action_executor.py 수정 (30분)

**파일**: `app/services/action_executor.py`

**수정 내용**: 각 액션 실행 시 ChangeLog 생성

현재 코드:
```python
def execute(self, entity_id: str, **kwargs) -> ActionResult:
    # ... 액션 실행 로직 ...
    self.db.commit()
    return ActionResult(...)
```

수정 후:
```python
from app.services.changelog_service import ChangeLogService

def execute(self, entity_id: str, **kwargs) -> ActionResult:
    # ... 액션 실행 로직 ...
    
    # ✅ Changelog 생성 추가
    ChangeLogService.create_changelog(
        db=self.db,
        entity_id=entity_id,
        entity_type="Project",  # 또는 entity.type
        domain_id="ai-voucher-2025",
        action_type=self.action_id,
        actor=kwargs.get("requested_by", "unknown"),
        old_status=old_status,
        new_status=new_status,
        source="api",
        target_system="SAP"  # 액션에 따라 다를 수 있음
    )
    
    self.db.commit()
    return ActionResult(...)
```

**체크리스트**:
- [ ] ActionBase.__init__에서 ChangeLogService import
- [ ] 각 액션의 execute() 메서드 끝에 ChangeLogService.create_changelog() 호출 추가
- [ ] old_status와 new_status 정보 전달

---

### Step 4: 테스트 작성 (1시간)

**파일**: `tests/test_changelog_model.py` (신규 생성)

**코드**:
```python
"""Changelog 모델 및 서비스 테스트"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base, Entity, ChangeLog
from app.services.changelog_service import ChangeLogService


# 테스트용 인메모리 DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """테스트용 DB 세션"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_entity(db: Session):
    """테스트용 엔티티"""
    entity = Entity(
        id="proj_001",
        entity_type="Project",
        domain_id="ai-voucher-2025",
        properties={
            "name": "Test Project",
            "status": "UnderReview",
            "budget": 5000000
        }
    )
    db.add(entity)
    db.commit()
    return entity


class TestChangeLogModel:
    """ChangeLog 모델 테스트"""
    
    def test_changelog_creation(self, db: Session, test_entity):
        """Test 1: Changelog 레코드 생성"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved",
            source="api",
            target_system="SAP"
        )
        db.commit()
        
        assert changelog.id is not None
        assert changelog.entity_id == "proj_001"
        assert changelog.action_type == "APPROVE_PROJECT"
        assert changelog.actor == "pm@example.com"
        assert changelog.sync_status == "PENDING"
    
    def test_changelog_old_new_status(self, db: Session, test_entity):
        """Test 2: 상태 변화 기록"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="REJECT_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Rejected"
        )
        db.commit()
        
        assert changelog.old_status == "UnderReview"
        assert changelog.new_status == "Rejected"
    
    def test_changelog_mark_synced(self, db: Session, test_entity):
        """Test 3: Changelog을 SYNCED로 표시"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()
        
        # SYNCED로 표시
        ChangeLogService.mark_synced(db, changelog.id)
        
        # 확인
        updated = db.query(ChangeLog).filter(ChangeLog.id == changelog.id).first()
        assert updated.sync_status == "SYNCED"
        assert updated.sync_timestamp is not None
    
    def test_changelog_mark_failed(self, db: Session, test_entity):
        """Test 4: Changelog을 FAILED로 표시"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()
        
        # FAILED로 표시
        ChangeLogService.mark_failed(db, changelog.id, "SAP API timeout", retry_count=1)
        
        # 확인
        updated = db.query(ChangeLog).filter(ChangeLog.id == changelog.id).first()
        assert updated.sync_status == "FAILED"
        assert updated.error_message == "SAP API timeout"
        assert updated.retry_count == 1
    
    def test_changelog_increment_retry(self, db: Session, test_entity):
        """Test 5: 재시도 횟수 증가"""
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()
        
        # 재시도 1회
        ChangeLogService.increment_retry(db, changelog.id)
        updated1 = db.query(ChangeLog).filter(ChangeLog.id == changelog.id).first()
        assert updated1.retry_count == 1
        
        # 재시도 2회
        ChangeLogService.increment_retry(db, changelog.id)
        updated2 = db.query(ChangeLog).filter(ChangeLog.id == changelog.id).first()
        assert updated2.retry_count == 2
    
    def test_get_pending_changes(self, db: Session, test_entity):
        """Test 6: PENDING 상태의 changelog 조회"""
        # 2개 생성
        cl1 = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        cl2 = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_002",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="REJECT_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Rejected"
        )
        db.commit()
        
        # 1개를 SYNCED로 변경
        ChangeLogService.mark_synced(db, cl1.id)
        
        # PENDING만 조회
        pending = ChangeLogService.get_pending_changes(db, "ai-voucher-2025")
        assert len(pending) == 1
        assert pending[0].id == cl2.id
    
    def test_get_change_history(self, db: Session, test_entity):
        """Test 7: 특정 엔티티의 변경 이력 조회"""
        # 같은 엔티티에 대해 3개 액션 실행
        cl1 = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        cl2 = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="START_PAYMENT",
            actor="cfo@example.com",
            old_status="Approved",
            new_status="PaymentStarted"
        )
        db.commit()
        
        # 이력 조회
        history = ChangeLogService.get_change_history(db, "proj_001")
        assert len(history) == 2
        assert history[0].id == cl2.id  # 최신순
        assert history[1].id == cl1.id
    
    def test_changelog_timestamp_auto_set(self, db: Session, test_entity):
        """Test 8: timestamp 자동 설정"""
        before = datetime.utcnow()
        
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()
        
        after = datetime.utcnow()
        
        assert before <= changelog.timestamp <= after
    
    def test_changelog_jsonl_file_created(self, db: Session, test_entity):
        """Test 9: JSONL 파일에 저장됨"""
        import os
        
        changelog = ChangeLogService.create_changelog(
            db=db,
            entity_id="proj_001",
            entity_type="Project",
            domain_id="ai-voucher-2025",
            action_type="APPROVE_PROJECT",
            actor="pm@example.com",
            old_status="UnderReview",
            new_status="Approved"
        )
        db.commit()
        
        # 파일 확인
        file_path = f"storage/demo-co/proj-01/changelog/ai-voucher-2025_changes.jsonl"
        assert os.path.exists(file_path)
        
        # 내용 확인
        with open(file_path, "r") as f:
            content = f.read()
            assert changelog.id in content
            assert "APPROVE_PROJECT" in content
```

**체크리스트**:
- [ ] test_changelog_creation() 작성됨
- [ ] test_changelog_old_new_status() 작성됨
- [ ] test_changelog_mark_synced() 작성됨
- [ ] test_changelog_mark_failed() 작성됨
- [ ] test_changelog_increment_retry() 작성됨
- [ ] test_get_pending_changes() 작성됨
- [ ] test_get_change_history() 작성됨
- [ ] test_changelog_timestamp_auto_set() 작성됨
- [ ] test_changelog_jsonl_file_created() 작성됨

---

### Step 5: 테스트 실행 (20분)

```bash
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend

# 1단계: DB 초기화 (필요하면)
# python -m alembic upgrade head

# 2단계: 테스트 실행
pytest tests/test_changelog_model.py -v

# 예상 결과:
# ======================== 9 passed in 1.23s ========================
```

**체크리스트**:
- [ ] 모든 9개 테스트 통과
- [ ] JSONL 파일이 올바르게 생성됨
- [ ] DB 레코드가 올바르게 저장됨

---

## 📊 완료 기준

```
✅ ORM 모델 정의 완료
  - ChangeLog 클래스 (app/db/models.py)
  - 모든 필드 포함
  - 제약조건 설정

✅ Service 클래스 구현 완료
  - ChangeLogService (app/services/changelog_service.py)
  - create_changelog()
  - mark_synced()
  - mark_failed()
  - increment_retry()
  - get_pending_changes()
  - get_change_history()
  - JSONL 파일 저장

✅ ActionExecutor 통합
  - 각 액션 실행 시 ChangeLog 자동 생성

✅ 테스트 완료
  - 9개 테스트 모두 통과
  - JSONL 파일 생성 확인
```

---

## 🎯 최종 체크리스트

### Code Quality
- [ ] Changelog 모델이 Base를 상속
- [ ] 모든 필드에 type hint 있음
- [ ] 모든 필드에 nullable 지정
- [ ] FK, Index, CheckConstraint 설정됨

### Service
- [ ] ChangeLogService 구현 완료
- [ ] 모든 메서드가 docstring 있음
- [ ] JSONL 저장 로직 작동함

### Integration
- [ ] action_executor.py 수정됨
- [ ] 각 액션에서 ChangeLog 생성
- [ ] DB commit 시점 올바름

### Testing
- [ ] 9개 테스트 모두 통과
- [ ] JSONL 파일 생성 확인
- [ ] 데이터 무결성 검증

---

## 📝 다음 단계

**Task 1 완료 후**:
1. ✅ Changelog 모델 (현재)
2. 📋 SAP API Mock 구현
3. 📋 WriteBackWorker 구현
4. 📋 Write-back 통합 테스트

---

## 📌 참고 자료

- **PHASE3_IMPLEMENTATION_PLAN.md** — Week 3 전체 계획 (226~256줄)
- **app/db/models.py** — 기존 ORM 모델들
- **app/services/action_executor.py** — 액션 실행 로직
- **tests/test_action_executor.py** — 테스트 패턴 참고

---

**작성자**: Claude (Backend Agent)  
**상태**: 📋 지시서 완료  
**시작 가능**: 즉시  
**예상 완료**: 2026-05-25 ~ 05-26 (4시간)
