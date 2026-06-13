"""Write-back Worker 비동기 안전장치 성능 검증 스크립트"""
import time
import threading
import concurrent.futures
import multiprocessing
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 백엔드 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.models import Base, Entity, WriteBackQueue, ActionExecution, ChangeLog
from app.services.write_back_worker import WriteBackWorker, WriteBackWorkerConfig
from app.services.sap_api_mock import SAPApiMock, MockResponseStatus

def setup_test_db(engine):
    Base.metadata.create_all(bind=engine)

def run_scenario_1() -> float:
    """테스트 시나리오 1: 다중 워커 중복 실행률 검증"""
    print("\n[Scenario 1] Multiple Workers Duplicate Execution Rate Verification...")
    
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    setup_test_db(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # 의존성 데이터 삽입
    ae = ActionExecution(
        id="ae_sc1", action_id="test", entity_id="proj_001", domain_id="ai-voucher-2025",
        status="EXECUTED", requested_by="user@example.com", requested_at=datetime.utcnow()
    )
    db.add(ae)
    db.flush()

    # 100개 PENDING 아이템 삽입
    for i in range(100):
        item = WriteBackQueue(
            id=f"item_{i:03d}", action_execution_id="ae_sc1", target_system="SAP",
            payload={"project_id": f"proj_{i:03d}"}, status="PENDING", retry_count=0
        )
        db.add(item)
    db.commit()

    processed_logs = []
    log_lock = threading.Lock()

    # 100% 성공율의 Slow Mock API 정의 (경합 시뮬레이션용 지연 시간 추가)
    class ThreadSafeSlowMock(SAPApiMock):
        def post(self, target_system, endpoint, payload):
            time.sleep(0.01)  # 10ms 지연
            with log_lock:
                processed_logs.append(payload.get("project_id"))
            return super().post(target_system, endpoint, payload)

    sap_mock = ThreadSafeSlowMock(success_rate=1.0)

    def worker_task(worker_id):
        worker_db = SessionLocal()
        worker = WriteBackWorker(worker_db, sap_mock)
        # 10번 반복 실행하며 대기열 처리
        for _ in range(10):
            worker.process_pending()
            time.sleep(0.05)
        worker_db.close()

    # 2개 워커 병렬 가동
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(worker_task, 1)
        executor.submit(worker_task, 2)

    # 결과 분석
    total_processed = len(processed_logs)
    unique_processed = len(set(processed_logs))
    duplicates = total_processed - unique_processed
    duplicate_rate = (duplicates / 100.0) * 100.0 if unique_processed > 0 else 0

    print(f"-> Total Processed: {total_processed}")
    print(f"-> Unique Processed: {unique_processed}")
    print(f"-> Duplicate Processed: {duplicates}")
    print(f"-> Duplicate Execution Rate: {duplicate_rate:.2f}%")

    assert duplicate_rate == 0.0, f"Duplicate execution detected! Rate: {duplicate_rate}%"
    print("[PASS] Scenario 1: Duplicate execution rate is 0%")
    return duplicate_rate

def run_scenario_2() -> float:
    """테스트 시나리오 2: 지수 백오프 지연 준수율 검증"""
    print("\n[Scenario 2] Exponential Backoff Compliance Verification...")

    engine = create_engine("sqlite:///:memory:")
    setup_test_db(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    ae = ActionExecution(
        id="ae_sc2", action_id="test", entity_id="proj_sc2", domain_id="ai-voucher-2025",
        status="EXECUTED", requested_by="user@example.com", requested_at=datetime.utcnow()
    )
    db.add(ae)
    db.flush()

    item = WriteBackQueue(
        id="backoff_item", action_execution_id="ae_sc2", target_system="SAP",
        payload={"project_id": "proj_sc2"}, status="PENDING", retry_count=0, max_retries=3
    )
    db.add(item)
    db.commit()

    # 무조건 실패하는 Mock API 및 설정 준비
    sap_mock = SAPApiMock(success_rate=0.0)
    config = WriteBackWorkerConfig()
    config.INITIAL_RETRY_DELAY = 60  # 기본 지연 60초
    config.RETRY_BACKOFF_MULTIPLIER = 2  # 백오프 승수 2배

    worker = WriteBackWorker(db, sap_mock, config)

    # 1차 실패 시뮬레이션
    now_1 = datetime.utcnow()
    worker.process_pending()
    db.refresh(item)

    expected_delay = 120  # 60 * 2^1 = 120초
    actual_delay = (item.next_retry_at - now_1).total_seconds()

    print(f"-> Attempt 1 Next Retry: {item.next_retry_at} (Delay: {actual_delay:.1f}s)")
    assert 118 <= actual_delay <= 122, f"Delay mismatch: {actual_delay}s"
    assert item.retry_count == 1, "Retry count incremented to 1"

    # 2차 실패 시뮬레이션
    now_2 = datetime.utcnow()
    # 2차 처리를 위해 next_retry_at을 임의로 현재 시각으로 앞당김 (대기 방지)
    item.next_retry_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    worker.process_pending()
    db.refresh(item)

    expected_delay_2 = 240  # 60 * 2^2 = 240초
    actual_delay_2 = (item.next_retry_at - now_2).total_seconds()

    print(f"-> Attempt 2 Next Retry: {item.next_retry_at} (Delay: {actual_delay_2:.1f}s)")
    assert 238 <= actual_delay_2 <= 242, f"Delay mismatch: {actual_delay_2}s"
    assert item.retry_count == 2, "Retry count incremented to 2"

    # 3차 실패 시뮬레이션
    now_3 = datetime.utcnow()
    item.next_retry_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    worker.process_pending()
    db.refresh(item)

    expected_delay_3 = 480  # 60 * 2^3 = 480초
    actual_delay_3 = (item.next_retry_at - now_3).total_seconds()

    print(f"-> Attempt 3 Next Retry: {item.next_retry_at} (Delay: {actual_delay_3:.1f}s)")
    assert 478 <= actual_delay_3 <= 482, f"Delay mismatch: {actual_delay_3}s"
    assert item.retry_count == 3, "Retry count incremented to 3"

    # 4차 실패 -> DLQ로 격리 확인
    item.next_retry_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    worker.process_pending()
    db.refresh(item)

    print(f"-> Attempt 4 Final Status: {item.status}")
    assert item.status == "DLQ", f"Incorrect final status: {item.status}"
    assert item.dlq_reason is not None, "DLQ reason saved"
    assert item.dlq_at is not None, "DLQ timestamp saved"

    print("[PASS] Scenario 2: Exponential backoff compliant at 100%")
    return 100.0

def worker_process_with_crash_helper(item_count: int, crash_at_item: int):
    """프로세스 크래시 시뮬레이션용 헬퍼 함수"""
    engine = create_engine("sqlite:///crash_test.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    worker = WriteBackWorker(db, SAPApiMock(success_rate=1.0))
    
    # 쿼리로 pending 항목 가져오기
    pending_items = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "PENDING"
    ).all()

    for idx, item in enumerate(pending_items):
        if idx == crash_at_item:
            # 강제 크래시
            print(f"-> [Worker Process] Crash occurred while processing item {idx}...")
            os._exit(1)
        
        try:
            worker._process_single_item(item)
            db.commit()  # 개별 커밋
        except Exception:
            db.commit()

def run_scenario_3() -> float:
    """테스트 시나리오 3: 트랜잭션 유실률 검증"""
    print("\n[Scenario 3] Transaction Loss Rate Verification...")
    
    # 파일 DB 초기화
    db_file = "crash_test.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    engine = create_engine(f"sqlite:///{db_file}")
    setup_test_db(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    ae = ActionExecution(
        id="ae_sc3", action_id="test", entity_id="proj_sc3", domain_id="ai-voucher-2025",
        status="EXECUTED", requested_by="user@example.com", requested_at=datetime.utcnow()
    )
    db.add(ae)
    db.flush()

    # 20개 PENDING 아이템 삽입
    for i in range(20):
        item = WriteBackQueue(
            id=f"crash_item_{i:02d}", action_execution_id="ae_sc3", target_system="SAP",
            payload={"project_id": f"proj_{i:02d}"}, status="PENDING"
        )
        db.add(item)
    db.commit()
    db.close()

    # 별도 프로세스로 워커 가동 (10번째 아이템 처리 후 크래시)
    p = multiprocessing.Process(target=worker_process_with_crash_helper, args=(20, 10))
    p.start()
    p.join()  # 크래시가 발생할 때까지 대기

    # 결과 데이터 검증
    db_verif = SessionLocal()
    synced_items = db_verif.query(WriteBackQueue).filter(WriteBackQueue.status == "CONFIRMED").all()
    pending_items = db_verif.query(WriteBackQueue).filter(WriteBackQueue.status == "PENDING").all()

    print(f"-> Post-Crash CONFIRMED items count: {len(synced_items)}")
    print(f"-> Post-Crash PENDING items count: {len(pending_items)}")

    # 개별 커밋으로 인해 크래시 이전 10개(0~9)는 완벽히 CONFIRMED로 저장되어야 함
    assert len(synced_items) == 10, f"Data loss detected! Synced count: {len(synced_items)}"
    assert len(pending_items) == 10, f"Pending count mismatch: {len(pending_items)}"

    # 파일 삭제
    db_verif.close()
    engine.dispose()
    if os.path.exists(db_file):
        os.remove(db_file)

    print("[PASS] Scenario 3: Transaction loss rate is 0%")
    return 0.0

def run_scenario_4() -> dict:
    """테스트 시나리오 4: 성능 메트릭 측정 (500개 대형 처리)"""
    print("\n[Scenario 4] Performance Metrics Calculation (500 items)...")

    engine = create_engine("sqlite:///:memory:")
    setup_test_db(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    ae = ActionExecution(
        id="ae_sc4", action_id="test", entity_id="proj_sc4", domain_id="ai-voucher-2025",
        status="EXECUTED", requested_by="user@example.com", requested_at=datetime.utcnow()
    )
    db.add(ae)
    db.flush()

    # 500개 PENDING 아이템 삽입
    for i in range(500):
        item = WriteBackQueue(
            id=f"perf_item_{i:03d}", action_execution_id="ae_sc4", target_system="SAP",
            payload={"project_id": f"proj_{i:03d}"}, status="PENDING"
        )
        db.add(item)
    db.commit()

    # 100% 성공 Mock API
    sap_mock = SAPApiMock(success_rate=1.0)
    worker = WriteBackWorker(db, sap_mock)

    # 500개 순차 처리 시간 측정
    start_time = time.time()
    total_processed = 0
    while True:
        result = worker.process_pending()
        processed = result["processed"]
        total_processed += processed
        if processed == 0:
            break
    elapsed_time = time.time() - start_time  # 초
    throughput_per_min = (total_processed / elapsed_time) * 60.0
    avg_latency_ms = (elapsed_time / total_processed) * 1000.0

    print(f"-> Processed Count: {total_processed}")
    print(f"-> Total Elapsed Time: {elapsed_time:.2f}s")
    print(f"-> Throughput: {throughput_per_min:.2f} items/min")
    print(f"-> Average Latency: {avg_latency_ms:.2f} ms")

    assert throughput_per_min >= 50.0, f"Throughput target missed: {throughput_per_min} items/min"
    assert avg_latency_ms <= 1000.0, f"Latency target exceeded: {avg_latency_ms} ms"

    print("[PASS] Scenario 4: Target performance metrics met")
    
    return {
        "throughput": throughput_per_min,
        "avg_latency": avg_latency_ms,
        "total_time": elapsed_time
    }

def main():
    print("==================================================")
    print("  WriteBackWorker Async Safety Performance Verification")
    print("==================================================")

    results = {}
    try:
        results["duplicate_rate"] = run_scenario_1()
        results["backoff_compliance"] = run_scenario_2()
        results["data_loss_rate"] = run_scenario_3()
        results["perf"] = run_scenario_4()
        
        print("\n==================================================")
        print("  [SUCCESS] All async safety performance tests passed!")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Test failure: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
