export type WriteBackQueueStatus = "PENDING" | "CONFIRMED" | "FAILED" | "DLQ";

export interface DLQItem {
  id: string;
  target_system: string;
  payload: Record<string, unknown>;
  dlq_reason: string | null;
  dlq_at: string | null;
  last_error_at: string | null;
  error_message: string | null;
  retry_count: number;
  created_at?: string | null;
}

export interface DLQItemsResponse {
  items: DLQItem[];
  count: number;
}

export interface WriteBackStatistics {
  pending: number;
  confirmed: number;
  dlq: number;
  failed: number;
  total: number;
}

export interface ReplayResponse {
  status: "replayed" | string;
  queue_id: string;
}

export interface DLQFilters {
  targetSystem?: string;
  dateFrom?: string;
  dateTo?: string;
  errorType?: string;
}
