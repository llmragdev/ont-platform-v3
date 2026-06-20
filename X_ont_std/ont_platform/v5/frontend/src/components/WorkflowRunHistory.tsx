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

function statusLabel(status: string): string {
  if (status === "succeeded") return "성공";
  if (status === "failed") return "실패";
  if (status === "running") return "진행 중";
  if (status === "pending") return "대기";
  if (status === "skipped") return "건너뜀";
  if (status === "waiting_approval") return "승인 대기";
  return status;
}

function StepRow({ step }: { step: WorkflowStepRun }) {
  const color = STATUS_COLOR[step.status] ?? "text-slate-500 bg-slate-50";
  return (
    <div className="flex items-center justify-between gap-3 py-1 text-xs">
      <div className="min-w-0 flex items-center gap-2">
        <span className="font-mono text-slate-400">{step.node_type}</span>
        <span className="truncate text-slate-600 dark:text-slate-300">{step.node_id}</span>
      </div>
      <span className={`rounded px-2 py-0.5 font-bold ${color}`}>{statusLabel(step.status)}</span>
    </div>
  );
}

function RunRow({ run }: { run: WorkflowRun }) {
  const [expanded, setExpanded] = useState(false);
  const color = STATUS_COLOR[run.status] ?? "text-slate-500 bg-slate-50";
  const started = run.started_at ? new Date(run.started_at).toLocaleString("ko-KR") : "-";

  return (
    <div className="overflow-hidden rounded-md border border-slate-200 dark:border-slate-800">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-800"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="min-w-0 flex items-center gap-2">
          <span className="font-mono text-xs text-slate-500">{run.run_id.slice(0, 16)}</span>
          <span className="truncate text-xs text-slate-400">{started}</span>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className={`rounded px-2 py-0.5 text-xs font-bold ${color}`}>{statusLabel(run.status)}</span>
          <span className="text-xs text-slate-400">{run.steps.length} 단계</span>
          <span className="text-slate-300">{expanded ? "▲" : "▼"}</span>
        </div>
      </button>

      {expanded && (
        <div className="space-y-3 bg-slate-50 px-3 py-3 dark:bg-slate-950">
          {run.user_trace.length > 0 && (
            <div className="space-y-0.5 text-xs text-slate-600 dark:text-slate-300">
              {run.user_trace.map((trace, index) => <div key={`${run.run_id}-trace-${index}`}>• {trace}</div>)}
            </div>
          )}
          <div className="space-y-2">
            {run.steps.length > 0 && <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-0.5">컴포넌트별 상태</div>}
            <div className="divide-y divide-slate-200 dark:divide-slate-800 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden">
              {run.steps.map((step) => <StepRow key={step.step_id} step={step} />)}
            </div>
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
        <div className="panel-body text-sm text-slate-400">불러오는 중...</div>
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
