export interface EntityMetadata {
  entity_id: string;
  domain_id: string;
  created_by: string;
  created_at: string;
  updated_by?: string;
  updated_at?: string;
  version: number;
  tags: string[];
  description: string;
  data_quality_score?: number;
  last_validated_at?: string;
}

export interface PropertyChange {
  property_name: string;
  old_value?: unknown;
  new_value: unknown;
  changed_at: string;
  changed_by: string;
}

export interface Transformation {
  transformation_id: string;
  operation_type: "merge" | "split" | "enrich" | "filter" | string;
  input_entity_ids: string[];
  output_entity_id: string;
  transformation_rule: Record<string, unknown>;
  performed_by: string;
  performed_at: string;
  status: "completed" | "failed" | "pending";
  error_message?: string;
}

export interface LineageInfo {
  entity_id: string;
  source_entities: string[];
  transformations: Transformation[];
  data_quality_chain: number[];
  created_from_import?: Record<string, unknown>;
}

export interface EntityVersion {
  version_id: string;
  entity_id: string;
  version_number: number;
  data: Record<string, unknown>;
  changed_fields: string[];
  changed_by: string;
  changed_at: string;
  change_reason?: string;
  rollback_enabled: boolean;
}

export interface AuditLog {
  audit_id: string;
  entity_id?: string;
  action: "create" | "update" | "delete" | "import" | "merge";
  old_value?: Record<string, unknown>;
  new_value?: Record<string, unknown>;
  performed_by: string;
  performed_at: string;
  ip_address?: string;
  user_agent?: string;
  status: "success" | "failed";
  error_details?: string;
  retention_days: number;
}

export interface AuditQuery {
  entity_id?: string;
  action?: AuditLog["action"] | "";
  performed_by?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface AuditLogResponse {
  items: AuditLog[];
  total: number;
}

export interface ImpactInfo {
  affected_entities: Array<{ id: string; name: string; type: string }>;
}

export interface DataQualityInfo {
  score: number;
  factors: Record<string, number>;
}
