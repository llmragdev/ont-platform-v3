"use client";

import type { SeedEntity } from "@/types/api";
import { getEntityTypeIcon, getEntityTypeConfig } from "@/constants/entity-type-icons";

interface SeedEntityCardProps {
  entity: SeedEntity;
}

export function SeedEntityCard({ entity }: SeedEntityCardProps) {
  const config = getEntityTypeConfig(entity.type);
  const Icon = getEntityTypeIcon(entity.type);

  return (
    <div className={`border-l-4 border-l-blue-500 ${config.bgColor} rounded p-4 space-y-2`}>
      <div className="flex items-center gap-2">
        <Icon className="w-5 h-5 text-blue-600" />
        <h3 className="text-base font-semibold text-slate-900">{entity.name}</h3>
        <span className="ml-auto text-xs font-medium text-slate-500 bg-slate-100 px-2 py-1 rounded">
          {config.label}
        </span>
      </div>

      {entity.definition && (
        <p className="text-sm text-slate-600 leading-relaxed">
          {entity.definition}
        </p>
      )}

      <div className="flex flex-wrap gap-3 text-xs text-slate-500 pt-2">
        {entity.confidence !== undefined && (
          <span className="font-medium">
            신뢰도 {Math.round(entity.confidence * 100)}%
          </span>
        )}
        {entity.source_document && (
          <span className="text-slate-400">출처: {entity.source_document}</span>
        )}
      </div>
    </div>
  );
}
