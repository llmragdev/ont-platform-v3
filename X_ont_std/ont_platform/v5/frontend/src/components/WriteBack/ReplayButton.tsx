"use client";

import { RotateCcw } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import type { DLQItem } from "@/types/writeback";

interface ReplayButtonProps {
  item: DLQItem;
  onSuccess: () => void;
}

function formatTime(value: string | null | undefined): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

export function ReplayButton({ item, onSuccess }: ReplayButtonProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<"idle" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function replay() {
    setLoading(true);
    setResult("idle");
    setMessage("");
    try {
      await api.writeback.replayDLQItem(item.id);
      setResult("success");
      setMessage(`${item.id} 항목이 PENDING 상태로 복구되었습니다.`);
      onSuccess();
    } catch (error) {
      const text = error instanceof Error ? error.message : "알 수 없는 오류";
      setResult("error");
      setMessage(`재실행 실패: ${text}`);
    } finally {
      setLoading(false);
    }
  }

  function close() {
    setOpen(false);
    setResult("idle");
    setMessage("");
  }

  return (
    <>
      <button
        type="button"
        data-testid={`replay-open-${item.id}`}
        className="btn btn-primary px-2 py-1 text-xs"
        disabled={loading}
        onClick={(event) => {
          event.stopPropagation();
          setOpen(true);
        }}
      >
        <RotateCcw className="mr-1 h-3.5 w-3.5" />
        재실행
      </button>

      {open && (
        <div
          data-testid="replay-modal"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4"
          onClick={close}
        >
          <div className="panel w-full max-w-lg" onClick={(event) => event.stopPropagation()}>
            <div className="panel-header">
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">아이템 재실행 확인</h2>
              <button type="button" className="btn btn-ghost px-2 py-1 text-xs" onClick={close}>
                닫기
              </button>
            </div>
            <div className="panel-body space-y-4">
              {result === "idle" && (
                <>
                  <div className="grid gap-3 text-sm md:grid-cols-2">
                    <div>
                      <div className="text-xs font-semibold uppercase text-slate-500">Item ID</div>
                      <div data-testid="replay-item-id" className="mt-1 font-mono text-slate-900 dark:text-slate-100">{item.id}</div>
                    </div>
                    <div>
                      <div className="text-xs font-semibold uppercase text-slate-500">Last failure</div>
                      <div className="mt-1 text-slate-700 dark:text-slate-200">{formatTime(item.last_error_at)}</div>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase text-slate-500">Error message</div>
                    <pre className="mt-1 max-h-28 overflow-auto rounded-md bg-slate-50 p-3 text-xs text-slate-700 dark:bg-slate-950 dark:text-slate-200">
                      {item.error_message ?? item.dlq_reason ?? "-"}
                    </pre>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    이 항목을 PENDING 상태로 되돌리고 재시도 횟수를 초기화합니다.
                  </p>
                </>
              )}

              {result === "success" && (
                <div data-testid="replay-success" className="rounded-md bg-emerald-50 p-4 text-sm font-semibold text-emerald-700">
                  {message}
                </div>
              )}
              {result === "error" && (
                <div data-testid="replay-error" className="rounded-md bg-rose-50 p-4 text-sm font-semibold text-rose-700">
                  {message}
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2 border-t border-slate-200 px-4 py-3 dark:border-slate-800">
              <button type="button" className="btn btn-ghost" disabled={loading} onClick={close}>
                {result === "idle" ? "취소" : "확인"}
              </button>
              {result === "idle" && (
                <button type="button" data-testid="replay-confirm" className="btn btn-primary" disabled={loading} onClick={replay}>
                  {loading ? "처리 중..." : "재실행 확인"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
