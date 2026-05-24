#!/usr/bin/env python3
"""
Neon.tech PostgreSQL 데이터베이스 초기화 스크립트

사용:
    python scripts/setup_database.py
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv('.env.neon')

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    logger.error("❌ DATABASE_URL이 설정되지 않았습니다.")
    logger.error("   .env.neon 파일을 확인하세요.")
    sys.exit(1)

def connect_database():
    """데이터베이스 연결"""
    try:
        logger.info("🔌 Neon.tech PostgreSQL 연결 중...")
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ 연결 성공!")
        return conn
    except Exception as e:
        logger.error(f"❌ 연결 실패: {e}")
        sys.exit(1)

def execute_sql_file(conn, filepath: Path):
    """SQL 파일 실행"""
    try:
        logger.info(f"📄 SQL 파일 실행: {filepath.name}")
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()

        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()

        logger.info(f"✅ {filepath.name} 실행 완료")
        return True
    except Exception as e:
        logger.error(f"❌ SQL 실행 실패: {e}")
        conn.rollback()
        return False

def verify_schema(conn):
    """스키마 검증"""
    try:
        logger.info("🔍 스키마 검증 중...")
        cursor = conn.cursor()

        # 테이블 확인
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"✅ 테이블 ({len(tables)}개):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"   - {table}: {count} rows")

        # 뷰 확인
        cursor.execute("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
        """)

        views = [row[0] for row in cursor.fetchall()]
        if views:
            logger.info(f"✅ 뷰 ({len(views)}개):")
            for view in views:
                logger.info(f"   - {view}")

        # 인덱스 확인
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY indexname
        """)

        indexes = [row[0] for row in cursor.fetchall()]
        logger.info(f"✅ 인덱스 ({len(indexes)}개):")
        for index in indexes[:5]:
            logger.info(f"   - {index}")
        if len(indexes) > 5:
            logger.info(f"   ... 외 {len(indexes) - 5}개")

        cursor.close()
        return True
    except Exception as e:
        logger.error(f"❌ 스키마 검증 실패: {e}")
        return False

def test_insert(conn):
    """테스트 데이터 삽입"""
    try:
        logger.info("🧪 테스트 데이터 삽입 중...")
        cursor = conn.cursor()

        # 테스트 엔티티
        cursor.execute("""
            INSERT INTO entities (id, entity_type, domain_id, properties)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            'test_entity_001',
            'TestEntity',
            'ontology_v1',
            '{"name": "Test Entity", "description": "Setup test"}'
        ))

        conn.commit()
        logger.info("✅ 테스트 엔티티 삽입 완료")

        # 삽입 확인
        cursor.execute("SELECT COUNT(*) FROM entities")
        count = cursor.fetchone()[0]
        logger.info(f"   현재 엔티티 수: {count}")

        cursor.close()
        return True
    except Exception as e:
        logger.error(f"❌ 테스트 데이터 삽입 실패: {e}")
        conn.rollback()
        return False

def main():
    """메인 초기화 함수"""
    logger.info("=" * 60)
    logger.info("🚀 Neon.tech PostgreSQL 데이터베이스 초기화")
    logger.info("=" * 60)

    # 1. 연결
    conn = connect_database()

    # 2. 스키마 생성
    schema_file = Path(__file__).parent / 'init_schema.sql'
    if not schema_file.exists():
        logger.error(f"❌ 스키마 파일이 없습니다: {schema_file}")
        sys.exit(1)

    if not execute_sql_file(conn, schema_file):
        sys.exit(1)

    # 3. 검증
    if not verify_schema(conn):
        sys.exit(1)

    # 4. 테스트 삽입
    if not test_insert(conn):
        logger.warning("⚠️  테스트 데이터 삽입 실패 (선택사항)")

    # 5. 완료
    conn.close()

    logger.info("=" * 60)
    logger.info("✅ 데이터베이스 초기화 완료!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("다음 단계:")
    logger.info("  1. .env.neon을 .env로 복사: cp .env.neon .env")
    logger.info("  2. 애플리케이션 시작: python -m app.main")
    logger.info("  3. API 테스트: curl http://localhost:8001/health")
    logger.info("")

if __name__ == '__main__':
    main()
