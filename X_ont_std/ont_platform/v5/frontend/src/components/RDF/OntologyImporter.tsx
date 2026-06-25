"use client";

import { Database, FileUp, Globe2, UploadCloud } from "lucide-react";
import { useState } from "react";
import { useOntologyImport } from "@/hooks/useOntologyImport";
import type { ImportSourceType } from "@/types/rdf";

const SOURCES: Array<{ type: ImportSourceType; label: string; icon: typeof Globe2 }> = [
  { type: "dbpedia", label: "DBpedia", icon: Globe2 },
  { type: "wikidata", label: "Wikidata", icon: Database },
  { type: "rdf_file", label: "RDF File", icon: FileUp },
];

export function OntologyImporter() {
  const { history, progress, loading, error, runImport, defaultIdentifier } = useOntologyImport();
  const [type, setType] = useState<ImportSourceType>("dbpedia");
  const [identifier, setIdentifier] = useState(defaultIdentifier("dbpedia"));
  const [domainId, setDomainId] = useState("ai");

  function changeType(next: ImportSourceType) {
    setType(next);
    setIdentifier(defaultIdentifier(next));
  }

  async function submit() {
    if (!identifier.trim() || !domainId) return;
    await runImport({ type, identifier: identifier.trim(), domain_id: domainId });
  }

  return (
    <section data-testid="ontology-importer" className="panel">
      <div className="panel-header">
        <div>
          <h3 className="text-sm font-semibold">Import External Ontology</h3>
          <p className="text-xs text-slate-500">DBpedia, Wikidata, RDF 파일 소스를 도메인 그래프에 연결</p>
        </div>
      </div>
      <div className="panel-body space-y-4">
        <div className="grid gap-2 md:grid-cols-3">
          {SOURCES.map((source) => {
            const Icon = source.icon;
            return (
              <button
                key={source.type}
                type="button"
                data-testid={`import-type-${source.type}`}
                className={`rounded-md border px-3 py-3 text-left transition ${
                  type === source.type ? "border-blue-500 bg-blue-50 text-blue-700" : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
                onClick={() => changeType(source.type)}
              >
                <Icon className="mb-2 h-4 w-4" />
                <div className="text-sm font-semibold">{source.label}</div>
              </button>
            );
          })}
        </div>

        <div className="grid gap-3 md:grid-cols-[1fr_180px]">
          {type === "rdf_file" ? (
            <input
              data-testid="rdf-file-input"
              type="file"
              accept=".rdf,.ttl,.n3,.nt"
              className="rounded-md border border-slate-200 px-3 py-2 text-sm"
              onChange={(event) => setIdentifier(event.target.files?.[0]?.name ?? "")}
            />
          ) : (
            <input
              data-testid="import-identifier"
              className="rounded-md border border-slate-200 px-3 py-2 text-sm"
              value={identifier}
              placeholder={type === "dbpedia" ? "https://dbpedia.org/resource/Machine_learning" : "Q11660"}
              onChange={(event) => setIdentifier(event.target.value)}
            />
          )}
          <select
            data-testid="import-domain"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            value={domainId}
            onChange={(event) => setDomainId(event.target.value)}
          >
            <option value="ai">AI/ML Domain</option>
            <option value="biology">Biology Domain</option>
            <option value="manufacturing">Manufacturing Domain</option>
          </select>
        </div>

        <div className="flex items-center justify-between gap-3">
          <button type="button" data-testid="import-submit" className="btn btn-primary gap-1.5" disabled={loading || !identifier.trim()} onClick={() => void submit()}>
            <UploadCloud className="h-4 w-4" />
            {loading ? "Importing..." : "Import"}
          </button>
          {progress > 0 && (
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
              <div data-testid="import-progress" className="h-full bg-blue-600 transition-all" style={{ width: `${progress}%` }} />
            </div>
          )}
        </div>

        {error && <div data-testid="import-error" className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">{error}</div>}

        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase text-slate-500">Import History</h4>
          <div className="space-y-2">
            {history.map((item) => (
              <div key={item.import_id} data-testid="import-history-item" className="flex items-center justify-between rounded-md border border-slate-100 px-3 py-2 text-xs">
                <div>
                  <span className="font-semibold">{item.source}</span>
                  <span className="mx-2 text-slate-400">/</span>
                  <span>{item.identifier}</span>
                </div>
                <span className="badge badge-low">{item.imported_triples} triples</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
