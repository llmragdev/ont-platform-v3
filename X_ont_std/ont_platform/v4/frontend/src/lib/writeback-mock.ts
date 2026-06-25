import type { DLQItem, WriteBackStatistics } from "@/types/writeback";

export const mockDLQItems: DLQItem[] = [
  {
    id: "wbq-dlq-001",
    target_system: "SAP",
    payload: { entity_id: "project-001", action: "APPROVE_PROJECT" },
    dlq_reason: "Max retries exceeded",
    dlq_at: "2026-05-25T04:40:00Z",
    last_error_at: "2026-05-25T04:38:30Z",
    error_message: "Connection timeout after 3 attempts",
    retry_count: 3,
    created_at: "2026-05-25T04:30:00Z",
  },
  {
    id: "wbq-dlq-002",
    target_system: "ERP",
    payload: { entity_id: "payment-018", action: "START_PAYMENT" },
    dlq_reason: "Permission denied",
    dlq_at: "2026-05-25T03:12:00Z",
    last_error_at: "2026-05-25T03:10:52Z",
    error_message: "External system rejected service account token",
    retry_count: 4,
    created_at: "2026-05-25T03:05:00Z",
  },
  {
    id: "wbq-dlq-003",
    target_system: "CRM",
    payload: { entity_id: "customer-077", action: "SYNC_PROFILE" },
    dlq_reason: "Validation failed",
    dlq_at: "2026-05-24T23:55:00Z",
    last_error_at: "2026-05-24T23:53:42Z",
    error_message: "Missing required external_customer_id",
    retry_count: 3,
    created_at: "2026-05-24T23:48:00Z",
  },
];

export const mockWriteBackStatistics: WriteBackStatistics = {
  pending: 8,
  confirmed: 124,
  dlq: mockDLQItems.length,
  failed: 5,
  total: 140,
};
