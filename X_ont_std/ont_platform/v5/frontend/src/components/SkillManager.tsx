"use client";

import { useEffect, useMemo, useState } from "react";
import { Boxes, Code2, Database, Globe2, PlugZap, RefreshCw, Search, ShieldAlert, Trash2, Edit2, Plus, Wrench } from "lucide-react";
import { api } from "@/lib/api";
import type { Skill } from "@/types/api";
import { CustomSkillModal } from "./CustomSkillModal";

type SkillFilter = "all" | "builtin" | "custom";

function implementationLabel(type: Skill["implementation"]["type"]) {
  if (type === "mcp_http") return "MCP HTTP";
  if (type === "builtin") return "Built-in";
  if (type === "custom") return "Custom";
  return "HTTP";
}

function implementationIcon(type: Skill["implementation"]["type"]) {
  if (type === "mcp_http") return PlugZap;
  if (type === "builtin") return Database;
  if (type === "custom") return Code2;
  return Globe2;
}

function schemaKeys(schema: Record<string, unknown> | undefined) {
  const properties = schema?.properties;
  if (!properties || typeof properties !== "object") return [];
  return Object.keys(properties as Record<string, unknown>);
}

function SkillCard({
  skill,
  source,
  onEdit,
  onDelete,
}: {
  skill: Skill;
  source: "builtin" | "custom";
  onEdit?: (skill: Skill) => void;
  onDelete?: (skillId: string) => Promise<void>;
}) {
  const Icon = implementationIcon(skill.implementation.type);
  const inputs = schemaKeys(skill.inputSchema);
  const outputs = schemaKeys(skill.outputSchema);
  const isCustom = skill.implementation.type === "custom";
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!onDelete) return;
    if (!confirm(`"${skill.name}" 스킬을 삭제하시겠습니까?`)) return;

    setDeleting(true);
    try {
      await onDelete(skill.id);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-teal-200 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
            <Icon className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="truncate text-sm font-extrabold text-slate-950">{skill.name}</h3>
              <span className="badge badge-neutral">{implementationLabel(skill.implementation.type)}</span>
              <span className={source === "builtin" ? "badge badge-low" : "badge badge-medium"}>
                {source === "builtin" ? "기본" : "커스텀"}
              </span>
            </div>
            <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-600">{skill.description}</p>
          </div>
        </div>
        <span className="shrink-0 rounded-md bg-slate-50 px-2 py-1 font-mono text-[10px] font-semibold text-slate-500">
          v{skill.version}
        </span>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Input</div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {inputs.length === 0 ? (
              <span className="text-[10px] text-slate-400">입력 스키마 없음</span>
            ) : (
              inputs.slice(0, 8).map((item) => (
                <span key={item} className="rounded-md bg-white px-2 py-1 font-mono text-[10px] text-slate-600">
                  {item}
                </span>
              ))
            )}
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Output</div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {outputs.length === 0 ? (
              <span className="text-[10px] text-slate-400">출력 스키마 없음</span>
            ) : (
              outputs.slice(0, 8).map((item) => (
                <span key={item} className="rounded-md bg-white px-2 py-1 font-mono text-[10px] text-slate-600">
                  {item}
                </span>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-600">{skill.category}</span>
        <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-[10px] text-slate-500">{skill.id}</span>
        {skill.tags?.slice(0, 4).map((tag) => (
          <span key={tag} className="rounded-md bg-teal-50 px-2 py-1 text-[10px] font-semibold text-teal-700">
            {tag}
          </span>
        ))}
      </div>

      {isCustom && (
        <div className="mt-4 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-800">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
          <span>Custom Code 스킬은 Phase 1에서 저장/편집만 가능하며 실행은 제한됩니다.</span>
        </div>
      )}

      {source === "custom" && (
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            onClick={() => onEdit?.(skill)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 transition font-semibold text-xs"
          >
            <Edit2 className="h-3.5 w-3.5" />
            편집
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 transition font-semibold text-xs disabled:opacity-50"
          >
            <Trash2 className="h-3.5 w-3.5" />
            {deleting ? "삭제 중..." : "삭제"}
          </button>
        </div>
      )}
    </article>
  );
}

export function SkillManager() {
  const [builtinSkills, setBuiltinSkills] = useState<Skill[]>([]);
  const [customSkills, setCustomSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<SkillFilter>("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);

  async function loadSkills() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.skills.list();
      setBuiltinSkills(Array.isArray(res.builtinSkills) ? res.builtinSkills : []);
      setCustomSkills(Array.isArray(res.customSkills) ? res.customSkills : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setBuiltinSkills([]);
      setCustomSkills([]);
    } finally {
      setLoading(false);
    }
  }

  const handleSaveSkill = async (skill: Skill) => {
    try {
      await api.skills.createCustom(skill);
      setEditingSkill(null);
      setModalOpen(false);
      await loadSkills();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleDeleteSkill = async (skillId: string) => {
    try {
      await api.skills.deleteCustom(skillId);
      setEditingSkill(null);
      await loadSkills();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleEditSkill = (skill: Skill) => {
    setEditingSkill(skill);
    setModalOpen(true);
  };

  const handleNewSkill = () => {
    setEditingSkill(null);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditingSkill(null);
  };

  useEffect(() => {
    void loadSkills();
  }, []);

  const visibleSkills = useMemo(() => {
    const all = [
      ...builtinSkills.map((skill) => ({ skill, source: "builtin" as const })),
      ...customSkills.map((skill) => ({ skill, source: "custom" as const })),
    ];
    const normalized = query.trim().toLowerCase();
    return all.filter(({ skill, source }) => {
      if (filter !== "all" && source !== filter) return false;
      if (!normalized) return true;
      return [
        skill.id,
        skill.name,
        skill.description,
        skill.category,
        skill.implementation.type,
        ...(skill.tags ?? []),
      ].some((value) => value.toLowerCase().includes(normalized));
    });
  }, [builtinSkills, customSkills, filter, query]);

  const stats = {
    total: builtinSkills.length + customSkills.length,
    builtin: builtinSkills.length,
    custom: customSkills.length,
    executable: [...builtinSkills, ...customSkills].filter((skill) => skill.implementation.type !== "custom").length,
  };

  return (
    <div className="space-y-4">
      <section className="grid gap-3 md:grid-cols-4">
        <div className="panel p-4">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Total</div>
          <div className="mt-2 text-2xl font-extrabold text-slate-950">{stats.total}</div>
          <div className="mt-1 text-xs text-slate-500">등록된 스킬</div>
        </div>
        <div className="panel p-4">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Built-in</div>
          <div className="mt-2 text-2xl font-extrabold text-teal-700">{stats.builtin}</div>
          <div className="mt-1 text-xs text-slate-500">시스템 기본 스킬</div>
        </div>
        <div className="panel p-4">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Custom</div>
          <div className="mt-2 text-2xl font-extrabold text-amber-700">{stats.custom}</div>
          <div className="mt-1 text-xs text-slate-500">프로젝트 스킬</div>
        </div>
        <div className="panel p-4">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Executable</div>
          <div className="mt-2 text-2xl font-extrabold text-emerald-700">{stats.executable}</div>
          <div className="mt-1 text-xs text-slate-500">Phase 1 실행 가능</div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-teal-700 text-white">
              <Wrench className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h2 className="truncate text-base font-extrabold text-slate-950">스킬 관리</h2>
              <p className="mt-0.5 text-xs text-slate-500">워크플로우 노드에서 재사용할 실행 기능을 조회하고 관리합니다.</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              className="btn btn-primary px-3 py-2"
              onClick={handleNewSkill}
              disabled={loading}
            >
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              새 스킬
            </button>
            <button className="btn btn-ghost px-3 py-2" onClick={() => void loadSkills()} disabled={loading}>
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              새로고침
            </button>
          </div>
        </div>

        <div className="border-b border-slate-200 bg-slate-50 p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <label className="relative block lg:w-96">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                className="premium-input w-full pl-9"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="스킬명, ID, 태그 검색"
              />
            </label>
            <div className="flex rounded-lg bg-white p-1 text-xs shadow-sm ring-1 ring-slate-200">
              {[
                ["all", "전체"],
                ["builtin", "Built-in"],
                ["custom", "Custom"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  className={`rounded-md px-3 py-2 font-bold transition ${
                    filter === key ? "bg-teal-700 text-white" : "text-slate-500 hover:text-slate-900"
                  }`}
                  onClick={() => setFilter(key as SkillFilter)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="panel-body bg-slate-50">
          {error && (
            <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm font-semibold text-rose-700">
              {error}
            </div>
          )}

          {loading ? (
            <div className="grid gap-3 lg:grid-cols-2">
              {[0, 1, 2, 3].map((item) => (
                <div key={item} className="h-40 animate-pulse rounded-xl border border-slate-200 bg-white" />
              ))}
            </div>
          ) : visibleSkills.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
              <Boxes className="mx-auto h-8 w-8 text-slate-300" />
              <div className="mt-3 text-sm font-bold text-slate-700">표시할 스킬이 없습니다.</div>
              <div className="mt-1 text-xs text-slate-500">검색어 또는 필터를 조정해 주세요.</div>
            </div>
          ) : (
            <div className="grid gap-3 xl:grid-cols-2">
              {visibleSkills.map(({ skill, source }) => (
                <SkillCard
                  key={`${source}-${skill.id}`}
                  skill={skill}
                  source={source}
                  onEdit={source === "custom" ? handleEditSkill : undefined}
                  onDelete={source === "custom" ? handleDeleteSkill : undefined}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      <CustomSkillModal
        isOpen={modalOpen}
        skill={editingSkill}
        onClose={handleCloseModal}
        onSave={handleSaveSkill}
      />
    </div>
  );
}
