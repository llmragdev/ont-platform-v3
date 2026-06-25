"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { mockImportHistory } from "@/lib/rdf-mock";
import type { ImportSourceType, OntologyImportRequest, OntologyImportResult } from "@/types/rdf";

export function useOntologyImport() {
  const [history, setHistory] = useState<OntologyImportResult[]>(mockImportHistory);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runImport(request: OntologyImportRequest): Promise<OntologyImportResult> {
    setLoading(true);
    setError(null);
    setProgress(20);

    try {
      const result = await api.rdf.importOntology(request);
      setProgress(100);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
    } catch (err) {
      const fallback: OntologyImportResult = {
        import_id: `demo-${Date.now()}`,
        status: "completed",
        source: request.type,
        identifier: request.identifier,
        domain_id: request.domain_id,
        imported_entities: request.type === "rdf_file" ? 64 : 18,
        imported_triples: request.type === "rdf_file" ? 320 : 96,
        warnings: ["Backend import endpoint unavailable; demo import result recorded."],
      };
      setError(err instanceof Error ? `데모 결과로 대체됨: ${err.message}` : "데모 결과로 대체됨");
      setProgress(100);
      setHistory((prev) => [fallback, ...prev].slice(0, 10));
      return fallback;
    } finally {
      window.setTimeout(() => setProgress(0), 900);
      setLoading(false);
    }
  }

  function defaultIdentifier(type: ImportSourceType): string {
    if (type === "dbpedia") return "https://dbpedia.org/resource/Machine_learning";
    if (type === "wikidata") return "Q11660";
    return "ai_domain_sample.ttl";
  }

  return { history, progress, loading, error, runImport, defaultIdentifier };
}
