"use client";

import { History, Loader2, RotateCcw, ShieldCheck, Tag } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { fallbackMetadata, fallbackQuality, fallbackVersions } from "@/lib/metadata-mock";
import type { DataQualityInfo, EntityMetadata, EntityVersion } from "@/types/metadata";

export function MetadataPanel({
  entityId,
  onVersionRollback,
}: {
  entityId: string;
  onVersionRollback?: (versionId: string) => void;
}) {
  const [metadata, setMetadata] = useState<EntityMetadata | null>(null);
  const [versions, setVersions] = useState<EntityVersion[]>([]);
  const [quality, setQuality] = useState<DataQualityInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setNotice(null);
      try {
        const [metadataRes, versionRes, qualityRes] = await Promise.all([
          api.metadata.getMetadata(entityId),
          api.metadata.getVersions(entityId),
          api.metadata.getDataQuality(entityId),
        ]);
        if (!cancelled) {
          setMetadata(metadataRes);
          setVersions(versionRes);
          setQuality(qualityRes);
        }
      } catch {
        if (!cancelled) {
          setMetadata(fallbackMetadata(entityId));
          setVersions(fallbackVersions(entityId));
          setQuality(fallbackQuality(entityId));
          setNotice("Using mock metadata until the v4 API is available.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [entityId]);

  async function handleRollback(version: EntityVersion) {
    try {
      const nextMetadata = await api.metadata.rollbackVersion(entityId, version.version_id);
      setMetadata(nextMetadata);
      setNotice(`Rollback requested for v${version.version_number}.`);
    } catch {
      setNotice(`Mock rollback selected for v${version.version_number}.`);
    }
    onVersionRollback?.(version.version_id);
  }

  const score = quality?.score ?? metadata?.data_quality_score ?? 0;

  return (
    <section data-testid="metadata-panel" className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-blue-600" />
          <h3 className="text-sm font-semibold">Metadata Panel</h3>
        </div>
        {loading && <Loader2 className="h-4 w-4 animate-spin text-slate-400" />}
      </div>

      <div className="panel-body space-y-4">
        {notice && (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
            {notice}
          </div>
        )}

        {metadata && (
          <>
            <div className="grid gap-3 text-sm md:grid-cols-2">
              <div>
                <div className="text-xs font-semibold uppercase text-slate-500">Entity ID</div>
                <div className="font-mono text-slate-900">{metadata.entity_id}</div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase text-slate-500">Domain</div>
                <div className="font-mono text-slate-900">{metadata.domain_id}</div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase text-slate-500">Created</div>
                <div>{new Date(metadata.created_at).toLocaleString()} by {metadata.created_by}</div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase text-slate-500">Updated</div>
                <div>
                  {metadata.updated_at ? new Date(metadata.updated_at).toLocaleString() : "-"}
                  {metadata.updated_by ? ` by ${metadata.updated_by}` : ""}
                </div>
              </div>
            </div>

            <p className="text-sm text-slate-600">{metadata.description}</p>

            <div>
              <div className="mb-1 flex items-center justify-between text-xs font-semibold uppercase text-slate-500">
                <span>Quality Score</span>
                <span>{score}/100</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
                />
              </div>
              {quality && (
                <div className="mt-2 grid gap-2 md:grid-cols-4">
                  {Object.entries(quality.factors).map(([key, value]) => (
                    <div key={key} className="rounded-md bg-slate-50 px-2 py-1">
                      <div className="text-[10px] uppercase text-slate-400">{key}</div>
                      <div className="text-xs font-semibold">{value}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
                <History className="h-3.5 w-3.5" />
                Version History
              </div>
              <div className="space-y-2">
                {versions.map((version) => (
                  <div key={version.version_id} className="flex items-start justify-between gap-3 rounded-md border border-slate-200 px-3 py-2">
                    <div>
                      <div className="text-sm font-semibold">v{version.version_number}</div>
                      <div className="text-xs text-slate-500">
                        {new Date(version.changed_at).toLocaleString()} by {version.changed_by}
                      </div>
                      <div className="mt-1 text-xs text-slate-600">
                        {version.changed_fields.join(", ")}{version.change_reason ? ` - ${version.change_reason}` : ""}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn btn-ghost px-2 py-1 text-xs"
                      disabled={!version.rollback_enabled}
                      onClick={() => void handleRollback(version)}
                    >
                      <RotateCcw className="mr-1 h-3.5 w-3.5" />
                      Rollback
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
                <Tag className="h-3.5 w-3.5" />
                Tags
              </div>
              <div className="flex flex-wrap gap-1.5">
                {metadata.tags.map((tag) => (
                  <span key={tag} className="badge badge-neutral">{tag}</span>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
