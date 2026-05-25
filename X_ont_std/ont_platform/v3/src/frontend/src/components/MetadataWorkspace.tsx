"use client";

import { useState } from "react";
import { AuditLogTable } from "@/components/AuditLogTable";
import { LineageViewer } from "@/components/LineageViewer";
import { MetadataPanel } from "@/components/MetadataPanel";
import { metadataEntityIds } from "@/lib/metadata-mock";

export function MetadataWorkspace() {
  const [entityId, setEntityId] = useState(metadataEntityIds[0]);
  const [input, setInput] = useState(metadataEntityIds[0]);

  function applyEntity() {
    const next = input.trim();
    if (next) setEntityId(next);
  }

  return (
    <div data-testid="metadata-workspace" className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-xs font-semibold text-slate-500">Entity ID</label>
          <div className="flex gap-2">
            <input
              data-testid="metadata-entity-input"
              className="w-56 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => { if (event.key === "Enter") applyEntity(); }}
            />
            <button type="button" data-testid="metadata-entity-apply" className="btn btn-primary" onClick={applyEntity}>
              Load
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {metadataEntityIds.map((id) => (
            <button
              key={id}
              type="button"
              className={`rounded-md border px-2 py-1 text-xs font-semibold ${
                entityId === id ? "border-blue-200 bg-blue-50 text-blue-700" : "border-slate-200 bg-white text-slate-600"
              }`}
              onClick={() => {
                setEntityId(id);
                setInput(id);
              }}
            >
              {id}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
        <MetadataPanel entityId={entityId} />
        <LineageViewer entityId={entityId} onEntityClick={(id) => { setEntityId(id); setInput(id); }} />
      </div>

      <AuditLogTable entityId={entityId} />
    </div>
  );
}
