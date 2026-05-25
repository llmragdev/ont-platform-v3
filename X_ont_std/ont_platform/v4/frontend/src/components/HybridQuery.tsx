"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { HybridAskResponse, HybridQueryType, OntologyDocInfo } from "@/types/api";
import { LlmAnswerPanel } from "@/components/LlmAnswerPanel";
import { OntologyEvidenceList } from "@/components/OntologyEvidenceList";
import { VectorSourceList } from "@/components/VectorSourceList";

const TYPE_META: Record<HybridQueryType, { label: string; color: string; desc: string }> = {
  descriptive: { label: "서술형",    color: "bg-blue-50 text-blue-700 border-blue-200",      desc: "벡터 검색 기반 서술형 답변" },
  filter:      { label: "필터 조회", color: "bg-green-50 text-green-700 border-green-200",   desc: "온톨로지 속성 기반 필터링" },
  compare:     { label: "비교 분석", color: "bg-purple-50 text-purple-700 border-purple-200", desc: "엔티티 속성 비교" },
  calculate:   { label: "수치 계산", color: "bg-amber-50 text-amber-700 border-amber-200",   desc: "METRIC 엔티티 수치 계산" },
  hybrid:      { label: "통합",      color: "bg-rose-50 text-rose-700 border-rose-200",      desc: "온톨로지 + 벡터 결합" },
};

const EXAMPLES = [
  "Submitted 상태인 Order 목록",
  "하이브리드 ORGANIZATION status: active 찾아줘",
  "PRODUCT 필터 status: inactive",
  "온톨로지 구조 설명해줘",
];

export function HybridQuery() {
  const [docs, setDocs] = useState<OntologyDocInfo[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<HybridAskResponse | null>(null);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void api.ontologyMgmt.listDocs()
      .then((list) => setDocs(Array.isArray(list) ? list : []))
      .catch(() => {});
  }, []);

  async function handleAsk() {
    if (!question.trim()) return;
    setAsking(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.hybridAsk(question, selectedDocIds.length > 0 ? selectedDocIds : undefined);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setAsking(false);
    }
  }

  function toggleDoc(docId: string) {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((d) => d !== docId) : [...prev, docId]
    );
  }

  const queryType = (result?.intent ?? result?.query_type ?? "descriptive") as HybridQueryType;
  const typeMeta = TYPE_META[queryType] ?? TYPE_META.descriptive;
  const ontItems = result?.structured_data?.ontology?.items ?? result?.results ?? [];
  const ontCount = result?.structured_data?.ontology?.count ?? result?.count ?? 0;

  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100 px-4 py-3 text-xs text-slate-600">
        <span className="font-semibold text-slate-700">통합 질의</span> — 질문 유형을 자동 감지해 온톨로지 + 벡터 검색을 조합합니다.
      </div>

      {docs.length > 0 && (
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold">검색 범위 (온톨로지 문서)</h3>
            <span className="text-xs text-slate-500">미선택 시 전체</span>
          </div>
          <div className="panel-body">
            <div className="flex flex-wrap gap-2">
              {docs.map((d) => (
                <button key={d.doc_id} type="button"
                  onClick={() => toggleDoc(d.doc_id)}
                  className={`rounded-full px-3 py-1 text-xs border transition ${
                    selectedDocIds.includes(d.doc_id)
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {d.doc_id} <span className="opacity-60">({d.entity_count})</span>
                </button>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="panel">
        <div className="panel-header"><h3 className="text-sm font-semibold">질의 입력</h3></div>
        <div className="panel-body space-y-3">
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void handleAsk()}
              placeholder="예) Submitted 상태인 Order 목록"
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
              disabled={asking}
            />
            <button className="btn btn-primary min-w-[90px]" onClick={() => void handleAsk()} disabled={asking || !question.trim()}>
              {asking ? "분석 중…" : "질의 실행"}
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
          <div className="flex items-center gap-3">
            <span className={`text-xs font-semibold border rounded-full px-3 py-1 ${typeMeta.color}`}>{typeMeta.label}</span>
            <span className="text-xs text-slate-500">{typeMeta.desc}</span>
          </div>

          {ontCount > 0 && (
            <section className="panel">
              <div className="panel-header">
                <h3 className="text-sm font-semibold">온톨로지 결과</h3>
                <span className="text-xs text-slate-500">{ontCount}건</span>
              </div>
              <div className="panel-body p-0">
                <table className="data-table">
                  <thead><tr><th>ID</th><th>유형</th><th>이름</th></tr></thead>
                  <tbody>
                    {(ontItems as Array<{ id?: string; name?: string; type?: string }>).map((item, i) => (
                      <tr key={item.id ?? i}>
                        <td className="font-mono text-xs text-slate-500">{item.id}</td>
                        <td><span className="badge badge-neutral">{item.type}</span></td>
                        <td className="font-medium">{item.name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          <LlmAnswerPanel
            answer={result.answer}
            intent={result.intent ?? result.query_type ?? "hybrid"}
            quality_metrics={result.quality_metrics}
            evidence={result.evidence}
            loading={false}
          />

          {result.ontology_evidence && result.ontology_evidence.length > 0 && (
            <OntologyEvidenceList evidence={result.ontology_evidence} />
          )}

          <VectorSourceList sources={result.sources ?? []} />
        </>
      )}
    </div>
  );
}
