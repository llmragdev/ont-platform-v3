"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type {
  HybridAskResponse,
  HybridQueryType,
  OntologyDocInfo,
} from "@/types/api";

// ── 질문 유형 배지 ──────────────────────────────────────────────────────────
const TYPE_META: Record<HybridQueryType, { label: string; color: string; desc: string }> = {
  descriptive: { label: "서술형",    color: "bg-blue-50 text-blue-700 border-blue-200",    desc: "PDF 문서에서 서술형 답변을 생성합니다." },
  filter:      { label: "필터 조회", color: "bg-green-50 text-green-700 border-green-200",  desc: "온톨로지에서 조건에 맞는 항목을 필터링합니다." },
  compare:     { label: "비교 분석", color: "bg-purple-50 text-purple-700 border-purple-200", desc: "온톨로지 엔티티를 속성 기준으로 비교합니다." },
  calculate:   { label: "수치 계산", color: "bg-amber-50 text-amber-700 border-amber-200",  desc: "METRIC 엔티티에서 수치를 추출해 계산합니다." },
  hybrid:      { label: "통합",      color: "bg-rose-50 text-rose-700 border-rose-200",     desc: "온톨로지 구조형 데이터 + RAG를 동시에 활용합니다." },
};

// ── 예시 질문 ───────────────────────────────────────────────────────────────
const EXAMPLE_QUESTIONS = [
  "Serverless 방식으로 과금되는 기능들은 무엇인가요?",
  "Virtual Warehouse와 Snowpipe를 비교해주세요.",
  "전체 고객 수 대비 $1M 이상 고객 비율은?",
  "Snowflake의 창립자는 누구인가요?",
  "한국 고객은 몇 개 있고, 주요 활용 사례는?",
];

// ── 구조형 결과 렌더러 ───────────────────────────────────────────────────────
function OntologyResultPanel({ result }: { result: HybridAskResponse["ontology_result"] }) {
  if (!result || result.mode === "none") return null;

  if (result.mode === "compare" && result.table) {
    const { headers, rows } = result.table;
    return (
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-xs">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left font-semibold text-slate-500">이름</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-500">유형</th>
              {headers.map((h) => (
                <th key={h} className="px-3 py-2 text-left font-semibold text-slate-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2 font-medium text-slate-800">{row.name}</td>
                <td className="px-3 py-2">
                  <span className="bg-slate-100 text-slate-600 rounded px-1.5 py-0.5 text-[10px] font-medium">{row.type}</span>
                </td>
                {headers.map((h) => (
                  <td key={h} className="px-3 py-2 text-slate-600">{String(row.props[h] ?? "-")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (result.mode === "calculate" && result.calc) {
    const { calc } = result;
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
        {calc.error ? (
          <p className="text-sm text-amber-700">{calc.error}</p>
        ) : (
          <>
            <div className="text-2xl font-bold text-amber-800 mb-1">
              {typeof calc.result === "number" ? calc.result.toLocaleString(undefined, { maximumFractionDigits: 4 }) : String(calc.result ?? "-")}
              {calc.unit && <span className="text-base font-normal ml-1">{calc.unit}</span>}
            </div>
            <p className="text-xs text-amber-600 mb-3">{calc.operation.toUpperCase()} 연산</p>
            <div className="space-y-1">
              {calc.operands.map((op, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-amber-700">
                  <span className="font-medium">{op.name}</span>
                  <span className="text-amber-500">→</span>
                  <span className="font-mono">{op.value.toLocaleString()} {op.unit}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  if (result.mode === "filter" && result.rows && result.rows.length > 0) {
    return (
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-xs">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left font-semibold text-slate-500 w-16">ID</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-500 w-24">유형</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-500">이름</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-500">속성</th>
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row, i) => {
              const r = row as Record<string, unknown>;
              return (
                <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono text-slate-400">{String(r.id ?? "")}</td>
                  <td className="px-3 py-2">
                    <span className="bg-slate-100 text-slate-600 rounded px-1.5 py-0.5 text-[10px] font-medium">{String(r.type ?? "")}</span>
                  </td>
                  <td className="px-3 py-2 font-medium text-slate-800">{String(r.name ?? "")}</td>
                  <td className="px-3 py-2 text-slate-500 text-[11px]">
                    {Object.entries((r.properties as Record<string, unknown>) ?? {})
                      .slice(0, 3)
                      .map(([k, v]) => `${k}: ${v}`)
                      .join(" · ") || "-"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  }

  if (result.mode === "relations" && result.rows && result.rows.length > 0) {
    return (
      <div className="space-y-1">
        {result.rows.map((row, i) => {
          const r = row as Record<string, unknown>;
          return (
            <div key={i} className="flex items-center gap-2 text-sm bg-slate-50 rounded px-3 py-2">
              <span className="font-medium text-slate-700">{String(r.from_name ?? r.from_id ?? "")}</span>
              <span className="text-slate-400">→</span>
              <span className="text-blue-600 font-medium">{String(r.relation ?? "")}</span>
              <span className="text-slate-400">→</span>
              <span className="font-medium text-slate-700">{String(r.to_name ?? r.to_id ?? "")}</span>
            </div>
          );
        })}
      </div>
    );
  }

  return null;
}

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
export function HybridQuery({ user }: { user: string }) {
  const [docs, setDocs] = useState<OntologyDocInfo[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<HybridAskResponse | null>(null);
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const res = await api.ontologyMgmt.listDocs();
        setDocs(res.ontologies);
      } catch {
        // 온톨로지 없으면 무시
      }
    })();
  }, []);

  async function handleAsk() {
    if (!question.trim()) return;
    setAsking(true);
    setAskError(null);
    setResult(null);
    try {
      const res = await api.hybridAsk(user, question, selectedDocIds.length > 0 ? selectedDocIds : undefined);
      setResult(res);
    } catch (err) {
      setAskError(err instanceof Error ? err.message : String(err));
    } finally {
      setAsking(false);
    }
  }

  function toggleDoc(docId: string) {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((d) => d !== docId) : [...prev, docId]
    );
  }

  const typeMeta = result ? TYPE_META[result.query_type] ?? TYPE_META.descriptive : null;
  const hasStructured =
    result &&
    result.ontology_result &&
    result.ontology_result.mode !== "none" &&
    (result.ontology_result.rows?.length ||
      result.ontology_result.table?.rows?.length ||
      result.ontology_result.calc);

  return (
    <div className="space-y-4">
      {/* ── 안내 배너 ── */}
      <div className="rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100 px-4 py-3 text-xs text-slate-600">
        <span className="font-semibold text-slate-700">통합 질의 (Hybrid Query)</span> — 질문 유형을 자동 감지해
        온톨로지 구조형 데이터와 RAG 문서 검색을 조합해 답변합니다.
      </div>

      {/* ── 문서 범위 선택 ── */}
      {docs.length > 0 && (
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold">검색 범위 (온톨로지 문서)</h3>
            <span className="text-xs text-slate-500">미선택 시 전체 문서 대상</span>
          </div>
          <div className="panel-body">
            <div className="flex flex-wrap gap-2">
              {docs.map((d) => (
                <button
                  key={d.doc_id}
                  type="button"
                  onClick={() => toggleDoc(d.doc_id)}
                  className={`rounded-full px-3 py-1 text-xs border transition ${
                    selectedDocIds.includes(d.doc_id)
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {d.filename}
                  <span className="ml-1 opacity-60">({d.entity_count})</span>
                </button>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── 질의 입력 ── */}
      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">질의 입력</h3>
        </div>
        <div className="panel-body space-y-3">
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void handleAsk()}
              placeholder="예) Serverless 과금 기능은? / 창립자 비교해줘 / 총 고객 수는?"
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
              disabled={asking}
            />
            <button
              type="button"
              className="btn btn-primary min-w-[90px]"
              onClick={() => void handleAsk()}
              disabled={asking || !question.trim()}
            >
              {asking ? "분석 중…" : "질의 실행"}
            </button>
          </div>

          {/* 예시 질문 */}
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                className="text-xs bg-slate-100 text-slate-600 rounded-full px-2.5 py-1 hover:bg-slate-200 transition"
                onClick={() => setQuestion(q)}
              >
                {q}
              </button>
            ))}
          </div>
          {askError && <div className="text-sm text-rose-600 bg-rose-50 rounded px-3 py-2">{askError}</div>}
        </div>
      </section>

      {/* ── 결과 ── */}
      {result && (
        <>
          {/* 질문 유형 배지 */}
          <div className="flex items-center gap-3">
            <span
              className={`text-xs font-semibold border rounded-full px-3 py-1 ${typeMeta?.color}`}
            >
              {typeMeta?.label}
            </span>
            <span className="text-xs text-slate-500">{typeMeta?.desc}</span>
            <span className="ml-auto text-xs text-slate-400">{result.latency_ms} ms</span>
          </div>

          {/* 분류 상세 */}
          {result.classification.entities?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 items-center text-xs">
              <span className="text-slate-500">감지된 엔티티:</span>
              {result.classification.entities.map((e) => (
                <span key={e} className="bg-blue-50 text-blue-700 rounded px-2 py-0.5 font-medium">{e}</span>
              ))}
              {result.classification.entity_type && (
                <span className="bg-slate-100 text-slate-600 rounded px-2 py-0.5">{result.classification.entity_type}</span>
              )}
            </div>
          )}

          {/* 구조형 결과 (온톨로지) */}
          {hasStructured && (
            <section className="panel">
              <div className="panel-header">
                <h3 className="text-sm font-semibold">온톨로지 구조형 결과</h3>
                <span className="text-xs text-slate-500 uppercase tracking-wide">{result.ontology_result.mode}</span>
              </div>
              <div className="panel-body">
                <OntologyResultPanel result={result.ontology_result} />
              </div>
            </section>
          )}

          {/* AI 서술형 답변 */}
          <section className="panel">
            <div className="panel-header">
              <h3 className="text-sm font-semibold">AI 답변</h3>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className={`badge ${result.llm_provider === "gemini" ? "badge-low" : "badge-medium"}`}>
                  {result.llm_provider} ({result.llm_model})
                </span>
              </div>
            </div>
            <div className="panel-body space-y-2">
              {result.warning && (
                <div className="rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-xs px-3 py-2">
                  ⚠ {result.warning}
                </div>
              )}
              <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans">{result.answer}</pre>
              <div className="text-xs text-slate-400 pt-2 border-t border-slate-100">
                Trace: {result.steps.map((s) => s.name).join(" → ")}
              </div>
            </div>
          </section>

          {/* RAG 근거 문서 */}
          {result.evidence.length > 0 && (
            <section className="panel">
              <div className="panel-header">
                <h3 className="text-sm font-semibold">참조 PDF 청크</h3>
                <span className="text-xs text-slate-500">{result.evidence.length}건</span>
              </div>
              <div className="panel-body space-y-2">
                {result.evidence.map((ev, i) => (
                  <div key={`${ev.document_id}-${i}`} className="rounded-md border border-slate-200 p-3">
                    <div className="flex justify-between items-start">
                      <div className="text-xs font-medium text-slate-600">{ev.title}</div>
                      <span className="badge badge-low ml-2 shrink-0">score {ev.score.toFixed(3)}</span>
                    </div>
                    <div className="text-xs text-slate-600 mt-1 leading-relaxed line-clamp-3">{ev.text}</div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
