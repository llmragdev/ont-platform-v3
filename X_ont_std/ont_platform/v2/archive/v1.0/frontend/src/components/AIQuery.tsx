"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import type { AskResponse } from "@/types/api";

export function AIQuery({ user }: { user: string }) {
  const [question, setQuestion] = useState("O001 주문 승인해도 될까?");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.ask(user, question);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-blue-50 text-blue-700 text-xs px-4 py-2">
        온톨로지 객체 ID(예: O001, C002, P003)가 포함된 질문에 답변합니다.
        PDF 문서 기반 질의는 <strong>RAG 문서 질의</strong> 메뉴를 이용하세요.
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">온톨로지 질의</h3>
          <span className="text-xs text-slate-500">예) O001 주문 승인해도 될까? / C002 고객의 위험도는?</span>
        </div>
        <div className="panel-body space-y-3">
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && handleAsk()}
              placeholder="객체 ID가 포함된 질문을 입력하세요 (예: O001, C002)"
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            <button type="button" className="btn btn-primary" onClick={handleAsk} disabled={loading}>
              {loading ? "분석 중…" : "질의 실행"}
            </button>
          </div>
          {error && <div className="text-sm text-rose-600">{error}</div>}
        </div>
      </section>

      {result && (
        <>
          <section className="panel">
            <div className="panel-header">
              <h3 className="text-sm font-semibold">AI 답변</h3>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className={`badge ${result.llm_provider === "gemini" ? "badge-low" : "badge-medium"}`}>
                  {result.llm_provider} ({result.llm_model})
                </span>
                <span>{result.latency_ms} ms</span>
              </div>
            </div>
            <div className="panel-body space-y-2">
              {result.warning && (
                <div className="rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-xs px-3 py-2">
                  ⚠ {result.warning}
                </div>
              )}
              <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans">{result.answer}</pre>
              <div className="text-xs text-slate-500 pt-2 border-t border-slate-100">
                <strong>Trace:</strong> {result.steps.map((step) => step.name).join(" → ")}
              </div>
              {result.available_actions.length > 0 && (
                <div className="text-xs text-slate-500">
                  <strong>추천 액션:</strong>{" "}
                  {result.available_actions.map((action) => (
                    <span key={action} className="badge badge-neutral mr-1">{action}</span>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h3 className="text-sm font-semibold">검색 근거 (BM25)</h3>
              <span className="text-xs text-slate-500">{result.evidence.length}건</span>
            </div>
            <div className="panel-body space-y-3">
              {result.evidence.map((evidence) => (
                <div key={evidence.document_id} className="rounded-md border border-slate-200 p-3">
                  <div className="flex justify-between items-center">
                    <div className="text-sm font-medium">
                      {evidence.title} <span className="text-xs text-slate-400">({evidence.document_id})</span>
                    </div>
                    <span className="badge badge-neutral">score {evidence.score}</span>
                  </div>
                  <div className="text-xs text-slate-600 mt-1 leading-relaxed">{evidence.text}</div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
