from __future__ import annotations

import os
import sqlite3
import time
import re
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple

from app.models.data_catalog import CatalogTableResponse, ColumnSpec, QueryExecuteResponse, QueryExecuteRequest


class DataCatalogService:
    """메달리온 아키텍처 모의 데이터베이스(SQLite) 관리 및 질의 서비스"""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            backend_dir = Path(__file__).resolve().parent.parent.parent
            storage_dir = backend_dir / "storage"
            storage_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(storage_dir / "data_catalog.db")

        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """데이터베이스 및 예제 테이블 구조 생성 & 초기 시딩"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Bronze 테이블 생성 (원천 로데이터)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS src_factory_events (
                raw_id TEXT PRIMARY KEY,
                event_type TEXT,
                payload TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Silver 테이블 생성 (정제된 데이터)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tb_equipment_status (
                equipment_id TEXT PRIMARY KEY,
                name TEXT,
                factory TEXT,
                status TEXT,
                last_updated TEXT
            )
        """)

        # 3. Gold 테이블 생성 (분석용 마트)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gold_daily_equipment_metrics (
                metric_date TEXT,
                equipment_id TEXT,
                failure_count INTEGER,
                avg_repair_time REAL,
                PRIMARY KEY (metric_date, equipment_id)
            )
        """)

        conn.commit()

        # 데이터가 비어 있는 경우 시딩 진행
        cursor.execute("SELECT COUNT(*) as cnt FROM tb_equipment_status")
        row = cursor.fetchone()
        if row and row['cnt'] == 0:
            self._seed_data(cursor)
            conn.commit()

        conn.close()

    def _seed_data(self, cursor: sqlite3.Cursor):
        """모의 데이터 삽입"""
        # Bronze: 3개 이벤트 등록
        cursor.executemany(
            "INSERT INTO src_factory_events (raw_id, event_type, payload, received_at) VALUES (?, ?, ?, ?)",
            [
                ("evt-001", "fault", '{"equipment_name": "검사 카메라", "message": "압력이 낮고 렌즈가 오염되었습니다.", "level": "WARN"}', "2026-06-14 10:00:00"),
                ("evt-002", "info", '{"equipment_name": "배터리 탭 용접기", "message": "용접 압력 정상 범위 도달.", "level": "INFO"}', "2026-06-14 10:15:00"),
                ("evt-003", "fault", '{"equipment_name": "조립 로봇", "message": "서보 모터 과열 에러 발생. 작동 중단.", "level": "CRITICAL"}', "2026-06-14 11:30:00"),
            ]
        )

        # Silver: 4개 장비 등록
        cursor.executemany(
            "INSERT INTO tb_equipment_status (equipment_id, name, factory, status, last_updated) VALUES (?, ?, ?, ?, ?)",
            [
                ("eq-001", "검사 카메라", "세종 배터리팩 공장", "점검필요", "2026-06-14 18:00"),
                ("eq-002", "배터리 탭 용접기", "세종 배터리팩 공장", "정상", "2026-06-14 18:05"),
                ("eq-003", "조립 로봇", "울산 모듈 공장", "고장", "2026-06-14 17:50"),
                ("eq-004", "에이징 챔버", "울산 모듈 공장", "정상", "2026-06-14 16:30"),
            ]
        )

        # Gold: 최근 일별 집계 지표 등록
        cursor.executemany(
            "INSERT INTO gold_daily_equipment_metrics (metric_date, equipment_id, failure_count, avg_repair_time) VALUES (?, ?, ?, ?)",
            [
                ("2026-06-12", "eq-001", 1, 45.5),
                ("2026-06-12", "eq-003", 0, 0.0),
                ("2026-06-13", "eq-001", 2, 60.0),
                ("2026-06-13", "eq-002", 0, 0.0),
                ("2026-06-13", "eq-003", 1, 120.0),
                ("2026-06-14", "eq-001", 3, 35.0),
                ("2026-06-14", "eq-003", 2, 90.0),
            ]
        )

    def get_tables_metadata(self) -> List[CatalogTableResponse]:
        """메달리온 테이블 정보와 컬럼 사양 반환"""
        table_descriptions = {
            "src_factory_events": (
                "BRONZE",
                "공장 및 외부 IoT 시스템에서 원천 유입된 로그 및 센서 이력 데이터 (반정형 payload 포함)"
            ),
            "tb_equipment_status": (
                "SILVER",
                "원천 이벤트를 파싱 및 정제하고 온톨로지 개념과 매핑 완료한 표준 장비 마스터 데이터"
            ),
            "gold_daily_equipment_metrics": (
                "GOLD",
                "장비별 일별 고장 횟수 및 평균 정비 소요 시간 집계 요약 마트 (BI 및 보고용)"
            )
        }

        # 컬럼 한국어 설명 맵
        column_descriptions = {
            "raw_id": "수집 원본 식별 아이디",
            "event_type": "이벤트 종류 (fault, info, log)",
            "payload": "이벤트 본문 (JSON 텍스트)",
            "received_at": "수집 이벤트 유입 시간",
            "equipment_id": "설비 고유 온톨로지 ID",
            "name": "설비 명칭",
            "factory": "소속 공장 명칭",
            "status": "장비 가동 상태 (정상, 점검필요, 고장)",
            "last_updated": "최종 정보 갱신 시간",
            "metric_date": "지표 측정 기준 일자",
            "failure_count": "당일 누적 고장 건수",
            "avg_repair_time": "평균 정비 복구 시간 (분 단위)"
        }

        conn = self._get_connection()
        cursor = conn.cursor()
        catalog: List[CatalogTableResponse] = []

        try:
            for table_name, (layer, desc) in table_descriptions.items():
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                
                columns: List[ColumnSpec] = []
                for col in columns_info:
                    col_name = col['name']
                    columns.append(ColumnSpec(
                        name=col_name,
                        type=col['type'],
                        description=column_descriptions.get(col_name, "")
                    ))

                catalog.append(CatalogTableResponse(
                    table_name=table_name,
                    layer=layer,
                    description=desc,
                    columns=columns
                ))
        finally:
            conn.close()

        return catalog

    def execute_query(self, query_request: QueryExecuteRequest) -> QueryExecuteResponse:
        """안전하게 SQL 질의 실행 (오직 SELECT 문만 수행 허용)"""
        raw_query = query_request.query.strip()
        
        # 1. 쿼리 비어있음 예외
        if not raw_query:
            return QueryExecuteResponse(columns=[], rows=[], execution_time_ms=0, error="쿼리가 입력되지 않았습니다.")

        # 2. SELECT 문 검증 (주석 제외하고 첫 단어 확인)
        clean_query = re.sub(r'--.*$', '', raw_query, flags=re.MULTILINE) # 한 줄 주석 제거
        clean_query = re.sub(r'/\*[\s\S]*?\*/', '', clean_query) # 여러 줄 주석 제거
        clean_query = clean_query.strip()

        # 읽기 전용 검증: SELECT 및 WITH 문만 통과
        if not (clean_query.lower().startswith("select") or clean_query.lower().startswith("with")):
            return QueryExecuteResponse(
                columns=[], 
                rows=[], 
                execution_time_ms=0, 
                error="보안 경고: 데이터 카탈로그 콘솔은 읽기 전용(SELECT, WITH) 쿼리 실행만 지원합니다. DDL/DML 수행은 허용되지 않습니다."
            )

        # 악성 명령어(수정/삭제 등) 내장 여부 서브 검증
        blocked_keywords = ["drop", "delete", "update", "insert", "alter", "create", "replace", "truncate"]
        for word in blocked_keywords:
            if re.search(r'\b' + word + r'\b', clean_query.lower()):
                return QueryExecuteResponse(
                    columns=[],
                    rows=[],
                    execution_time_ms=0,
                    error=f"보안 경고: 쿼리 실행이 차단되었습니다. 허용되지 않는 키워드가 감지되었습니다: '{word}'"
                )

        # 3. 데이터베이스 실행
        conn = self._get_connection()
        cursor = conn.cursor()
        start_time = time.time()

        try:
            cursor.execute(raw_query)
            rows = cursor.fetchall()
            elapsed_time_ms = (time.time() - start_time) * 1000

            # 컬럼명 추출
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # 이중 리스트로 로우 데이터 변환
            rows_data = []
            for r in rows:
                rows_data.append([r[col] for col in columns])

            return QueryExecuteResponse(
                columns=columns,
                rows=rows_data,
                execution_time_ms=round(elapsed_time_ms, 2),
                error=None
            )
        except Exception as e:
            elapsed_time_ms = (time.time() - start_time) * 1000
            return QueryExecuteResponse(
                columns=[],
                rows=[],
                execution_time_ms=round(elapsed_time_ms, 2),
                error=f"SQL 실행 에러: {str(e)}"
            )
        finally:
            conn.close()
