from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile

from .data import fresh_raw_data


class DataRepository:
    def load(self) -> dict:
        raise NotImplementedError

    def save(self, raw: dict) -> None:
        raise NotImplementedError


def resolve_default() -> "DataRepository":
    """환경 변수를 보고 적절한 Repository를 선택한다.

    우선순위:
        1. DATABASE_URL (postgresql://...) → PostgresDataRepository (psycopg 필요)
        2. ONTOLOGY_DATA_PATH → JsonFileDataRepository
        3. 기본값 → InMemoryDataRepository
    """
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith(("postgresql://", "postgres://")):
        try:
            return PostgresDataRepository(database_url)
        except Exception as exc:  # noqa: BLE001
            # 의존성/접속 실패 시 안전하게 메모리로 폴백 (교육 환경 보호)
            print(f"[repository] Postgres 연결 실패 → InMemory 폴백: {exc}")
            return InMemoryDataRepository()
    data_path = os.environ.get("ONTOLOGY_DATA_PATH")
    if data_path:
        return JsonFileDataRepository(data_path)
    return InMemoryDataRepository()


class InMemoryDataRepository(DataRepository):
    def __init__(self, seed: dict | None = None) -> None:
        self.raw = deepcopy(seed) if seed is not None else fresh_raw_data()

    def load(self) -> dict:
        return deepcopy(self.raw)

    def save(self, raw: dict) -> None:
        self.raw = deepcopy(raw)


class JsonFileDataRepository(DataRepository):
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            raw = fresh_raw_data()
            self.save(raw)
            return raw
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, raw: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
            json.dump(raw, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_path = Path(handle.name)
        temp_path.replace(self.path)


class PostgresDataRepository(DataRepository):
    """JSONB 한 행에 전체 raw_data를 저장하는 단순 Postgres 저장소.

    교육·운영 입문용. 실제 운영은 객체 타입별 정규화 테이블을 권장.
    의존성: psycopg[binary] (없으면 import 시 ImportError).
    """

    TABLE_NAME = "ontology_snapshot"
    ROW_ID = 1

    def __init__(self, database_url: str) -> None:
        try:
            import psycopg  # noqa: F401  (확인용 import)
        except ImportError as exc:
            raise RuntimeError(
                "PostgresDataRepository를 사용하려면 `pip install psycopg[binary]`가 필요합니다."
            ) from exc
        self.database_url = database_url
        self._ensure_schema()

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url, autocommit=True)

    def _ensure_schema(self) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id INT PRIMARY KEY,
                    raw JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

    def load(self) -> dict:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT raw FROM {self.TABLE_NAME} WHERE id = %s", (self.ROW_ID,)
            )
            row = cur.fetchone()
            if row is None:
                raw = fresh_raw_data()
                self.save(raw)
                return raw
            value = row[0]
            return value if isinstance(value, dict) else json.loads(value)

    def save(self, raw: dict) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self.TABLE_NAME} (id, raw, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (id) DO UPDATE
                  SET raw = EXCLUDED.raw, updated_at = NOW();
                """,
                (self.ROW_ID, json.dumps(raw, ensure_ascii=False)),
            )
