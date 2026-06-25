"use client";

import { Check, Link2, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { mockMappingCandidates } from "@/lib/rdf-mock";
import type { MappingCandidate, MappingRelationshipType, OntologyMappingRule, RDFGraphNode } from "@/types/rdf";

const RELATIONSHIPS: Array<{ value: MappingRelationshipType; label: string; description: string }> = [
  { value: "owl:sameAs", label: "owl:sameAs", description: "완전히 동일한 개념" },
  { value: "skos:exactMatch", label: "skos:exactMatch", description: "정확히 일치하는 외부 개념" },
  { value: "skos:closeMatch", label: "skos:closeMatch", description: "대체로 일치하지만 차이가 있음" },
  { value: "skos:broader", label: "skos:broader", description: "외부 개념이 더 넓음" },
  { value: "skos:narrower", label: "skos:narrower", description: "외부 개념이 더 좁음" },
  { value: "relatedTo", label: "relatedTo", description: "관련 개념" },
];

export function OntologyMappingPanel({ selectedNode }: { selectedNode?: RDFGraphNode | null }) {
  const externalUri = selectedNode?.uri ?? selectedNode?.id ?? "https://dbpedia.org/resource/Machine_learning";
  const externalLabel = selectedNode?.label ?? "Machine Learning";
  const [candidates, setCandidates] = useState<MappingCandidate[]>(mockMappingCandidates);
  const [selectedCandidate, setSelectedCandidate] = useState<MappingCandidate | null>(mockMappingCandidates[0]);
  const [relationshipType, setRelationshipType] = useState<MappingRelationshipType>("skos:closeMatch");
  const [confidence, setConfidence] = useState(84);
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.rdf.mappingCandidates(externalUri, externalLabel)
      .then((response) => {
        if (!mounted) return;
        const candidates = Array.isArray(response?.candidates) ? response.candidates : mockMappingCandidates;
        setCandidates(candidates);
        setSelectedCandidate(candidates[0] ?? null);
      })
      .catch(() => {
        if (!mounted) return;
        setCandidates(mockMappingCandidates);
        setSelectedCandidate(mockMappingCandidates[0]);
      });
    return () => {
      mounted = false;
    };
  }, [externalLabel, externalUri]);

  async function saveMapping() {
    if (!selectedCandidate) return;
    const payload: OntologyMappingRule = {
      externalUri,
      externalLabel,
      internalEntityId: selectedCandidate.id,
      internalLabel: selectedCandidate.label,
      relationshipType,
      confidence: confidence / 100,
      comment,
      approvalStatus: "pending",
    };
    try {
      await api.rdf.saveMapping(payload);
      setStatus("매핑 저장 완료");
    } catch {
      setStatus("백엔드 미연결: 데모 매핑으로 기록됨");
    }
  }

  return (
    <section data-testid="ontology-mapping-panel" className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Link2 className="h-4 w-4 text-blue-600" />
          <h3 className="text-sm font-semibold">External URI Mapping</h3>
        </div>
      </div>
      <div className="panel-body space-y-4">
        <div className="rounded-md bg-slate-50 p-3 text-xs">
          <div className="font-semibold text-slate-700">{externalLabel}</div>
          <div className="mt-1 break-all font-mono text-slate-500">{externalUri}</div>
        </div>

        <div>
          <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Recommended internal entities</div>
          <div className="space-y-2">
            {candidates.map((candidate) => (
              <button
                key={candidate.id}
                type="button"
                data-testid="mapping-candidate"
                className={`w-full rounded-md border px-3 py-2 text-left text-xs ${
                  selectedCandidate?.id === candidate.id ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
                onClick={() => {
                  setSelectedCandidate(candidate);
                  setConfidence(Math.round(candidate.similarity * 100));
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{candidate.label}</span>
                  <span className="badge badge-neutral">{Math.round(candidate.similarity * 100)}%</span>
                </div>
                <div className="mt-1 text-slate-500">{candidate.reason}</div>
              </button>
            ))}
          </div>
        </div>

        <label className="block text-xs">
          <span className="font-semibold uppercase text-slate-500">Relationship</span>
          <select
            data-testid="mapping-relationship"
            className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
            value={relationshipType}
            onChange={(event) => setRelationshipType(event.target.value as MappingRelationshipType)}
          >
            {RELATIONSHIPS.map((item) => (
              <option key={item.value} value={item.value}>{item.label} - {item.description}</option>
            ))}
          </select>
        </label>

        <label className="block text-xs">
          <span className="font-semibold uppercase text-slate-500">Confidence {confidence}%</span>
          <input
            data-testid="mapping-confidence"
            className="mt-2 w-full"
            type="range"
            min={0}
            max={100}
            value={confidence}
            onChange={(event) => setConfidence(Number(event.target.value))}
          />
        </label>

        <textarea
          data-testid="mapping-comment"
          className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
          rows={3}
          placeholder="매핑 근거 또는 검수 의견"
          value={comment}
          onChange={(event) => setComment(event.target.value)}
        />

        <button type="button" data-testid="mapping-save" className="btn btn-primary w-full gap-1.5" onClick={() => void saveMapping()}>
          <Save className="h-4 w-4" />
          Save mapping
        </button>
        {status && (
          <div data-testid="mapping-status" className="flex items-center gap-2 rounded-md bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
            <Check className="h-4 w-4" />
            {status}
          </div>
        )}
      </div>
    </section>
  );
}
