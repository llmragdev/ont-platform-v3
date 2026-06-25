"use client";

import type { OntologyGraphResponse, OntologyGraphPayload } from "@/types/api";
import { SeedEntityCard } from "./SeedEntityCard";
import { RelatedEntitiesList } from "./RelatedEntitiesList";
import { FilteredOutToggle } from "./FilteredOutToggle";

interface OntologyGraphRendererProps {
  response: OntologyGraphResponse | null;
  onLegacyFallback?: (ontology: any[]) => void;
}

export function OntologyGraphRenderer({
  response,
  onLegacyFallback,
}: OntologyGraphRendererProps) {
  if (!response) {
    return (
      <div className="text-center py-8 text-slate-400">
        온톨로지 검색 결과가 없습니다.
      </div>
    );
  }

  // v2 구조 (ontology_graph)가 있으면 우선 사용
  if (response.ontology_graph) {
    const graph = response.ontology_graph;

    return (
      <div className="space-y-4">
        {/* 메타데이터 정보 */}
        {graph.provenance && (
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600">
            <span className="font-medium">의도:</span> {graph.policy?.intent || "분석"}
            {graph.provenance.extraction_timestamp && (
              <span className="ml-4 text-slate-500">
                시간: {new Date(graph.provenance.extraction_timestamp).toLocaleString("ko-KR")}
              </span>
            )}
          </div>
        )}

        {/* Seed Entity (중심 개념) */}
        {graph.seed_entity && (
          <div>
            <h4 className="text-sm font-semibold text-slate-900 mb-2">중심 개념</h4>
            <SeedEntityCard entity={graph.seed_entity} />
          </div>
        )}

        {/* Related Entities (관련 개념) */}
        {graph.related_entities && graph.related_entities.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-900 mb-2">
              관련 개념 ({graph.related_entities.length})
            </h4>
            <RelatedEntitiesList entities={graph.related_entities} />
          </div>
        )}

        {/* Filtered Out (필터된 항목) */}
        {graph.filtered_out && graph.filtered_out.length > 0 && (
          <div>
            <FilteredOutToggle items={graph.filtered_out} />
          </div>
        )}

        {/* 정책 정보 */}
        {graph.policy && (
          <div className="text-xs text-slate-500 border-t border-slate-200 pt-3 mt-3">
            <div className="mb-2">
              <span className="font-medium">적용된 필터:</span> {graph.policy.applied_filters || 0}개
            </div>
            {graph.policy.traversal_depth !== undefined && (
              <div>
                <span className="font-medium">확장 깊이:</span> {graph.policy.traversal_depth}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Fallback: 기존 ontology 배열 지원
  if (response.ontology && response.ontology.length > 0) {
    onLegacyFallback?.(response.ontology);
    return (
      <div className="text-center py-8 text-slate-400">
        <p className="text-sm">레거시 온톨로지 형식</p>
        <p className="text-xs text-slate-500 mt-1">
          {response.ontology.length}개 항목
        </p>
      </div>
    );
  }

  return (
    <div className="text-center py-8 text-slate-400">
      온톨로지 검색 결과가 없습니다.
    </div>
  );
}
