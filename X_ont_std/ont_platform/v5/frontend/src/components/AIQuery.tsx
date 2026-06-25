"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { HybridAskResponse } from "@/types/api";
import { LlmAnswerPanel } from "@/components/LlmAnswerPanel";
import { OntologyEvidenceList } from "@/components/OntologyEvidenceList";

const EXAMPLES = [
  "Submitted 상태인 Order를 찾아줘",
  "Organization 목록 보여줘",
  "status가 Approved인 항목은?",
  "온톨로지 설명해줘",
];

type ResultRow = { id: string; name?: string; type?: string };

export function AIQuery() {
  const [question, setQuestion] = useState(EXAMPLES[0]);
  const [seedDocIds, setSeedDocIds] = useState<string[]>([]);
  const [seedStatus, setSeedStatus] = useState<string | null>(null);
  const [result, setResult] = useState<HybridAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.hybridAsk(question, seedDocIds.length > 0 ? seedDocIds : undefined);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSeedExample() {
    setSeeding(true);
    setError(null);
    try {
      const seeded = await api.ontologyMgmt.seedOrderExample();
      setSeedDocIds([seeded.doc_id]);
      setSeedStatus(`${seeded.doc_id}에 예시 데이터 ${seeded.entity_count}건 입력됨`);
      setQuestion(seeded.query || "Submitted 상태인 Order를 찾아줘");
      setResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSeeding(false);
    }
  }

  const ontologyItems = (result?.structured_data?.ontology?.items ?? []) as Array<{ id?: string; name?: string; type?: string }>;
  const tableResults: ResultRow[] = (result?.results && result.results.length > 0)
    ? result.results
    : ontologyItems
        .map((item) => ({ id: item.id ?? "", name: item.name, type: item.type }))
        .filter((item) => item.id);
  const resultCount = result?.count ?? result?.structured_data?.ontology?.count ?? tableResults.length;

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-blue-50 px-4 py-2 text-xs text-blue-700">
        온톨로지 객체 기반 AI 질의입니다. 질문 유형을 자동 분류해 온톨로지와 문서 근거를 함께 확인합니다.
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">온톨로지 질의</h3>
        </div>
        <div className="panel-body space-y-3">
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && void handleAsk()}
              placeholder="예) Submitted 상태인 Order 찾아줘"
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            <button className="btn btn-primary" onClick={() => void handleAsk()} disabled={loading}>
              {loading ? "분석 중" : "질의 실행"}
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs text-emerald-700 hover:bg-emerald-200 disabled:opacity-60"
              onClick={() => void handleSeedExample()}
              disabled={seeding || loading}
            >
              {seeding ? "예시 데이터 입력 중" : "예시 데이터 입력"}
            </button>
            {EXAMPLES.map((example) => (
              <button
                key={example}
                type="button"
                className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-200"
                onClick={() => setQuestion(example)}
              >
                {example}
              </button>
            ))}
          </div>

          {seedStatus && (
            <div className="rounded-md bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
              {seedStatus}
              {seedDocIds.length > 0 && <span className="ml-2 font-mono">검색 문서: {seedDocIds.join(", ")}</span>}
            </div>
          )}
          {error && <div className="rounded bg-rose-50 px-3 py-2 text-sm text-rose-600">{error}</div>}
        </div>
      </section>

      {result && (
        <>
          <LlmAnswerPanel
            answer={result.answer}
            intent={result.intent ?? result.query_type ?? "unknown"}
            quality_metrics={result.quality_metrics}
            evidence={result.evidence}
            loading={false}
          />

          {result.ontology_evidence && result.ontology_evidence.length > 0 && (
            <OntologyEvidenceList evidence={result.ontology_evidence} />
          )}

          {tableResults.length > 0 && (
            <section className="panel">
              <div className="panel-header">
                <h3 className="text-sm font-semibold">필터 결과</h3>
                <span className="text-xs text-slate-500">{resultCount}건</span>
              </div>
              <div className="panel-body p-0">
                <table className="data-table">
                  <thead>
                    <tr><th>ID</th><th>유형</th><th>이름</th></tr>
                  </thead>
                  <tbody>
                    {tableResults.map((row) => (
                      <tr key={row.id}>
                        <td className="font-mono text-xs text-slate-500">{row.id}</td>
                        <td><span className="badge badge-neutral">{row.type}</span></td>
                        <td className="font-medium">{row.name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
