"use client";

import { ExternalLink, Languages } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { mockLinkedResources } from "@/lib/rdf-mock";
import type { LinkedResource } from "@/types/rdf";

interface LinkedDataViewerProps {
  entityId: string;
}

export function LinkedDataViewer({ entityId }: LinkedDataViewerProps) {
  const [resources, setResources] = useState<LinkedResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    api.rdf.describeEntity(entityId)
      .then((data) => {
        if (!mounted) return;
        const linkedResources = Array.isArray(data?.resources) ? data.resources : mockLinkedResources;
        setResources(linkedResources);
        setError(null);
      })
      .catch((err) => {
        if (!mounted) return;
        setResources(mockLinkedResources);
        setError(err instanceof Error ? "Linked Data API 미연결: 데모 데이터를 표시합니다." : "데모 데이터를 표시합니다.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [entityId]);

  return (
    <section data-testid="linked-data-viewer" className="panel">
      <div className="panel-header">
        <div>
          <h3 className="text-sm font-semibold">Linked Data Viewer</h3>
          <p className="text-xs text-slate-500">DESCRIBE 기반 외부 리소스 연결 확인</p>
        </div>
        <span className="badge badge-neutral">{resources.length} resources</span>
      </div>
      <div className="panel-body space-y-3">
        {loading && <div className="text-sm text-slate-500">Linked Data 조회 중...</div>}
        {error && <div data-testid="linked-data-error" className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">{error}</div>}
        {!loading && resources.map((resource) => (
          <article key={resource.uri} data-testid="linked-resource-card" className="rounded-md border border-slate-200 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h4 className="text-sm font-semibold text-slate-900">{resource.label}</h4>
                <p className="mt-1 text-xs leading-5 text-slate-600">{resource.description}</p>
              </div>
              <a className="btn btn-ghost px-2 py-1" href={resource.uri} target="_blank" rel="noreferrer" aria-label={`Open ${resource.label}`}>
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {resource.sources.map((source) => <span key={source} className="badge badge-neutral">{source}</span>)}
              {resource.language && (
                <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                  <Languages className="h-3.5 w-3.5" />
                  {resource.language}
                </span>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
