"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { DocumentInfo, HybridAskResponse } from "@/types/api";

export function RAGQuery() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<HybridAskResponse | null>(null);
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  const loadDocs = useCallback(async () => {
    try {
      const res = await api.documents.list();
      setDocs((res as { documents?: DocumentInfo[] }).documents ?? (res as unknown as DocumentInfo[]));
    } catch {
      // backend may not have vector search; ignore
    }
  }, []);

  useEffect(() => { void loadDocs(); }, [loadDocs]);

  async function handleUpload(evt: React.ChangeEvent<HTMLInputElement>) {
    const file = evt.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setUploadMsg(null);
    try {
      const info = await api.documents.upload(file);
      setUploadMsg(`업로드 완료: ${info.filename}`);
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
      await api.documents.remove(docId);
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
      const res = await api.ragAsk(question);
      setResult(res);
    } catch (err) {
      setAskError(err instanceof Error ? err.message : String(err));
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="space-y-4">
      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">PDF 문서 관리</h3>
          <span className="text-xs text-slate-500">업로드된 문서는 벡터 검색에 사용됩니다</span>
        </div>
        <div className="panel-body space-y-3">
          <div className="flex items-center gap-3">
            <label className={`btn btn-primary cursor-pointer text-xs ${uploading ? "opacity-60 pointer-events-none" : ""}`}>
              {uploading ? "업로드 중…" : "PDF 업로드"}
              <input ref={fileInputRef} type="file" accept=".pdf" className="hidden" disabled={uploading} onChange={handleUpload} />
            </label>
          </div>
          {uploadMsg && <div className="text-xs text-emerald-700 bg-emerald-50 rounded px-3 py-2">{uploadMsg}</div>}
          {uploadError && <div className="text-xs text-rose-600 bg-rose-50 rounded px-3 py-2">{uploadError}</div>}
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
                    <td className="py-1.5 pr-4 text-right text-slate-500">{doc.page_count ?? "-"}</td>
                    <td className="py-1.5 pr-4 text-right text-slate-500">{doc.chunk_count ?? "-"}</td>
                    <td className="py-1.5">
                      <button className="text-rose-400 hover:text-rose-600 text-xs" onClick={() => void handleDelete(doc.doc_id)}>삭제</button>
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

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">문서 질의 (Hybrid Ask)</h3>
          <span className="text-xs text-slate-500">descriptive 유형으로 벡터 검색을 우선 사용합니다</span>
        </div>
        <div className="panel-body space-y-3">
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void handleAsk()}
              placeholder="예) 이 문서의 핵심 내용은? / 계약 조건이 뭐야?"
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            <button className="btn btn-primary" onClick={() => void handleAsk()} disabled={asking}>
              {asking ? "검색 중…" : "질의 실행"}
            </button>
          </div>
          {askError && <div className="text-sm text-rose-600">{askError}</div>}
        </div>
      </section>

      {result && (
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold">AI 답변</h3>
            <span className="badge badge-neutral">{result.intent ?? result.query_type}</span>
          </div>
          <div className="panel-body space-y-2">
            {result.warning && (
              <div className="rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-xs px-3 py-2">⚠ {result.warning}</div>
            )}
            <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans">{result.answer}</pre>
            {result.evidence && result.evidence.length > 0 && (
              <div className="text-xs text-slate-400 pt-2 border-t border-slate-100">
                근거: {result.evidence.slice(0, 3).map((e) => e.citation).join(", ")}
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
