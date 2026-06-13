"use client";

import { AlertTriangle, Boxes, GitBranch, History, Library, UserRoundCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { workflowTemplates } from "@/lib/workflowTemplates";
import type { WorkflowGraph } from "@/types/api";
import type { ViewKey } from "@/components/Sidebar";

export function WorkflowHome({ onNavigate }: { onNavigate: (view: ViewKey) => void }) {
  const [graphs, setGraphs] = useState<WorkflowGraph[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.workflowGraphs
      .list()
      .then((items) => setGraphs(Array.isArray(items) ? items : []))
      .catch(() => setGraphs([]))
      .finally(() => setLoading(false));
  }, []);

  const stats = useMemo(
    () => [
      { label: "활성 워크플로우", value: graphs.length, icon: GitBranch },
      { label: "시스템 템플릿", value: workflowTemplates.length, icon: Library },
      { label: "수동 이관 후보", value: 2, icon: UserRoundCheck },
      { label: "거버넌스 정책", value: 4, icon: Boxes },
    ],
    [graphs.length]
  );

  return (
    <div className="space-y-5">
      <section className="panel">
        <div className="panel-body flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-xs font-semibold uppercase text-teal-700">Workflow entry</div>
            <h2 className="mt-1 text-2xl font-bold text-slate-950 dark:text-slate-100">업무 시나리오에서 시작하는 워크플로우</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              템플릿을 복제해 캔버스에서 수정하고, 실행 이력과 근거 정책을 함께 확인합니다.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="btn btn-primary bg-teal-700 hover:bg-teal-800" onClick={() => onNavigate("template-gallery")}>
              템플릿 선택
            </button>
            <button className="btn btn-ghost" onClick={() => onNavigate("workflow-graph")}>
              빈 캔버스 열기
            </button>
          </div>
        </div>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="panel p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500 dark:text-slate-400">{item.label}</span>
                <Icon className="h-4 w-4 text-teal-700" />
              </div>
              <div className="mt-3 text-3xl font-bold text-slate-950 dark:text-slate-100">{item.value}</div>
            </div>
          );
        })}
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3 className="font-semibold text-slate-950 dark:text-slate-100">Use Case Gallery</h3>
              <p className="text-xs text-slate-500">복제해서 수정할 수 있는 시작점</p>
            </div>
            <button className="btn btn-ghost" onClick={() => onNavigate("template-gallery")}>전체 보기</button>
          </div>
          <div className="panel-body grid gap-3 md:grid-cols-2">
            {workflowTemplates.slice(0, 4).map((template) => (
              <button
                key={template.templateId}
                type="button"
                onClick={() => onNavigate("template-gallery")}
                className="rounded-lg border border-slate-200 bg-white p-4 text-left transition hover:border-teal-300 hover:bg-teal-50/40 dark:border-slate-800 dark:bg-slate-950 dark:hover:bg-slate-900"
              >
                <div className="text-sm font-semibold text-slate-950 dark:text-slate-100">{template.name}</div>
                <div className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{template.summary}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h3 className="font-semibold text-slate-950 dark:text-slate-100">최근 워크플로우</h3>
              <p className="text-xs text-slate-500">{loading ? "불러오는 중" : `${graphs.length}개 저장됨`}</p>
            </div>
            <History className="h-4 w-4 text-slate-400" />
          </div>
          <div className="panel-body space-y-3">
            {graphs.length === 0 && (
              <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500 dark:border-slate-700">
                저장된 워크플로우가 없습니다. 템플릿을 복제하거나 빈 캔버스에서 시작하세요.
              </div>
            )}
            {graphs.slice(0, 5).map((graph) => (
              <button
                key={graph.id}
                type="button"
                onClick={() => onNavigate("workflow-graph")}
                className="flex w-full items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-left hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
              >
                <span>
                  <span className="block text-sm font-medium text-slate-900 dark:text-slate-100">{graph.name}</span>
                  <span className="text-xs text-slate-500">{graph.nodes.length} nodes / {graph.edges.length} edges</span>
                </span>
                <span className="text-xs text-slate-400">{graph.id}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-100">
        <div className="flex gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            현재 템플릿 복제는 워크플로우 그래프 저장 API를 사용합니다. 실제 계정 변경, 권한 부여, 댓글 등록은 Skill Manager와 외부 adapter가 연결된 뒤 운영 기능으로 전환합니다.
          </p>
        </div>
      </section>
    </div>
  );
}
