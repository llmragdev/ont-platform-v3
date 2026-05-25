import type {
  AuditLog,
  DataQualityInfo,
  EntityMetadata,
  EntityVersion,
  ImpactInfo,
  LineageInfo,
} from "@/types/metadata";

export const metadataEntityIds = ["entity-123", "entity-67", "entity-89", "entity-112"];

export const mockMetadata: Record<string, EntityMetadata> = {
  "entity-123": {
    entity_id: "entity-123",
    domain_id: "ai-voucher-2025",
    created_by: "john@example.com",
    created_at: "2026-08-05T10:30:00",
    updated_by: "jane@example.com",
    updated_at: "2026-08-10T15:45:00",
    version: 3,
    tags: ["production", "validated", "exported"],
    description: "Primary AI voucher project entity used for metadata and lineage validation.",
    data_quality_score: 92,
    last_validated_at: "2026-08-11T09:15:00",
  },
  "entity-67": {
    entity_id: "entity-67",
    domain_id: "ai-voucher-2025",
    created_by: "pipeline@example.com",
    created_at: "2026-08-07T09:20:00",
    updated_by: "pipeline@example.com",
    updated_at: "2026-08-09T12:00:00",
    version: 2,
    tags: ["derived", "review"],
    description: "Split output from the source import enrichment pipeline.",
    data_quality_score: 88,
    last_validated_at: "2026-08-09T12:05:00",
  },
  "entity-89": {
    entity_id: "entity-89",
    domain_id: "ai-voucher-2025",
    created_by: "pipeline@example.com",
    created_at: "2026-08-07T09:20:00",
    version: 1,
    tags: ["derived"],
    description: "Secondary split entity retained for downstream impact testing.",
    data_quality_score: 84,
  },
  "entity-112": {
    entity_id: "entity-112",
    domain_id: "ai-voucher-2025",
    created_by: "analyst@example.com",
    created_at: "2026-08-10T15:45:00",
    version: 1,
    tags: ["current", "merged"],
    description: "Current merged entity for lineage viewer smoke testing.",
    data_quality_score: 92,
    last_validated_at: "2026-08-11T09:15:00",
  },
};

export const mockVersions: Record<string, EntityVersion[]> = {
  "entity-123": [
    {
      version_id: "ver-entity-123-3",
      entity_id: "entity-123",
      version_number: 3,
      data: { status: "validated", budget: 50000000, owner: "Jane" },
      changed_fields: ["status", "owner"],
      changed_by: "jane@example.com",
      changed_at: "2026-08-10T15:45:00",
      change_reason: "Validated project owner and export status.",
      rollback_enabled: false,
    },
    {
      version_id: "ver-entity-123-2",
      entity_id: "entity-123",
      version_number: 2,
      data: { status: "review", budget: 50000000, owner: "John" },
      changed_fields: ["status"],
      changed_by: "john@example.com",
      changed_at: "2026-08-07T09:20:00",
      change_reason: "Moved to review after enrichment.",
      rollback_enabled: true,
    },
    {
      version_id: "ver-entity-123-1",
      entity_id: "entity-123",
      version_number: 1,
      data: { status: "created", budget: 48000000, owner: "John" },
      changed_fields: ["status", "budget", "owner"],
      changed_by: "john@example.com",
      changed_at: "2026-08-05T10:30:00",
      change_reason: "Initial import.",
      rollback_enabled: true,
    },
  ],
};

export const mockLineage: Record<string, LineageInfo> = {
  "entity-123": {
    entity_id: "entity-123",
    source_entities: ["DBpedia:VoucherProgram", "entity-45"],
    created_from_import: { source: "DBpedia", batch_id: "import-20260805-01" },
    data_quality_chain: [100, 98, 95, 92],
    transformations: [
      {
        transformation_id: "tr-001",
        operation_type: "merge",
        input_entity_ids: ["DBpedia:VoucherProgram", "entity-45"],
        output_entity_id: "entity-67",
        transformation_rule: { strategy: "prefer_recent", duplicate_key: "program_name" },
        performed_by: "pipeline@example.com",
        performed_at: "2026-08-06T08:00:00",
        status: "completed",
      },
      {
        transformation_id: "tr-002",
        operation_type: "enrich",
        input_entity_ids: ["entity-67"],
        output_entity_id: "entity-89",
        transformation_rule: { source: "Wikidata", fields: ["industry", "region"] },
        performed_by: "pipeline@example.com",
        performed_at: "2026-08-07T09:20:00",
        status: "completed",
      },
      {
        transformation_id: "tr-003",
        operation_type: "filter",
        input_entity_ids: ["entity-89"],
        output_entity_id: "entity-112",
        transformation_rule: { remove_duplicates: true, min_quality: 85 },
        performed_by: "analyst@example.com",
        performed_at: "2026-08-10T15:45:00",
        status: "completed",
      },
    ],
  },
};

export const mockImpact: Record<string, ImpactInfo> = {
  "entity-123": {
    affected_entities: [
      { id: "entity-67", name: "Voucher split output", type: "PROJECT" },
      { id: "entity-89", name: "Wikidata enriched entity", type: "PROJECT" },
      { id: "entity-112", name: "Current merged project", type: "PROJECT" },
    ],
  },
};

export const mockQuality: Record<string, DataQualityInfo> = {
  "entity-123": {
    score: 92,
    factors: {
      completeness: 94,
      consistency: 90,
      freshness: 91,
      provenance: 96,
    },
  },
};

export const mockAuditLogs: AuditLog[] = [
  {
    audit_id: "audit-001",
    entity_id: "entity-123",
    action: "import",
    new_value: { status: "created" },
    performed_by: "john@example.com",
    performed_at: "2026-08-05T10:30:00",
    ip_address: "10.10.0.12",
    user_agent: "metadata-importer/1.0",
    status: "success",
    retention_days: 365,
  },
  {
    audit_id: "audit-002",
    entity_id: "entity-123",
    action: "update",
    old_value: { status: "review" },
    new_value: { status: "validated" },
    performed_by: "jane@example.com",
    performed_at: "2026-08-10T15:45:00",
    ip_address: "10.10.0.21",
    user_agent: "ontology-console/4.0",
    status: "success",
    retention_days: 365,
  },
  {
    audit_id: "audit-003",
    entity_id: "entity-89",
    action: "merge",
    old_value: { target: "entity-89" },
    new_value: { target: "entity-112" },
    performed_by: "analyst@example.com",
    performed_at: "2026-08-10T15:40:00",
    status: "success",
    retention_days: 365,
  },
];

export function fallbackMetadata(entityId: string): EntityMetadata {
  return mockMetadata[entityId] ?? {
    ...mockMetadata["entity-123"],
    entity_id: entityId,
    description: `Mock metadata for ${entityId}.`,
  };
}

export function fallbackVersions(entityId: string): EntityVersion[] {
  return mockVersions[entityId] ?? mockVersions["entity-123"].map((version) => ({ ...version, entity_id: entityId }));
}

export function fallbackLineage(entityId: string): LineageInfo {
  return mockLineage[entityId] ?? { ...mockLineage["entity-123"], entity_id: entityId };
}

export function fallbackImpact(entityId: string): ImpactInfo {
  return mockImpact[entityId] ?? mockImpact["entity-123"];
}

export function fallbackQuality(entityId: string): DataQualityInfo {
  return mockQuality[entityId] ?? mockQuality["entity-123"];
}
