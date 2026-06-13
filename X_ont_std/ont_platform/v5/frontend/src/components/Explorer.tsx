"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { OntologyDocInfo, OntologyEntity } from "@/types/api";

export function Explorer() {
  const [docs, setDocs] = useState<OntologyDocInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [entities, setEntities] = useState<OntologyEntity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const list = await api.ontologyMgmt.listDocs();
        const arr = Array.isArray(list) ? list : [];
        setDocs(arr);
        if (arr.length > 0) setSelectedDoc(arr[0].doc_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedDoc) return;
    setLoading(true);
    api.ontologyMgmt.listEntities(selectedDoc, { size: 100 })
      .then((res) => setEntities(res.entities))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [selectedDoc]);

  return (
    <div className="space-y-4">
      {error && <div className="text-sm text-rose-600 bg-rose-50 rounded px-3 py-2">{error}</div>}
      <div className="flex items-center gap-3">
        <label className="text-xs text-slate-500">문서 선택</label>
        <select
          className="border border-slate-200 rounded px-2 py-1.5 text-sm"
          value={selectedDoc}
          onChange={(e) => setSelectedDoc(e.target.value)}
        >
          {docs.length === 0 && <option value="">문서 없음</option>}
          {docs.map((d) => (
            <option key={d.doc_id} value={d.doc_id}>
              {d.doc_id} ({d.entity_count}개 엔티티)
            </option>
          ))}
        </select>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">엔티티 목록</h3>
          <span className="text-xs text-slate-500">{entities.length}건</span>
        </div>
        <div className="panel-body p-0">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>유형</th>
                <th>이름</th>
                <th>속성</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={4} className="text-center py-6 text-slate-400">로딩 중…</td></tr>
              ) : entities.length === 0 ? (
                <tr><td colSpan={4} className="text-center py-6 text-slate-400">엔티티가 없습니다.</td></tr>
              ) : (
                entities.map((e) => (
                  <tr key={e.id}>
                    <td className="font-mono text-xs text-slate-500">{e.id}</td>
                    <td><span className="badge badge-neutral">{e.type}</span></td>
                    <td className="font-medium">{e.name}</td>
                    <td className="text-xs text-slate-500 max-w-xs truncate">
                      {Object.entries(e.properties ?? {}).map(([k, v]) => `${k}: ${v}`).join(" · ") || "-"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
