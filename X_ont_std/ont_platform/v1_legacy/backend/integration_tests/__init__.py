"""통합 테스트 패키지.

실행:
    python -m integration_tests
    python -m integration_tests --skip-seed
    python -m integration_tests --scenario S06 S07 --open-report
"""
from .run import main

__all__ = ["main"]
