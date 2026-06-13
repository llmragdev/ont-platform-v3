export type SyncStatus = "PENDING" | "SYNCED" | "FAILED" | "SKIPPED" | "SYNCING" | string;

export interface ChangelogEntry {
  changelog_id?: string;
  id?: string;
  entity_id: string;
  entity_type?: string;
  action: string;
  action_type?: string;
  performed_by?: string;
  user?: string;
  performed_at?: string;
  timestamp?: string;
  sync_status?: SyncStatus;
  old_status?: string;
  new_status?: string;
  old_value?: Record<string, unknown>;
  new_value?: Record<string, unknown>;
  target_system?: string;
  synced_at?: string | null;
  retry_count?: number;
  attempt_count?: number;
  errors?: Array<{ message?: string } | string>;
  params?: Record<string, unknown>;
}

export interface ChangelogFilters {
  domainId?: string;
  entityId?: string;
  actionType?: string;
  user?: string;
  syncStatus?: string;
  dateFrom?: string;
  dateTo?: string;
}

export interface ChangelogHistoryResponse {
  items?: ChangelogEntry[];
  changelogs?: ChangelogEntry[];
  total?: number;
  page?: number;
  page_size?: number;
  stats?: {
    success_rate?: number;
    failed_count?: number;
    pending_count?: number;
    average_retries?: number;
  };
}
