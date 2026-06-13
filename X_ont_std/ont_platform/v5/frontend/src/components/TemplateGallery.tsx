"use client";

import { Copy, GitBranch, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { buildGraphFromTemplate, workflowTemplates, type WorkflowTemplate } from "@/lib/workflowTemplates";
import type { ViewKey } from "@/components/Sidebar";

const categoryLabel: Record<WorkflowTemplate["category"], string> = {
  helpdesk: "?쒕퉬???붿껌",
  access: "怨꾩젙 議곗튂",
  approval: "沅뚰븳 ?덈궡",
  incident: "?μ븷 ?묐?",
  factory: "공장 자동화",
};

export function TemplateGallery({ onNavigate }: { onNavigate: (view: ViewKey) => void }) {
  const [selected, setSelected] = useState<WorkflowTemplate>(workflowTemplates[0]);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function cloneTemplate(template: WorkflowTemplate) {
    setSavingId(template.templateId);
    setMessage(null);
    try {
      let saved;
      try {
        saved = await api.workflowTemplates.clone(template.templateId, {
          name: `${template.name} - 운영본`,
          default_mode: "post",
        });
      } catch {
        saved = await api.workflowGraphs.save(buildGraphFromTemplate(template));
      }
      if (typeof window !== "undefined") {
        window.localStorage.setItem("workflow:lastClonedGraphId", saved.id);
      }
      setMessage(`蹂듭젣 ?꾨즺: ${saved.name}`);
      onNavigate("workflow-graph");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
      <section className="panel overflow-hidden">
        <div className="panel-header">
          <div>
            <h2 className="font-semibold text-slate-950 dark:text-slate-100">Template Gallery</h2>
            <p className="text-xs text-slate-500">Clone a system template into your project and customize it.</p>
          </div>
          <GitBranch className="h-4 w-4 text-teal-700" />
        </div>
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {workflowTemplates.map((template) => (
            <button
              key={template.templateId}
              type="button"
              onClick={() => setSelected(template)}
              className={`w-full p-4 text-left transition ${
                selected.templateId === template.templateId
                  ? "bg-teal-50 dark:bg-teal-950/40"
                  : "bg-white hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-800"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="badge badge-neutral">{categoryLabel[template.category]}</span>
                  <h3 className="mt-2 text-sm font-semibold text-slate-950 dark:text-slate-100">{template.name}</h3>
                </div>
                <span className="text-xs text-slate-400">{template.graph.nodes.length} nodes</span>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{template.summary}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <div className="flex items-center gap-2">
              <span className="badge badge-neutral">{categoryLabel[selected.category]}</span>
              <span className="text-xs text-slate-400">{selected.templateId}</span>
            </div>
            <h2 className="mt-2 text-xl font-bold text-slate-950 dark:text-slate-100">{selected.name}</h2>
          </div>
          <button
            className="btn btn-primary bg-teal-700 hover:bg-teal-800"
            onClick={() => void cloneTemplate(selected)}
            disabled={savingId === selected.templateId}
          >
            <Copy className="mr-2 h-4 w-4" />
            {savingId === selected.templateId ? "Cloning" : "Clone to project"}
          </button>
        </div>

        <div className="panel-body space-y-5">
          {message && (
            <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200">
              {message}
            </div>
          )}

          <div className="grid gap-3 lg:grid-cols-3">
            <InfoBlock label="?곸슜 議곌굔" value={selected.appliesTo} />
            <InfoBlock label="?먮룞???쒖쇅" value={selected.automationBoundary} />
            <InfoBlock label="洹몃옒???ш린" value={`${selected.graph.nodes.length} nodes / ${selected.graph.edges.length} edges`} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <ListBlock title="Required Skills" items={selected.requiredSkills} />
            <ListBlock title="Knowledge Sources" items={selected.requiredSources} />
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800">
            <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
              <h3 className="font-semibold text-slate-950 dark:text-slate-100">Template Flow</h3>
            </div>
            <div className="overflow-x-auto p-4">
              <div className="flex min-w-max items-center gap-3">
                {selected.graph.nodes.map((node, index) => (
                  <div key={node.id} className="flex items-center gap-3">
                    <div className="min-w-36 rounded-lg border border-teal-200 bg-teal-50 px-3 py-2 text-sm font-semibold text-teal-950 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-100">
                      {node.data?.label ?? node.type}
                      <div className="mt-1 text-[11px] font-normal text-teal-700 dark:text-teal-300">{node.type}</div>
                    </div>
                    {index < selected.graph.nodes.length - 1 && <span className="text-slate-300">→</span>}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-100">
            <div className="flex gap-3">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <div className="font-semibold">Governance</div>
                <div className="mt-1">{selected.governance.join(" / ")}</div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
      <div className="text-xs font-semibold uppercase text-slate-400">{label}</div>
      <div className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">{value}</div>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
      <h3 className="font-semibold text-slate-950 dark:text-slate-100">{title}</h3>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className="badge badge-neutral">{item}</span>
        ))}
      </div>
    </div>
  );
}
