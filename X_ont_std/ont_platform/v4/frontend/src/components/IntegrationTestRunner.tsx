"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type {
  IntegrationTestCase,
  IntegrationTestProject,
  IntegrationTestRun,
  IntegrationTestRunMeta,
  IntegrationTestSource,
} from "@/types/api";

// ── source badge ──────────────────────────────────────────────────────────────

const SOURCE_LABELS: Record<IntegrationTestSource, string> = {
  ontology: "온톨로지",
  vector: "벡터검색",
  hybrid: "하이브리드",
  no_evidence: "근거없음",
};

const SOURCE_COLORS: Record<IntegrationTestSource, string> = {
  ontology:   "bg-violet-100 text-violet-700",
  vector:     "bg-sky-100 text-sky-700",
  hybrid:     "bg-amber-100 text-amber-700",
  no_evidence:"bg-slate-100 text-slate-500",
};

function SourceBadge({ source }: { source: IntegrationTestSource }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${SOURCE_COLORS[source] ?? "bg-slate-100 text-slate-500"}`}>
      {SOURCE_LABELS[source] ?? source}
    </span>
  );
}

// ── pass/fail chip ────────────────────────────────────────────────────────────

function PassChip({ passed }: { passed: boolean }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-bold ${passed ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"}`}>
      {passed ? "PASS" : "FAIL"}
    </span>
  );
}

// ── pass rate bar ─────────────────────────────────────────────────────────────

function PassRateBar({ rate }: { rate: number }) {
  const pct = Math.round(rate * 100);
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-bold text-slate-700 w-10 text-right">{pct}%</span>
    </div>
  );
}

// ── case card ─────────────────────────────────────────────────────────────────

function CaseCard({ c }: { c: IntegrationTestCase }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`rounded-lg border ${c.passed ? "border-slate-200" : "border-red-200 bg-red-50/30"} bg-white`}>
      <button
        type="button"
        className="w-full text-left px-4 py-3 flex items-start gap-3"
        onClick={() => setOpen(!open)}
      >
        <PassChip passed={c.passed} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-slate-800">{c.id}</span>
            <SourceBadge source={c.actual_source} />
            {c.actual_source !== c.expected_source && (
              <span className="text-xs text-slate-400">
                (기대: {SOURCE_LABELS[c.expected_source] ?? c.expected_source})
              </span>
            )}
            {!c.source_matched && (
              <span className="text-xs text-red-500 font-medium">소스 불일치</span>
            )}
            {!c.keyword_matched && (
              <span className="text-xs text-red-500 font-medium">키워드 불일치</span>
            )}
          </div>
          <p className="text-xs text-slate-600 mt-0.5 truncate">{c.question}</p>
        </div>
        <span className="text-xs text-slate-400 shrink-0">{c.duration_ms}ms</span>
        <span className="text-slate-400 text-xs">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="border-t border-slate-100 px-4 py-3 space-y-3 text-xs">
          {/* answer */}
          <div>
            <div className="font-semibold text-slate-500 mb-1">답변</div>
            <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">{c.actual_answer || "(없음)"}</p>
          </div>

          {/* hits */}
          <div className="flex gap-4 text-slate-500">
            <span>온톨로지 히트: <strong className="text-slate-800">{c.ontology_hits}</strong></span>
            <span>벡터 히트: <strong className="text-slate-800">{c.vector_hits}</strong></span>
            <span>LLM: <strong className="text-slate-800">{c.llm_used ? "사용" : "미사용"}</strong></span>
          </div>

          {/* evidence */}
          {c.evidence.length > 0 && (
            <div>
              <div className="font-semibold text-slate-500 mb-1">근거</div>
              <ul className="space-y-1">
                {c.evidence.map((ev, i) => (
                  <li key={i} className={`px-2 py-1 rounded text-xs ${ev.type === "ontology" ? "bg-violet-50 text-violet-700" : "bg-sky-50 text-sky-700"}`}>
                    {ev.type === "ontology"
                      ? `[${ev.entity_type ?? "?"}] ${ev.entity ?? ""}`
                      : `[벡터] ${ev.doc_id ?? ""} score=${ev.score?.toFixed(2) ?? "?"} — ${ev.text ?? ""}`
                    }
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* keywords */}
          {c.expected_keywords.length > 0 && (
            <div className="flex flex-wrap gap-1">
              <span className="text-slate-400">기대 키워드:</span>
              {c.expected_keywords.map((kw) => {
                const found = c.actual_answer.toLowerCase().includes(kw.toLowerCase());
                return (
                  <span key={kw} className={`px-1.5 py-0.5 rounded ${found ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"}`}>
                    {kw}
                  </span>
                );
              })}
              <span className="text-slate-400 ml-1">({c.match_mode === "all" ? "모두 필요" : "하나 이상"})</span>
            </div>
          )}

          {/* note */}
          {c.note && <p className="text-slate-400 italic">{c.note}</p>}
        </div>
      )}
    </div>
  );
}

// ── run history row ───────────────────────────────────────────────────────────

function RunRow({
  run,
  selected,
  onSelect,
}: {
  run: IntegrationTestRunMeta;
  selected: boolean;
  onSelect: () => void;
}) {
  const ts = run.timestamp ? new Date(run.timestamp).toLocaleString("ko-KR") : run.run_id;
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full text-left px-4 py-3 rounded-lg border transition ${
        selected ? "border-blue-400 bg-blue-50" : "border-slate-200 bg-white hover:bg-slate-50"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-slate-500 truncate">{ts}</span>
        <span className="text-xs font-bold text-slate-700 shrink-0">
          {run.passed}/{run.total}
        </span>
      </div>
      <div className="mt-1">
        <PassRateBar rate={run.pass_rate} />
      </div>
      <div className="text-xs text-slate-400 mt-0.5">{run.duration_sec.toFixed(1)}초</div>
    </button>
  );
}

// ── main component ────────────────────────────────────────────────────────────

type SourceFilter = "all" | IntegrationTestSource;
type StatusFilter = "all" | "pass" | "fail";

export function IntegrationTestRunner() {
  const [projects, setProjects] = useState<IntegrationTestProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [runs, setRuns] = useState<IntegrationTestRunMeta[]>([]);
  const [selectedRun, setSelectedRun] = useState<IntegrationTestRun | null>(null);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [sourceFilter, setSourceFilter] = useState<SourceFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  useEffect(() => {
    api.integrationTest.listProjects()
      .then((data) => {
        setProjects(Array.isArray(data) ? data : []);
        if (Array.isArray(data) && data.length > 0) setSelectedProject(data[0].project);
      })
      .catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    if (!selectedProject) return;
    api.integrationTest.listRuns(selectedProject)
      .then((data) => setRuns(data.runs ?? []))
      .catch(() => setRuns([]));
  }, [selectedProject]);

  async function handleRun() {
    if (!selectedProject || running) return;
    setRunning(true);
    setError(null);
    try {
      const result = await api.integrationTest.run(selectedProject);
      setSelectedRun(result);
      // refresh run list
      const updated = await api.integrationTest.listRuns(selectedProject);
      setRuns(updated.runs ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  async function handleSelectRun(runId: string) {
    if (!selectedProject) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.integrationTest.getRun(selectedProject, runId);
      setSelectedRun(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const filteredCases = (selectedRun?.cases ?? []).filter((c) => {
    const srcOk = sourceFilter === "all" || c.expected_source === sourceFilter;
    const statusOk = statusFilter === "all" || (statusFilter === "pass" ? c.passed : !c.passed);
    return srcOk && statusOk;
  });

  const summary = selectedRun?.summary;

  return (
    <div className="space-y-6">
      {/* header bar */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          className="border border-slate-200 rounded px-3 py-2 text-sm"
          value={selectedProject}
          onChange={(e) => { setSelectedProject(e.target.value); setSelectedRun(null); }}
        >
          {projects.map((p) => (
            <option key={p.project} value={p.project}>{p.project}</option>
          ))}
          {projects.length === 0 && <option value="">프로젝트 없음</option>}
        </select>
        <button
          type="button"
          onClick={handleRun}
          disabled={!selectedProject || running}
          className="bg-blue-600 text-white rounded px-4 py-2 text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {running && <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />}
          {running ? "실행 중…" : "▶ 테스트 실행"}
        </button>
        {error && <span className="text-sm text-red-600">{error}</span>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* left: run history */}
        <div className="space-y-2">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">실행 이력</h2>
          {runs.length === 0 && (
            <p className="text-sm text-slate-400">실행 이력이 없습니다. 테스트를 실행해보세요.</p>
          )}
          {runs.map((r) => (
            <RunRow
              key={r.run_id}
              run={r}
              selected={selectedRun?.run_id === r.run_id}
              onSelect={() => handleSelectRun(r.run_id)}
            />
          ))}
        </div>

        {/* right: run detail */}
        <div className="lg:col-span-2 space-y-4">
          {loading && <p className="text-sm text-slate-400 animate-pulse">불러오는 중…</p>}

          {!loading && selectedRun && summary && (
            <>
              {/* summary cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: "전체", value: summary.total },
                  { label: "통과", value: summary.passed, color: "text-emerald-600" },
                  { label: "실패", value: summary.failed, color: "text-red-500" },
                  { label: "소요", value: `${summary.duration_sec.toFixed(1)}s` },
                ].map((s) => (
                  <div key={s.label} className="bg-white rounded-lg border border-slate-200 px-4 py-3 text-center">
                    <div className={`text-xl font-bold ${s.color ?? "text-slate-800"}`}>{s.value}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
                  </div>
                ))}
              </div>

              {/* pass rate */}
              <div className="bg-white rounded-lg border border-slate-200 px-4 py-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-slate-700">전체 pass율</span>
                  <span className="text-sm font-bold text-slate-800">{Math.round(summary.pass_rate * 100)}%</span>
                </div>
                <PassRateBar rate={summary.pass_rate} />
              </div>

              {/* by source breakdown */}
              <div className="bg-white rounded-lg border border-slate-200 px-4 py-3">
                <div className="text-xs font-semibold text-slate-500 uppercase mb-2">소스별 결과</div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {Object.entries(summary.by_source).map(([src, stat]) => (
                    <div key={src} className="text-center">
                      <SourceBadge source={src as IntegrationTestSource} />
                      <div className="mt-1 text-xs text-slate-500">{stat.passed}/{stat.total}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* filters */}
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-xs text-slate-400">소스:</span>
                {(["all", "ontology", "vector", "hybrid", "no_evidence"] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setSourceFilter(s)}
                    className={`text-xs px-2 py-1 rounded border ${sourceFilter === s ? "bg-blue-600 text-white border-blue-600" : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                  >
                    {s === "all" ? "전체" : SOURCE_LABELS[s]}
                  </button>
                ))}
                <span className="text-xs text-slate-400 ml-2">상태:</span>
                {(["all", "pass", "fail"] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setStatusFilter(s)}
                    className={`text-xs px-2 py-1 rounded border ${statusFilter === s ? "bg-blue-600 text-white border-blue-600" : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                  >
                    {s === "all" ? "전체" : s === "pass" ? "통과" : "실패"}
                  </button>
                ))}
                <span className="text-xs text-slate-400 ml-1">({filteredCases.length}개)</span>
              </div>

              {/* case list */}
              <div className="space-y-2">
                {filteredCases.map((c) => (
                  <CaseCard key={c.id} c={c} />
                ))}
                {filteredCases.length === 0 && (
                  <p className="text-sm text-slate-400">해당 케이스가 없습니다.</p>
                )}
              </div>
            </>
          )}

          {!loading && !selectedRun && (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
              왼쪽에서 실행 이력을 선택하거나 테스트를 실행하세요.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
