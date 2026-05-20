"""통합 테스트 진입점.

사용법:
    python -m integration_tests               # 전체 15개 시나리오
    python -m integration_tests --skip-seed   # 시드 주입 건너뜀
    python -m integration_tests --scenario S06 S07  # 특정 시나리오만
    python -m integration_tests --open-report       # 완료 후 HTML 자동 오픈
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import webbrowser
from datetime import datetime

import requests

from .config import BASE_URL, DEFAULT_USER
from .reporter import save_reports
from .runner import run_all
from .seed_data import inject


def _check_server() -> bool:
    try:
        resp = requests.get(f"{BASE_URL}/api/health?user={DEFAULT_USER}", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="통합 테스트 실행기")
    parser.add_argument("--skip-seed",  action="store_true", help="시드 데이터 주입 건너뜀")
    parser.add_argument("--scenario",   nargs="+", metavar="ID", help="실행할 시나리오 ID (예: S06 S07)")
    parser.add_argument("--open-report", action="store_true", help="HTML 리포트 자동 오픈")
    parser.add_argument("--no-verbose", action="store_true", help="진행 로그 숨김")
    args = parser.parse_args(argv)

    verbose = not args.no_verbose

    # ── 서버 연결 확인 ────────────────────────────────────────────────────────
    print(f"🔍 서버 연결 확인 중 ({BASE_URL})...")
    if not _check_server():
        print(
            "❌ 서버에 연결할 수 없습니다.\n"
            "   백엔드를 먼저 실행하세요:\n"
            "   conda activate claud_be\n"
            f"   cd {BASE_URL.replace('http://localhost:8000','').strip() or 'backend'}\n"
            "   python -m uvicorn app.main:app --reload --port 8000",
            file=sys.stderr,
        )
        return 1
    print("✅ 서버 연결 OK\n")

    # ── 시드 주입 ─────────────────────────────────────────────────────────────
    if args.skip_seed:
        print("⏭  시드 주입 건너뜀 (--skip-seed)\n")
    else:
        print("🌱 온톨로지 시드 데이터 주입 중...")
        summary = inject(verbose=verbose)
        if summary.get("errors"):
            print(f"⚠  시드 주입 오류 {len(summary['errors'])}건 — 계속 진행합니다.")
        else:
            print(f"✅ 시드 주입 완료: 엔티티 {summary['entities']}개 / 관계 {summary['relationships']}개\n")

    # ── 시나리오 실행 ─────────────────────────────────────────────────────────
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"🚀 통합 테스트 시작 [{run_ts}]\n")

    results = run_all(scenario_ids=args.scenario, verbose=verbose)

    # ── 리포트 저장 ───────────────────────────────────────────────────────────
    paths = save_reports(results, run_ts=run_ts)
    print(f"\n📄 리포트 저장 완료:")
    print(f"   HTML: {paths['html']}")
    print(f"   JSON: {paths['json']}")

    if args.open_report:
        webbrowser.open(paths["html"].as_uri())

    # ── 종료 코드 ─────────────────────────────────────────────────────────────
    pass_count = sum(1 for r in results if r["passed"])
    total      = len(results)
    all_pass   = pass_count == total

    if not all_pass:
        print(f"\n⚠  실패 시나리오 {total - pass_count}개")
        for r in results:
            if not r["passed"]:
                print(f"   {r['id']}  {r['total']}pt  {r['question'][:50]}")

    return 0 if all_pass else 2


if __name__ == "__main__":
    sys.exit(main())
