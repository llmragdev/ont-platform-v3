"use client";
import { useState } from "react";
import type { WorkflowRun, WorkflowStepRun } from "@/types/api";

interface WorkflowRunHistoryProps {
  runs: WorkflowRun[];
  loading?: boolean;
}

const STATUS_COLOR: Record<string, string> = {
  succeeded: "text-green-600 bg-green-50",
  failed: "text-red-600 bg-red-50",
  running: "text-blue-600 bg-blue-50",
  pending: "text-slate-500 bg-slate-50",
  skipped: "text-slate-400 bg-slate-50",
  waiting_approval: "text-amber-600 bg-amber-50",
};

function StepRow({ step }: { step: WorkflowStepRun }) {
  const color = STATUS_COLOR[step.status] ?? "text-slate-500";
  return (
    <div className="flex items-center justify-between py-1 text-xs">
      <div className="flex items-center gap-2">
        <span className="text-slate-400 font-mono">{step.node_type}</span>
        <span className="text-slate-600">{step.node_id}</span>
      </div>
      <span className={`rounded px-1.5 py-0.5 ${color}`}>{step.status}</span>
    </div>
  );
}

function RunRow({ run }: { run: WorkflowRun }) {
  const [expanded, setExpanded] = useState(false);
  const color = STATUS_COLOR[run.status] ?? "text-slate-500";
  const started = run.started_at ? new Date(run.started_at).toLocaleString("ko-KR") : "—";

  return (
    <div className="border border-slate-200 rounded-md overflow-hidden">
      <button
        type="button"
        className="w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-slate-50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-slate-500">{run.run_id.slice(0, 16)}…</span>
          <span className="text-xs text-slate-400">{started}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs rounded px-1.5 py-0.5 ${color}`}>{run.status}</span>
          <span className="text-xs text-slate-400">{run.steps.length}단계</span>
          <span className="text-slate-300">{expanded ? "▲" : "▼"}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2 bg-slate-50">
          {run.user_trace.length > 0 && (
            <div className="text-xs text-slate-600 space-y-0.5">
              {run.user_trace.map((t, i) => <div key={i}>• {t}</div>)}
            </div>
          )}
          <div className="divide-y divide-slate-100">
            {run.steps.map((step) => <StepRow key={step.step_id} step={step} />)}
          </div>
        </div>
      )}
    </div>
  );
}

export function WorkflowRunHistory({ runs, loading }: WorkflowRunHistoryProps) {
  if (loading) {
    return (
      <section className="panel">
        <div className="panel-header"><h3 className="text-sm font-semibold">실행 이력</h3></div>
        <div className="panel-body text-sm text-slate-400">로딩 중…</div>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">실행 이력</h3>
        <span className="badge badge-neutral">{runs.length}건</span>
      </div>
      <div className="panel-body space-y-2">
        {runs.length === 0 ? (
          <p className="text-sm text-slate-400">실행 이력이 없습니다.</p>
        ) : (
          runs.map((run) => <RunRow key={run.run_id} run={run} />)
        )}
      </div>
    </section>
  );
}
