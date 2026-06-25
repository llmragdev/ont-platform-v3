"use client";

import type { DLQItem } from "@/types/writeback";

interface DLQDetailModalProps {
  item: DLQItem | null;
  onClose: () => void;
}

function formatTime(value: string | null | undefined): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

export function DLQDetailModal({ item, onClose }: DLQDetailModalProps) {
  if (!item) return null;

  return (
    <div
      data-testid="dlq-detail-modal"
      className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/45 p-4"
      onClick={onClose}
    >
      <div className="panel w-full max-w-2xl" onClick={(event) => event.stopPropagation()}>
        <div className="panel-header">
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">DLQ 상세 정보</h2>
          <button type="button" data-testid="detail-close" className="btn btn-ghost px-2 py-1 text-xs" onClick={onClose}>
            닫기
          </button>
        </div>
        <div className="panel-body space-y-4">
          <div className="grid gap-3 text-sm md:grid-cols-3">
            <div>
              <div className="text-xs font-semibold uppercase text-slate-500">Item ID</div>
              <div className="mt-1 font-mono">{item.id}</div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase text-slate-500">Target</div>
              <div className="mt-1">{item.target_system}</div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase text-slate-500">Retries</div>
              <div className="mt-1">{item.retry_count}</div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase text-slate-500">DLQ at</div>
              <div className="mt-1">{formatTime(item.dlq_at)}</div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase text-slate-500">Last error</div>
              <div className="mt-1">{formatTime(item.last_error_at)}</div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase text-slate-500">Reason</div>
              <div className="mt-1">{item.dlq_reason ?? "-"}</div>
            </div>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase text-slate-500">Error message</div>
            <pre className="mt-1 max-h-32 overflow-auto rounded-md bg-slate-50 p-3 text-xs dark:bg-slate-950">
              {item.error_message ?? "-"}
            </pre>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase text-slate-500">Payload</div>
            <pre className="mt-1 max-h-52 overflow-auto rounded-md bg-slate-50 p-3 text-xs dark:bg-slate-950">
              {JSON.stringify(item.payload ?? {}, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
