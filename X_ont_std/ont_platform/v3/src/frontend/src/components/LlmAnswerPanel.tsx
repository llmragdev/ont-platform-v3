"use client";
import type { QualityMetrics } from "@/types/api";

interface LlmAnswerPanelProps {
  answer: string | null;
  intent: string;
  quality_metrics?: QualityMetrics;
  evidence?: Array<{ citation: string }>;
  loading: boolean;
}

export function LlmAnswerPanel({ answer, intent, quality_metrics, evidence, loading }: LlmAnswerPanelProps) {
  const llmUsed = quality_metrics?.llm_used ?? false;
  const fallbackUsed = quality_metrics?.fallback_used ?? false;

  return (
    <section className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">AI 답변</h3>
        <div className="flex gap-1.5 items-center">
          <span className="badge badge-neutral">{intent}</span>
          {llmUsed && (
            <span className="inline-flex items-center gap-1 text-xs bg-green-100 text-green-700 rounded-full px-2 py-0.5">
              ✓ LLM
            </span>
          )}
        </div>
      </div>
      <div className="panel-body space-y-3">
        {!llmUsed && !loading && (
          <div className="flex items-center gap-2 text-xs bg-amber-50 text-amber-700 border border-amber-200 rounded px-3 py-2">
            <span>⚠</span>
            <span>{fallbackUsed ? "fallback 사용됨 — LLM 없이 템플릿 답변" : "LLM 미연결 — 템플릿 답변"}</span>
          </div>
        )}

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500 py-4">
            <span className="inline-block w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
            AI가 답변을 생성하고 있습니다… (2~5초)
          </div>
        ) : (
          <>
            <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans">{answer ?? "—"}</pre>

            {evidence && evidence.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {evidence.slice(0, 5).map((e, i) => (
                  <span key={i} className="text-xs bg-blue-50 text-blue-700 rounded px-2 py-0.5 border border-blue-100">
                    {e.citation}
                  </span>
                ))}
              </div>
            )}
          </>
        )}

        {quality_metrics && !loading && (
          <div className="flex flex-wrap gap-3 text-xs text-slate-500 border-t pt-2">
            <span>벡터 {quality_metrics.vector_hits}건</span>
            <span>온톨로지 {quality_metrics.ontology_hits}건</span>
            {quality_metrics.latency_ms && <span>응답 {(quality_metrics.latency_ms / 1000).toFixed(1)}s</span>}
            <span className={fallbackUsed ? "text-amber-600" : "text-slate-400"}>
              fallback {fallbackUsed ? "✓" : "✗"}
            </span>
          </div>
        )}
      </div>
    </section>
  );
}
