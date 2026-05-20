"""HTML + JSON 리포트 생성기.

결과 디렉터리: backend/integration_tests/results/
파일명: YYYYMMDD_HHMMSS_report.html / .json
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .runner import summarize

_RESULTS_DIR = Path(__file__).parent / "results"

# ── 색상 팔레트 ────────────────────────────────────────────────────────────────
_TYPE_COLORS = {
    "descriptive": "#6366f1",
    "filter":      "#f59e0b",
    "compare":     "#10b981",
    "calculate":   "#3b82f6",
    "hybrid":      "#ec4899",
}
_DEFAULT_COLOR = "#6b7280"


def _type_badge(query_type: str) -> str:
    color = _TYPE_COLORS.get(query_type, _DEFAULT_COLOR)
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:9999px;font-size:0.75rem">{query_type}</span>'
    )


def _score_bar(points: int, max_pts: int) -> str:
    pct = int(points / max_pts * 100) if max_pts else 0
    color = "#10b981" if pct >= 60 else "#f59e0b" if pct >= 30 else "#ef4444"
    return (
        f'<div style="display:flex;align-items:center;gap:6px">'
        f'<div style="flex:1;background:#e5e7eb;border-radius:4px;height:8px">'
        f'<div style="width:{pct}%;background:{color};height:8px;border-radius:4px"></div></div>'
        f'<span style="font-weight:600;min-width:36px">{points}pt</span></div>'
    )


def _rows_html(results: list[dict]) -> str:
    rows = []
    for r in results:
        status_icon = "✅" if r["passed"] else "❌"
        status_bg   = "#f0fdf4" if r["passed"] else "#fef2f2"
        detail_id   = f"detail_{r['id']}"

        score_cells = ""
        for key, label, max_pt in [
            ("type_match", "타입", 40),
            ("answer",     "응답", 20),
            ("data_cond",  "데이터", 30),
            ("latency",    "레이턴시", 10),
        ]:
            sc = r["scores"].get(key, {})
            pts = sc.get("points", 0)
            reason = sc.get("reason", "")
            score_cells += (
                f'<td style="padding:8px;vertical-align:top" title="{reason}">'
                f'{_score_bar(pts, max_pt)}</td>'
            )

        actual_type = r["response"].get("query_type", "-") if not r["error"] else "오류"
        rows.append(f"""
<tr style="background:{status_bg};cursor:pointer"
    onclick="document.getElementById('{detail_id}').hidden ^= 1">
  <td style="padding:8px;font-weight:600">{status_icon} {r['id']}</td>
  <td style="padding:8px">{r['question'][:60]}{'…' if len(r['question'])>60 else ''}</td>
  <td style="padding:8px">{_type_badge(r['expected_type'])}</td>
  <td style="padding:8px">{_type_badge(actual_type) if not r['error'] else '오류'}</td>
  {score_cells}
  <td style="padding:8px;font-weight:700">{r['total']}/100</td>
  <td style="padding:8px;color:#6b7280">{r['elapsed_ms']:.0f}ms</td>
</tr>
<tr id="{detail_id}" hidden>
  <td colspan="10" style="padding:12px 24px;background:#f8fafc;border-bottom:2px solid #e2e8f0">
    <b>설명:</b> {r.get('description','')}<br>
    <b>태그:</b> {', '.join(r.get('tags',[]))}<br>
    {'<b>오류:</b> <span style="color:red">'+r['error']+'</span><br>' if r['error'] else ''}
    <details style="margin-top:8px">
      <summary style="cursor:pointer;color:#6366f1">응답 원문 보기</summary>
      <pre style="background:#1e293b;color:#e2e8f0;padding:12px;border-radius:6px;overflow:auto;font-size:0.8rem;margin-top:8px">{json.dumps(r['response'], ensure_ascii=False, indent=2)[:3000]}</pre>
    </details>
  </td>
</tr>""")
    return "\n".join(rows)


def build_html(results: list[dict], run_ts: str) -> str:
    summary = summarize(results)
    pass_color = "#10b981" if summary.get("pass_rate", 0) >= 80 else "#f59e0b"

    by_type_rows = "".join(
        f'<tr><td style="padding:4px 8px">{t}</td>'
        f'<td style="padding:4px 8px">{v["pass"]}/{v["total"]}</td>'
        f'<td style="padding:4px 8px">'
        f'{round(v["pass"]/v["total"]*100)}%</td></tr>'
        for t, v in summary.get("by_type", {}).items()
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>통합 테스트 결과 — {run_ts}</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 24px; background: #f1f5f9; }}
  h1 {{ color: #1e293b; margin-bottom: 4px; }}
  .card {{ background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 20px;
           box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .metric {{ display: inline-block; margin: 8px 16px 8px 0; text-align: center; }}
  .metric .val {{ font-size: 2rem; font-weight: 700; }}
  .metric .lbl {{ font-size: 0.8rem; color: #6b7280; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #1e293b; color: #fff; padding: 10px 8px; text-align: left; font-size: 0.85rem; }}
  tr:hover td {{ background: #f8fafc; }}
</style>
</head>
<body>
<h1>🧪 하이브리드 질의 통합 테스트</h1>
<p style="color:#6b7280">실행 시각: {run_ts}</p>

<div class="card">
  <div class="metric">
    <div class="val" style="color:{pass_color}">{summary.get('pass',0)}/{summary.get('total',0)}</div>
    <div class="lbl">PASS / 전체</div>
  </div>
  <div class="metric">
    <div class="val" style="color:{pass_color}">{summary.get('pass_rate',0)}%</div>
    <div class="lbl">합격률</div>
  </div>
  <div class="metric">
    <div class="val">{summary.get('avg_score',0)}</div>
    <div class="lbl">평균 점수</div>
  </div>
  <div class="metric">
    <div class="val">{int(summary.get('avg_latency',0))}ms</div>
    <div class="lbl">평균 응답 시간</div>
  </div>
  <div class="metric">
    <div class="val" style="color:#ef4444">{summary.get('errors',0)}</div>
    <div class="lbl">오류</div>
  </div>
</div>

<div style="display:flex;gap:16px">
  <div class="card" style="flex:1">
    <h3 style="margin-top:0">유형별 결과</h3>
    <table>
      <tr><th>유형</th><th>PASS/전체</th><th>합격률</th></tr>
      {by_type_rows}
    </table>
  </div>
  <div class="card" style="flex:1">
    <h3 style="margin-top:0">채점 기준</h3>
    <table>
      <tr><th>항목</th><th>배점</th><th>기준</th></tr>
      <tr><td>query_type 일치</td><td>40점</td><td>기대 유형과 정확히 일치</td></tr>
      <tr><td>응답 품질</td><td>20점</td><td>answer 100자 이상 (50자↑ 시 10점)</td></tr>
      <tr><td>데이터 조건</td><td>30점</td><td>시나리오별 check 함수 통과</td></tr>
      <tr><td>레이턴시</td><td>10점</td><td>15초 미만</td></tr>
    </table>
  </div>
</div>

<div class="card">
  <h3 style="margin-top:0">시나리오별 결과 (행 클릭 시 상세 표시)</h3>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>질문</th><th>기대 유형</th><th>실제 유형</th>
        <th>타입(40)</th><th>응답(20)</th><th>데이터(30)</th><th>레이턴시(10)</th>
        <th>총점</th><th>응답 시간</th>
      </tr>
    </thead>
    <tbody>
      {_rows_html(results)}
    </tbody>
  </table>
</div>
</body>
</html>"""


# ── 저장 함수 ──────────────────────────────────────────────────────────────────

def save_reports(
    results: list[dict[str, Any]],
    run_ts: str | None = None,
) -> dict[str, Path]:
    """HTML + JSON 리포트를 results/ 디렉터리에 저장.

    Returns:
        {"html": Path, "json": Path}
    """
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ts = run_ts or datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = _RESULTS_DIR / f"{ts}_report.html"
    json_path = _RESULTS_DIR / f"{ts}_report.json"

    html_content = build_html(results, ts)
    html_path.write_text(html_content, encoding="utf-8")

    summary = summarize(results)
    json_payload = {"run_ts": ts, "summary": summary, "results": results}
    json_path.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    return {"html": html_path, "json": json_path}
