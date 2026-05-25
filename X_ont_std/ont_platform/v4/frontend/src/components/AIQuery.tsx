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

export function AIQuery() {
  const [question, setQuestion] = useState(EXAMPLES[0]);
  const [result, setResult] = useState<HybridAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.hybridAsk(question);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-blue-50 text-blue-700 text-xs px-4 py-2">
        온톨로지 객체 기반 AI 질의 — filter / descriptive / hybrid 유형을 자동 분류합니다.
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">온톨로지 질의</h3>
        </div>
        <div className="panel-body space-y-3">
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void handleAsk()}
              placeholder="예) Submitted 상태인 Order 찾아줘"
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            <button className="btn btn-primary" onClick={() => void handleAsk()} disabled={loading}>
              {loading ? "분석 중…" : "질의 실행"}
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLES.map((q) => (
              <button key={q} type="button"
                className="text-xs bg-slate-100 text-slate-600 rounded-full px-2.5 py-1 hover:bg-slate-200"
                onClick={() => setQuestion(q)}
              >
                {q}
              </button>
            ))}
          </div>
          {error && <div className="text-sm text-rose-600 bg-rose-50 rounded px-3 py-2">{error}</div>}
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

          {(result.results ?? []).length > 0 && (
            <section className="panel">
              <div className="panel-header">
                <h3 className="text-sm font-semibold">필터 결과</h3>
                <span className="text-xs text-slate-500">{result.count}건</span>
              </div>
              <div className="panel-body p-0">
                <table className="data-table">
                  <thead><tr><th>ID</th><th>유형</th><th>이름</th></tr></thead>
                  <tbody>
                    {(result.results ?? []).map((r) => (
                      <tr key={r.id}>
                        <td className="font-mono text-xs text-slate-500">{r.id}</td>
                        <td><span className="badge badge-neutral">{r.type}</span></td>
                        <td className="font-medium">{r.name}</td>
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
