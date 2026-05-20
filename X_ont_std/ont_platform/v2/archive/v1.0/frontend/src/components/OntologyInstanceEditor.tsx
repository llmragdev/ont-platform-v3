"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { OntologyDocInfo, OntologyEntity, OntologyMgmtSchema } from "@/types/api";
import { usePermission } from "@/hooks/usePermission";
import { useUserContext } from "@/context/UserContext";

function Toast({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div
      className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-lg shadow text-sm ${
        ok ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-rose-50 text-rose-700 border border-rose-200"
      }`}
    >
      {text}
    </div>
  );
}

interface EditModal {
  mode: "create" | "edit";
  entity?: OntologyEntity;
}

export function OntologyInstanceEditor() {
  const [docs, setDocs] = useState<OntologyDocInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string>("");
  const [schema, setSchema] = useState<OntologyMgmtSchema | null>(null);
  const [entities, setEntities] = useState<OntologyEntity[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ ok: boolean; text: string } | null>(null);

  // 엔티티 편집 모달
  const [modal, setModal] = useState<EditModal | null>(null);
  const [modalName, setModalName] = useState("");
  const [modalType, setModalType] = useState("");
  const [modalProps, setModalProps] = useState("{}");
  const [modalError, setModalError] = useState<string | null>(null);
  const [modalSubmitting, setModalSubmitting] = useState(false);

  // 온톨로지 추출 중 상태
  const [extracting, setExtracting] = useState(false);

  const canEditOntology = usePermission("can_edit_ontology");
  const { user: tenantUser } = useUserContext();
  const userId = tenantUser?.id;

  const PAGE_SIZE = 20;

  const showToast = (ok: boolean, text: string) => {
    setToast({ ok, text });
    setTimeout(() => setToast(null), 3000);
  };

  useEffect(() => {
    void (async () => {
      try {
        const [docsRes, schemaRes] = await Promise.all([
          api.ontologyMgmt.listDocs(),
          api.ontologyMgmt.getSchema(),
        ]);
        setDocs(docsRes.ontologies);
        setSchema(schemaRes);
        if (docsRes.ontologies.length > 0) setSelectedDoc(docsRes.ontologies[0].doc_id);
      } catch (err) {
        showToast(false, err instanceof Error ? err.message : String(err));
      }
    })();
  }, []);

  const loadEntities = useCallback(async () => {
    if (!selectedDoc) return;
    setLoading(true);
    try {
      const res = await api.ontologyMgmt.listEntities(selectedDoc, {
        entity_type: typeFilter || undefined,
        page,
        size: PAGE_SIZE,
      });
      setEntities(res.entities);
      setTotal(res.total);
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [selectedDoc, typeFilter, page]);

  useEffect(() => { void loadEntities(); }, [loadEntities]);

  function openCreate() {
    setModal({ mode: "create" });
    setModalName(""); setModalType(""); setModalProps("{}"); setModalError(null);
  }

  function openEdit(e: OntologyEntity) {
    setModal({ mode: "edit", entity: e });
    setModalName(e.name); setModalType(e.type);
    setModalProps(JSON.stringify(e.properties, null, 2));
    setModalError(null);
  }

  async function handleModalSubmit() {
    if (!selectedDoc) return;
    setModalError(null);
    setModalSubmitting(true);
    try {
      let props: Record<string, unknown> = {};
      try { props = JSON.parse(modalProps); } catch { throw new Error("속성 JSON 형식이 잘못되었습니다."); }
      if (modal?.mode === "create") {
        await api.ontologyMgmt.createEntity(selectedDoc, { type: modalType, name: modalName, properties: props }, userId);
        showToast(true, "엔티티 추가됨");
      } else if (modal?.mode === "edit" && modal.entity) {
        await api.ontologyMgmt.updateEntity(selectedDoc, modal.entity.id, { name: modalName, properties: props }, userId);
        showToast(true, "엔티티 수정됨");
      }
      setModal(null);
      await loadEntities();
    } catch (err) {
      setModalError(err instanceof Error ? err.message : String(err));
    } finally {
      setModalSubmitting(false);
    }
  }

  async function handleDelete(entityId: string) {
    if (!selectedDoc) return;
    try {
      await api.ontologyMgmt.deleteEntity(selectedDoc, entityId, userId);
      showToast(true, `엔티티 ${entityId} 삭제됨`);
      await loadEntities();
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    }
  }

  async function handleExtract() {
    if (!selectedDoc) return;
    setExtracting(true);
    try {
      const res = await api.ontologyMgmt.extractOntology(selectedDoc, userId);
      showToast(true, `추출 완료: 엔티티 ${res.entity_count}개, 관계 ${res.relation_count}개`);
      await loadEntities();
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    } finally {
      setExtracting(false);
    }
  }

  const allTypeNames = schema?.entity_types.map((t) => t.name) ?? [];
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-4">
      {toast && <Toast ok={toast.ok} text={toast.text} />}

      {/* ── 상단 컨트롤 바 ── */}
      <div className="flex items-center gap-3 flex-wrap">
        <div>
          <label className="text-xs text-slate-500 mr-1">문서</label>
          <select
            className="border border-slate-200 rounded px-2 py-1.5 text-sm"
            value={selectedDoc}
            onChange={(e) => { setSelectedDoc(e.target.value); setPage(1); }}
          >
            {docs.length === 0 && <option value="">문서 없음</option>}
            {docs.map((d) => (
              <option key={d.doc_id} value={d.doc_id}>
                {d.filename} ({d.entity_count}개 엔티티)
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500 mr-1">유형 필터</label>
          <select
            className="border border-slate-200 rounded px-2 py-1.5 text-sm"
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
          >
            <option value="">전체</option>
            {allTypeNames.map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        <div className="ml-auto flex gap-2">
          <button
            className="bg-slate-100 text-slate-700 text-sm px-3 py-1.5 rounded hover:bg-slate-200 disabled:opacity-50"
            onClick={() => void handleExtract()}
            disabled={!selectedDoc || extracting || !canEditOntology}
            title={!canEditOntology ? "편집 권한이 없습니다" : undefined}
          >
            {extracting ? "추출 중…" : "PDF 재추출"}
          </button>
          <button
            className="bg-blue-600 text-white text-sm px-3 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
            onClick={openCreate}
            disabled={!selectedDoc || !canEditOntology}
            title={!canEditOntology ? "편집 권한이 없습니다" : undefined}
          >
            + 엔티티 추가
          </button>
        </div>
      </div>

      {/* ── 엔티티 테이블 ── */}
      <div className="rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-3 py-2 text-xs font-semibold text-slate-500 w-20">ID</th>
              <th className="text-left px-3 py-2 text-xs font-semibold text-slate-500 w-32">유형</th>
              <th className="text-left px-3 py-2 text-xs font-semibold text-slate-500">이름</th>
              <th className="text-left px-3 py-2 text-xs font-semibold text-slate-500">속성</th>
              <th className="text-left px-3 py-2 text-xs font-semibold text-slate-500 w-24">액션</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={5} className="px-3 py-8 text-center text-slate-400 text-xs">로딩 중…</td></tr>
            )}
            {!loading && entities.length === 0 && (
              <tr><td colSpan={5} className="px-3 py-8 text-center text-slate-400 text-xs">
                {selectedDoc ? "엔티티가 없습니다. PDF 재추출 또는 직접 추가하세요." : "문서를 선택하세요."}
              </td></tr>
            )}
            {entities.map((e) => (
              <tr key={e.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2 font-mono text-xs text-slate-500">{e.id}</td>
                <td className="px-3 py-2">
                  <span className="bg-slate-100 text-slate-700 text-xs rounded px-1.5 py-0.5 font-medium">{e.type}</span>
                </td>
                <td className="px-3 py-2 font-medium text-slate-800">{e.name}</td>
                <td className="px-3 py-2 text-xs text-slate-500 max-w-xs truncate">
                  {Object.keys(e.properties).length > 0
                    ? Object.entries(e.properties).map(([k, v]) => `${k}: ${v}`).join(" · ")
                    : <span className="text-slate-300 italic">없음</span>
                  }
                </td>
                <td className="px-3 py-2 flex gap-1">
                  {canEditOntology && (
                    <button
                      className="text-blue-500 hover:text-blue-700 text-xs px-1.5 py-0.5 rounded hover:bg-blue-50"
                      onClick={() => openEdit(e)}
                    >
                      수정
                    </button>
                  )}
                  {canEditOntology && (
                    <button
                      className="text-rose-400 hover:text-rose-600 text-xs px-1.5 py-0.5 rounded hover:bg-rose-50"
                      onClick={() => void handleDelete(e.id)}
                    >
                      삭제
                    </button>
                  )}
                  {!canEditOntology && <span className="text-xs text-slate-300">-</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── 페이지네이션 ── */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 text-sm">
          <button
            className="px-2 py-1 rounded border text-slate-600 disabled:opacity-40 hover:bg-slate-50"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            이전
          </button>
          <span className="text-slate-500">{page} / {totalPages}</span>
          <button
            className="px-2 py-1 rounded border text-slate-600 disabled:opacity-40 hover:bg-slate-50"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            다음
          </button>
        </div>
      )}

      {/* ── 추가/수정 모달 ── */}
      {modal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-[480px] max-h-[90vh] overflow-y-auto">
            <h3 className="text-sm font-bold text-slate-800 mb-4">
              {modal.mode === "create" ? "엔티티 추가" : `엔티티 수정 (${modal.entity?.id})`}
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">유형</label>
                {modal.mode === "create" ? (
                  <select
                    className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                    value={modalType}
                    onChange={(e) => setModalType(e.target.value)}
                  >
                    <option value="">선택…</option>
                    {allTypeNames.map((n) => <option key={n} value={n}>{n}</option>)}
                  </select>
                ) : (
                  <span className="text-sm text-slate-700 font-medium">{modal.entity?.type}</span>
                )}
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">이름</label>
                <input
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  value={modalName}
                  onChange={(e) => setModalName(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">속성 (JSON)</label>
                <textarea
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-xs font-mono h-28 resize-none"
                  value={modalProps}
                  onChange={(e) => setModalProps(e.target.value)}
                />
              </div>
              {modalError && (
                <p className="text-xs text-rose-600 bg-rose-50 rounded p-2">{modalError}</p>
              )}
            </div>
            <div className="flex gap-2 mt-5">
              <button
                className="flex-1 bg-blue-600 text-white text-sm py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
                onClick={() => void handleModalSubmit()}
                disabled={!modalName.trim() || (modal.mode === "create" && !modalType) || modalSubmitting}
              >
                {modalSubmitting ? "처리 중…" : modal.mode === "create" ? "추가" : "저장"}
              </button>
              <button
                className="flex-1 bg-slate-100 text-slate-700 text-sm py-1.5 rounded hover:bg-slate-200"
                onClick={() => setModal(null)}
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
