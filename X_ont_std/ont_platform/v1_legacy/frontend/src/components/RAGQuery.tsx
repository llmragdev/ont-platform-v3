"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { DocumentInfo, RagAskResponse } from "@/types/api";

export function RAGQuery({ user }: { user: string }) {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [vectorAvailable, setVectorAvailable] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<RagAskResponse | null>(null);
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  const loadDocs = useCallback(async () => {
    try {
      const res = await api.documents.list(user);
      setDocs(res.documents);
      setVectorAvailable(res.vector_search.available);
    } catch {
      // 백엔드 미기동 시 무시
    }
  }, [user]);

  useEffect(() => { loadDocs(); }, [loadDocs]);

  async function handleUpload(evt: React.ChangeEvent<HTMLInputElement>) {
    const file = evt.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setUploadMsg(null);
    try {
      const info = await api.documents.upload(user, file);
      setUploadMsg(`✓ ${info.filename} — ${info.page_count}페이지 / ${info.chunk_count}청크 벡터화 완료`);
      await loadDocs();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(docId: string) {
    try {
      await api.documents.remove(user, docId);
      await loadDocs();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleAsk() {
    if (!question.trim()) return;
    setAsking(true);
    setAskError(null);
    setResult(null);
    try {
      const res = await api.ragAsk(user, question);
      setResult(res);
    } catch (err) {
      setAskError(err instanceof Error ? err.message : String(err));
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* ── 상태 배너 ── */}
      <div className={`rounded-md px-4 py-2 text-xs flex items-center gap-2 ${vectorAvailable ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
        <span className="text-lg">{vectorAvailable ? "●" : "○"}</span>
        <span>
          {vectorAvailable
            ? `임베딩 활성 — 문서 ${docs.length}개 인덱싱됨`
            : "임베딩 비활성 (GEMINI_API_KEY 미설정 또는 백엔드 미기동)"}
        </span>
      </div>

      {/* ── PDF 문서 관리 ── */}
      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">PDF 문서 관리</h3>
          <span className="text-xs text-slate-500">업로드된 문서는 질의 시 자동 검색됩니다</span>
        </div>
        <div className="panel-body space-y-3">
          <div className="flex items-center gap-3">
            <label className={`btn btn-primary cursor-pointer text-xs ${uploading ? "opacity-60 pointer-events-none" : ""}`}>
              {uploading ? "업로드 중…" : "PDF 업로드"}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                disabled={uploading}
                onChange={handleUpload}
              />
            </label>
            <span className="text-xs text-slate-400">PDF 파일 (임베딩에 API 키 필요)</span>
          </div>

          {uploadMsg && (
            <div className="text-xs text-emerald-700 bg-emerald-50 rounded px-3 py-2">{uploadMsg}</div>
          )}
          {uploadError && (
            <div className="text-xs text-rose-600 bg-rose-50 rounded px-3 py-2">
              업로드 오류: {uploadError}
            </div>
          )}

          {docs.length > 0 ? (
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-200">
                  <th className="py-1 pr-4 font-medium">파일명</th>
                  <th className="py-1 pr-4 text-right font-medium">페이지</th>
                  <th className="py-1 pr-4 text-right font-medium">청크</th>
                  <th className="py-1 w-10" />
                </tr>
              </thead>
              <tbody>
                {docs.map((doc) => (
                  <tr key={doc.doc_id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-1.5 pr-4 font-medium text-slate-700">{doc.filename}</td>
                    <td className="py-1.5 pr-4 text-right text-slate-500">{doc.page_count}</td>
                    <td className="py-1.5 pr-4 text-right text-slate-500">{doc.chunk_count}</td>
                    <td className="py-1.5">
                      <button
                        type="button"
                        className="text-rose-400 hover:text-rose-600 text-xs"
                        onClick={() => handleDelete(doc.doc_id)}
                      >
                        삭제
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-xs text-slate-400">업로드된 문서 없음</p>
          )}
        </div>
      </section>

      {/* ── RAG 질의 ── */}
      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">문서 질의</h3>
          <span className="text-xs text-slate-500">업로드된 PDF 내용을 기반으로 답변합니다</span>
        </div>
        <div className="panel-body space-y-3">
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              placeholder="예) 이 문서의 핵심 내용은? / 계약 조건이 뭐야?"
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
              disabled={docs.length === 0}
            />
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleAsk}
              disabled={asking || docs.length === 0}
            >
              {asking ? "검색 중…" : "질의 실행"}
            </button>
          </div>
          {docs.length === 0 && (
            <p className="text-xs text-slate-400">PDF를 먼저 업로드하세요.</p>
          )}
          {askError && <div className="text-sm text-rose-600">{askError}</div>}
        </div>
      </section>

      {/* ── 결과 ── */}
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
              <div className="text-xs text-slate-400 pt-2 border-t border-slate-100">
                Trace: {result.steps.map((s) => s.name).join(" → ")}
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h3 className="text-sm font-semibold">참조 PDF 청크</h3>
              <span className="text-xs text-slate-500">{result.evidence.length}건</span>
            </div>
            <div className="panel-body space-y-3">
              {result.evidence.map((ev, i) => (
                <div key={`${ev.document_id}-${i}`} className="rounded-md border border-slate-200 p-3">
                  <div className="flex justify-between items-start">
                    <div className="text-xs font-medium text-slate-600">{ev.title}</div>
                    <span className="badge badge-low ml-2 shrink-0">score {ev.score.toFixed(3)}</span>
                  </div>
                  <div className="text-xs text-slate-600 mt-1 leading-relaxed line-clamp-4">{ev.text}</div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
