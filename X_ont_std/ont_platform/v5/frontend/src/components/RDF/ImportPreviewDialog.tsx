"use client";

import { AlertTriangle, FileSearch, GitCompare } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { mockImportPreview } from "@/lib/rdf-mock";
import type { ImportPreview, OntologyImportRequest } from "@/types/rdf";

type PreviewTab = "stats" | "conflicts" | "mappings";

export function ImportPreviewDialog({ request }: { request: OntologyImportRequest }) {
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [tab, setTab] = useState<PreviewTab>("stats");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function generatePreview() {
    setLoading(true);
    setMessage(null);
    try {
      const result = await api.rdf.importPreview(request);
      setPreview(result);
    } catch {
      setPreview({
        ...mockImportPreview,
        fileInfo: { ...mockImportPreview.fileInfo, name: request.identifier || mockImportPreview.fileInfo.name },
      });
      setMessage("백엔드 preview API 미연결: 데모 diff를 표시합니다.");
    } finally {
      setLoading(false);
    }
  }

  const current = preview ?? mockImportPreview;

  return (
    <section data-testid="import-preview-dialog" className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <FileSearch className="h-4 w-4 text-blue-600" />
          <h3 className="text-sm font-semibold">Import Preview & Diff</h3>
        </div>
        <button type="button" data-testid="preview-generate" className="btn btn-primary text-xs" disabled={loading} onClick={() => void generatePreview()}>
          {loading ? "Previewing..." : "Generate preview"}
        </button>
      </div>
      <div className="panel-body space-y-4">
        {message && (
          <div data-testid="preview-message" className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">{message}</div>
        )}
        <div className="flex gap-2">
          {(["stats", "conflicts", "mappings"] as const).map((key) => (
            <button
              key={key}
              type="button"
              data-testid={`preview-tab-${key}`}
              className={`btn py-1 text-xs ${tab === key ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setTab(key)}
            >
              {key}
            </button>
          ))}
        </div>

        {tab === "stats" && (
          <div data-testid="preview-stats" className="grid gap-3 text-sm md:grid-cols-2">
            <div className="rounded-md bg-slate-50 p-3">
              <div className="text-xs font-semibold uppercase text-slate-500">File</div>
              <div className="mt-1 font-semibold">{current.fileInfo.name}</div>
              <div className="text-xs text-slate-500">{current.fileInfo.triples} triples / {current.fileInfo.size} bytes</div>
            </div>
            {Object.entries(current.statistics).map(([key, value]) => (
              <div key={key} className="rounded-md bg-slate-50 p-3">
                <div className="text-xs font-semibold uppercase text-slate-500">{key}</div>
                <div className="mt-1 text-xl font-bold">{value}</div>
              </div>
            ))}
          </div>
        )}

        {tab === "conflicts" && (
          <div data-testid="preview-conflicts" className="space-y-2">
            {current.conflicts.map((conflict) => (
              <div key={conflict.id} data-testid="preview-conflict-row" className="rounded-md border border-slate-200 p-3 text-xs">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-semibold">{conflict.type}</span>
                  <span className={`badge ${conflict.severity === "error" ? "badge-high" : conflict.severity === "warning" ? "badge-medium" : "badge-neutral"}`}>
                    {conflict.severity}
                  </span>
                </div>
                <div className="grid gap-2 md:grid-cols-2">
                  <div><strong>External:</strong> {conflict.externalValue}<br /><span className="break-all text-slate-500">{conflict.externalUri}</span></div>
                  <div><strong>Internal:</strong> {conflict.internalValue ?? "-"}<br /><span className="break-all text-slate-500">{conflict.internalUri ?? "-"}</span></div>
                </div>
              </div>
            ))}
            {current.conflicts.length === 0 && <div className="text-sm text-emerald-700">충돌 없음</div>}
          </div>
        )}

        {tab === "mappings" && (
          <div data-testid="preview-mappings" className="space-y-2">
            {current.autoMappings.map((mapping) => (
              <div key={mapping.externalUri} data-testid="preview-mapping-row" className="rounded-md border border-slate-200 p-3 text-xs">
                <div className="flex items-center gap-2">
                  <GitCompare className="h-4 w-4 text-slate-500" />
                  <span className="font-semibold">{mapping.externalLabel}</span>
                  <span className="text-slate-400">→</span>
                  <span>{mapping.suggestedInternalLabel}</span>
                  <span className="badge badge-neutral ml-auto">{Math.round(mapping.confidence * 100)}%</span>
                </div>
                <div className="mt-1 text-slate-500">{mapping.suggestedRelationship}</div>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-center gap-2 rounded-md bg-blue-50 px-3 py-2 text-xs text-blue-700">
          <AlertTriangle className="h-4 w-4" />
          Preview confirms changes before commit; final import remains a separate controlled step.
        </div>
      </div>
    </section>
  );
}
