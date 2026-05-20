"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { OntologyMgmtSchema } from "@/types/api";
import { usePermission } from "@/hooks/usePermission";

function Toast({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-lg shadow text-sm ${
      ok ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-rose-50 text-rose-700 border border-rose-200"
    }`}>
      {text}
    </div>
  );
}

const BUILTIN_COLORS: Record<string, string> = {
  PERSON: "bg-blue-50 text-blue-700 border-blue-200",
  ORGANIZATION: "bg-purple-50 text-purple-700 border-purple-200",
  PRODUCT: "bg-green-50 text-green-700 border-green-200",
  METRIC: "bg-amber-50 text-amber-700 border-amber-200",
  CONCEPT: "bg-cyan-50 text-cyan-700 border-cyan-200",
  CATEGORY: "bg-orange-50 text-orange-700 border-orange-200",
  EVENT: "bg-rose-50 text-rose-700 border-rose-200",
  LOCATION: "bg-teal-50 text-teal-700 border-teal-200",
};

export function OntologySchemaManager() {
  const canEditOntology = usePermission("can_edit_ontology");
  const [schema, setSchema] = useState<OntologyMgmtSchema | null>(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ ok: boolean; text: string } | null>(null);

  const [etName, setEtName] = useState("");
  const [etDesc, setEtDesc] = useState("");
  const [etProps, setEtProps] = useState("");
  const [etSubmitting, setEtSubmitting] = useState(false);

  const [rtName, setRtName] = useState("");
  const [rtFrom, setRtFrom] = useState("");
  const [rtTo, setRtTo] = useState("");
  const [rtSubmitting, setRtSubmitting] = useState(false);

  const showToast = (ok: boolean, text: string) => {
    setToast({ ok, text });
    setTimeout(() => setToast(null), 3000);
  };

  const loadSchema = useCallback(async () => {
    setLoading(true);
    try {
      setSchema(await api.ontologyMgmt.getSchema());
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadSchema(); }, [loadSchema]);

  async function handleAddEntityType() {
    if (!etName.trim()) return;
    setEtSubmitting(true);
    try {
      const props = etProps.split(",").map((p) => p.trim()).filter(Boolean);
      await api.ontologyMgmt.addEntityType({ name: etName.trim().toUpperCase(), description: etDesc.trim(), properties: props });
      showToast(true, `엔티티 유형 '${etName}' 추가됨`);
      setEtName(""); setEtDesc(""); setEtProps("");
      await loadSchema();
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    } finally {
      setEtSubmitting(false);
    }
  }

  async function handleDeleteEntityType(name: string) {
    try {
      await api.ontologyMgmt.deleteEntityType(name);
      showToast(true, `엔티티 유형 '${name}' 삭제됨`);
      await loadSchema();
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    }
  }

  async function handleAddRelationType() {
    if (!rtName.trim() || !rtFrom.trim() || !rtTo.trim()) return;
    setRtSubmitting(true);
    try {
      await api.ontologyMgmt.addRelationType({ name: rtName.trim().toUpperCase(), from_type: rtFrom.trim().toUpperCase(), to_type: rtTo.trim().toUpperCase() });
      showToast(true, `관계 유형 '${rtName}' 추가됨`);
      setRtName(""); setRtFrom(""); setRtTo("");
      await loadSchema();
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    } finally {
      setRtSubmitting(false);
    }
  }

  async function handleDeleteRelationType(name: string) {
    try {
      await api.ontologyMgmt.deleteRelationType(name);
      showToast(true, `관계 유형 '${name}' 삭제됨`);
      await loadSchema();
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    }
  }

  const allTypeNames = schema?.entity_types.map((t) => t.name) ?? [];

  return (
    <div className="space-y-6">
      {toast && <Toast ok={toast.ok} text={toast.text} />}
      {loading && <div className="text-sm text-slate-500">스키마 로딩 중…</div>}

      <section>
        <h3 className="text-base font-bold text-slate-800 mb-3">엔티티 유형 (Entity Types)</h3>
        <div className="mb-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">내장 범용 유형 (수정 불가)</p>
          <div className="grid grid-cols-2 gap-2">
            {schema?.entity_types.filter((t) => t.is_builtin).map((t) => (
              <div key={t.name} className={`rounded-lg border px-3 py-2 text-xs ${BUILTIN_COLORS[t.name] ?? "bg-slate-50 text-slate-700 border-slate-200"}`}>
                <div className="font-bold">{t.name}</div>
                <div className="text-[11px] mt-0.5 opacity-80">{t.description}</div>
                {t.properties.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {t.properties.map((p) => (
                      <span key={p} className="bg-white/60 rounded px-1 py-0.5 font-mono text-[10px]">{p}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">도메인 유형</p>
          {(schema?.entity_types.filter((t) => !t.is_builtin) ?? []).length === 0 ? (
            <p className="text-xs text-slate-400 italic">등록된 도메인 유형이 없습니다.</p>
          ) : (
            <div className="space-y-1">
              {schema?.entity_types.filter((t) => !t.is_builtin).map((t) => (
                <div key={t.name} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2">
                  <div>
                    <span className="text-sm font-semibold text-slate-800">{t.name}</span>
                    {t.description && <span className="ml-2 text-xs text-slate-500">{t.description}</span>}
                    {t.properties.length > 0 && <span className="ml-2 text-xs text-slate-400 font-mono">[{t.properties.join(", ")}]</span>}
                  </div>
                  {canEditOntology && (
                    <button className="text-rose-400 hover:text-rose-600 text-xs ml-2" onClick={() => void handleDeleteEntityType(t.name)}>삭제</button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold text-slate-600 mb-3">도메인 유형 추가</p>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">유형명 (영대문자)</label>
              <input className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm bg-white" placeholder="예: CONTRACT" value={etName} onChange={(e) => setEtName(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">설명</label>
              <input className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm bg-white" placeholder="예: 계약서" value={etDesc} onChange={(e) => setEtDesc(e.target.value)} />
            </div>
          </div>
          <div className="mb-3">
            <label className="block text-xs text-slate-500 mb-1">속성 (쉼표 구분, 선택)</label>
            <input className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm bg-white" placeholder="예: start_date, end_date, value" value={etProps} onChange={(e) => setEtProps(e.target.value)} />
          </div>
          <button
            className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
            onClick={() => void handleAddEntityType()}
            disabled={!etName.trim() || etSubmitting || !canEditOntology}
            title={!canEditOntology ? "편집 권한이 없습니다" : undefined}
          >
            {etSubmitting ? "추가 중…" : "유형 추가"}
          </button>
        </div>
      </section>

      <section>
        <h3 className="text-base font-bold text-slate-800 mb-3">관계 유형 (Relation Types)</h3>
        {(schema?.relation_types ?? []).length === 0 ? (
          <p className="text-xs text-slate-400 italic mb-4">등록된 관계 유형이 없습니다.</p>
        ) : (
          <div className="mb-4 space-y-1">
            {schema?.relation_types.map((r) => (
              <div key={r.name} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-mono text-slate-500 text-xs bg-slate-100 rounded px-1">{r.from_type}</span>
                  <span className="font-semibold text-slate-800">{r.name}</span>
                  <span className="font-mono text-slate-500 text-xs bg-slate-100 rounded px-1">{r.to_type}</span>
                </div>
                {canEditOntology && (
                  <button className="text-rose-400 hover:text-rose-600 text-xs ml-2" onClick={() => void handleDeleteRelationType(r.name)}>삭제</button>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold text-slate-600 mb-3">관계 유형 추가</p>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">관계명</label>
              <input className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm bg-white" placeholder="예: BELONGS_TO" value={rtName} onChange={(e) => setRtName(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">From 유형</label>
              <select className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm bg-white" value={rtFrom} onChange={(e) => setRtFrom(e.target.value)}>
                <option value="">선택…</option>
                {allTypeNames.map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">To 유형</label>
              <select className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm bg-white" value={rtTo} onChange={(e) => setRtTo(e.target.value)}>
                <option value="">선택…</option>
                {allTypeNames.map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
          </div>
          <button
            className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
            onClick={() => void handleAddRelationType()}
            disabled={!rtName.trim() || !rtFrom || !rtTo || rtSubmitting || !canEditOntology}
            title={!canEditOntology ? "편집 권한이 없습니다" : undefined}
          >
            {rtSubmitting ? "추가 중…" : "관계 유형 추가"}
          </button>
        </div>
      </section>
    </div>
  );
}
