"use client";

import type { DLQItem } from "@/types/writeback";
import { ReplayButton } from "./ReplayButton";

interface DLQItemTableProps {
  items: DLQItem[];
  loading: boolean;
  onReplaySuccess: () => void;
  onSelectItem: (item: DLQItem) => void;
}

function formatTime(value: string | null | undefined): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function reasonOf(item: DLQItem): string {
  return item.dlq_reason ?? item.error_message ?? "-";
}

export function DLQItemTable({ items, loading, onReplaySuccess, onSelectItem }: DLQItemTableProps) {
  const sorted = [...items].sort((a, b) => {
    const left = a.dlq_at ? new Date(a.dlq_at).getTime() : 0;
    const right = b.dlq_at ? new Date(b.dlq_at).getTime() : 0;
    return right - left;
  });

  return (
    <div className="overflow-auto">
      <table data-testid="dlq-table" className="data-table">
        <thead>
          <tr>
            <th>Item ID</th>
            <th>대상 시스템</th>
            <th>DLQ 사유</th>
            <th>DLQ 시간</th>
            <th>재시도</th>
            <th>액션</th>
          </tr>
        </thead>
        <tbody>
          {loading && sorted.length === 0 && (
            <tr>
              <td colSpan={6} className="py-8 text-center text-slate-500">DLQ 항목을 불러오는 중...</td>
            </tr>
          )}
          {!loading && sorted.length === 0 && (
            <tr>
              <td colSpan={6} className="py-8 text-center text-slate-400">DLQ 아이템이 없습니다.</td>
            </tr>
          )}
          {sorted.map((item) => (
            <tr
              key={item.id}
              data-testid="dlq-row"
              className="clickable"
              onClick={() => onSelectItem(item)}
            >
              <td className="font-mono text-xs">{item.id}</td>
              <td>{item.target_system}</td>
              <td>
                <div className="max-w-xs truncate" title={reasonOf(item)}>
                  {reasonOf(item)}
                </div>
              </td>
              <td className="text-xs text-slate-500">{formatTime(item.dlq_at)}</td>
              <td>
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{item.retry_count}</span>
                  {item.retry_count >= 3 && <span className="badge badge-medium">최대 도달</span>}
                </div>
              </td>
              <td>
                <ReplayButton item={item} onSuccess={onReplaySuccess} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
