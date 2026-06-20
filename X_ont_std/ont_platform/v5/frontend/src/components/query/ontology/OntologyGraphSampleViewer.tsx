"use client";

import type { OntologyGraphResponse } from "@/types/api";
import { OntologyGraphRenderer } from "./OntologyGraphRenderer";

// Mock 데이터: Antigravity 하네스 샘플 페이로드
const SAMPLE_ONTOLOGY_GRAPH: OntologyGraphResponse = {
  ontology_contract_version: "v2",
  ontology_graph: {
    seed_entity: {
      name: "온톨로지",
      type: "CONCEPT",
      rank: 1,
      confidence: 0.98,
      definition: "상위 구조를 정의하는 체계",
      source_document: "doc-75349dc3",
    },
    related_entities: [
      {
        name: "RAG",
        type: "CONCEPT",
        rank: 2,
        relation_type: "정의",
        confidence: 0.95,
        source_document: "doc-75349dc3",
      },
      {
        name: "벡터DB",
        type: "INSTANCE",
        rank: 3,
        relation_type: "구성",
        confidence: 0.87,
        source_document: "doc-75349dc4",
      },
    ],
    filtered_out: [
      {
        name: "김정윤",
        type: "PERSON",
        reason: "concept_explanation 의도에서 메타데이터 후순위",
        original_rank: 4,
      },
      {
        name: "이경화",
        type: "PERSON",
        reason: "concept_explanation 의도에서 메타데이터 후순위",
        original_rank: 5,
      },
      {
        name: "국방기술진흥연구소",
        type: "ORGANIZATION",
        reason: "concept_explanation 의도에서 메타데이터 후순위",
        original_rank: 6,
      },
    ],
    policy: {
      intent: "concept_explanation",
      allowed_entity_types: ["CONCEPT", "PROPERTY", "INSTANCE"],
      disallowed_entity_types: ["PERSON", "ORGANIZATION"],
      priority_relation_types: ["정의", "구성", "역할", "추론"],
      traversal_depth: 1,
      applied_filters: 3,
    },
    provenance: {
      query: "상위 온톨로지가 필요한 이유는?",
      vector_search_top1: "온톨로지 (confidence: 0.98)",
      intent_classification_confidence: 0.94,
      extraction_timestamp: new Date().toISOString(),
    },
  },
  ontology: [
    { name: "온톨로지", type: "CONCEPT" },
    { name: "RAG", type: "CONCEPT" },
    { name: "벡터DB", type: "INSTANCE" },
  ],
};

interface OntologyGraphSampleViewerProps {
  variant?: "seed-only" | "with-related" | "with-filtered" | "complete";
}

export function OntologyGraphSampleViewer({
  variant = "complete",
}: OntologyGraphSampleViewerProps) {
  let sampleData = SAMPLE_ONTOLOGY_GRAPH;

  // 변형에 따라 다른 샘플 데이터 생성
  if (variant === "seed-only") {
    sampleData = {
      ...SAMPLE_ONTOLOGY_GRAPH,
      ontology_graph: {
        ...SAMPLE_ONTOLOGY_GRAPH.ontology_graph,
        related_entities: [],
        filtered_out: [],
      },
    };
  } else if (variant === "with-related") {
    sampleData = {
      ...SAMPLE_ONTOLOGY_GRAPH,
      ontology_graph: {
        ...SAMPLE_ONTOLOGY_GRAPH.ontology_graph,
        filtered_out: [],
      },
    };
  } else if (variant === "with-filtered") {
    sampleData = {
      ...SAMPLE_ONTOLOGY_GRAPH,
      ontology_graph: {
        ...SAMPLE_ONTOLOGY_GRAPH.ontology_graph,
        related_entities: [],
      },
    };
  }

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg border border-slate-200">
      <div className="mb-4 pb-4 border-b border-slate-200">
        <h2 className="text-lg font-bold text-slate-900">
          온톨로지 그래프 샘플 (Typed Ontology Retrieval v2)
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          변형: <span className="font-mono">{variant}</span>
        </p>
      </div>

      <OntologyGraphRenderer response={sampleData} />

      <div className="mt-6 pt-4 border-t border-slate-200">
        <p className="text-xs text-slate-500 font-mono break-all">
          샘플 JSON 페이로드 크기:{" "}
          {JSON.stringify(sampleData).length} bytes
        </p>
      </div>
    </div>
  );
}
