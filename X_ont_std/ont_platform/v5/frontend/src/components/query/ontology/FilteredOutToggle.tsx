"use client";

import { useState } from "react";
import type { FilteredOutEntity } from "@/types/api";
import { getEntityTypeConfig } from "@/constants/entity-type-icons";
import { ChevronDown } from "lucide-react";

interface FilteredOutToggleProps {
  items: FilteredOutEntity[];
}

export function FilteredOutToggle({ items }: FilteredOutToggleProps) {
  const [expanded, setExpanded] = useState(false);

  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 border border-dashed border-slate-300 rounded-lg bg-white hover:bg-slate-50 transition-colors"
      >
        <span className="text-sm font-medium text-slate-700">
          필터된 항목 ({items.length}개)
        </span>
        <ChevronDown
          className={`w-4 h-4 text-slate-500 transition-transform ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {expanded && (
        <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 bg-slate-50">
          {items.map((item, idx) => {
            const config = getEntityTypeConfig(item.type);

            return (
              <div key={idx} className="px-4 py-3 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-slate-600 bg-white px-2 py-1 rounded border border-slate-200">
                    {config.label}
                  </span>
                  <span className="text-sm text-slate-900">{item.name}</span>
                </div>
                <p className="text-xs text-slate-500 italic">
                  이유: {item.reason}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
