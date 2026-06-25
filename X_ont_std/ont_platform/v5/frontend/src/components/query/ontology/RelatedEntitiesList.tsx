"use client";

import type { RelatedEntity } from "@/types/api";
import { getEntityTypeIcon, getEntityTypeConfig } from "@/constants/entity-type-icons";

interface RelatedEntitiesListProps {
  entities: RelatedEntity[];
}

export function RelatedEntitiesList({ entities }: RelatedEntitiesListProps) {
  if (!entities || entities.length === 0) {
    return null;
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
        <h3 className="text-sm font-semibold text-slate-900">관련 개념</h3>
      </div>

      <div className="divide-y divide-slate-100">
        {entities.map((entity, idx) => {
          const config = getEntityTypeConfig(entity.type);
          const Icon = getEntityTypeIcon(entity.type);

          return (
            <div
              key={idx}
              className={`${config.bgColor} px-4 py-3 space-y-1.5`}
            >
              <div className="flex items-center gap-2">
                <Icon className="w-4 h-4" style={{ color: "#1e40af" }} />
                <span className="text-sm font-medium text-slate-900">
                  {entity.name}
                </span>
                {entity.rank !== undefined && (
                  <span className="ml-auto text-xs text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                    순위 {entity.rank}
                  </span>
                )}
              </div>

              <div className="flex flex-wrap gap-3 text-xs text-slate-500">
                {entity.relation_type && (
                  <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    관계: {entity.relation_type}
                  </span>
                )}
                {entity.confidence !== undefined && (
                  <span>신뢰도 {Math.round(entity.confidence * 100)}%</span>
                )}
                {entity.source_document && (
                  <span className="text-slate-400">
                    출처: {entity.source_document}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
