"use client";

import { useUserContext } from "@/context/UserContext";

export type ViewKey =
  | "dashboard"
  | "workflow-home"
  | "template-gallery"
  | "explorer"
  | "ontology-graph"
  | "ai-query"
  | "sparql-query"
  | "rdf-workbench"
  | "rag-query"
  | "hybrid-query"
  | "workflow"
  | "workflow-graph"
  | "workflow-ontology-trace"
  | "writeback-dlq"
  | "audit"
  | "integration-test"
  | "ontology-schema"
  | "ontology-instance"
  | "ontology-graph-edit";

type SidebarGroup = {
  title: string;
  items: { key: ViewKey; label: string; description: string }[];
};

const GROUPS: SidebarGroup[] = [
  {
    title: "워크플로우 v5",
    items: [
      { key: "workflow-home", label: "Workflow Home", description: "템플릿, 실행, 이관 현황" },
      { key: "template-gallery", label: "Template Gallery", description: "복제해서 시작하는 업무 흐름" },
      { key: "workflow-graph", label: "Workflow Builder", description: "캔버스 편집과 실행" },
      { key: "workflow-ontology-trace", label: "Workflow Trace", description: "실행 결과와 온톨로지 흐름" },
      { key: "workflow", label: "승인 워크플로우", description: "상태 전이 액션" },
      { key: "writeback-dlq", label: "Writeback DLQ", description: "실패 큐 모니터링" },
    ],
  },
  {
    title: "분석 및 질의",
    items: [
      { key: "dashboard", label: "대시보드", description: "주요 지표와 작업 큐" },
      { key: "explorer", label: "객체 탐색", description: "온톨로지 엔티티 조회" },
      { key: "ai-query", label: "온톨로지 질의", description: "AI 기반 업무 질의" },
      { key: "hybrid-query", label: "통합 질의", description: "온톨로지 + RAG 분석" },
      { key: "rag-query", label: "문서 RAG 질의", description: "PDF 근거 기반 답변" },
      { key: "sparql-query", label: "SPARQL 콘솔", description: "표준 쿼리 실행" },
      { key: "rdf-workbench", label: "RDF Lab", description: "RDF/외부 온톨로지" },
    ],
  },
  {
    title: "온톨로지 관리",
    items: [
      { key: "ontology-schema", label: "스키마 정의", description: "엔티티와 관계 타입" },
      { key: "ontology-instance", label: "인스턴스 편집", description: "엔티티 수정 및 추가" },
      { key: "ontology-graph-edit", label: "관계 그래프 편집", description: "React Flow 기반 편집" },
      { key: "ontology-graph", label: "온톨로지 그래프", description: "객체와 관계 시각화" },
    ],
  },
  {
    title: "운영",
    items: [
      { key: "audit", label: "감사 로그", description: "운영 이벤트 기록" },
      { key: "integration-test", label: "통합 테스트", description: "질의와 근거 검증" },
    ],
  },
];

export function Sidebar({
  current,
  onSelect,
}: {
  current: ViewKey;
  onSelect: (view: ViewKey) => void;
}) {
  const { user, setUser, presets } = useUserContext();

  return (
    <aside className="w-full shrink-0 border-b border-slate-200 bg-white flex flex-col dark:bg-slate-900 dark:border-slate-800 md:h-screen md:w-72 md:border-b-0 md:border-r">
      <div className="px-4 py-4 border-b border-slate-200 dark:border-slate-800 md:py-5">
        <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">Ontology Console v5</h1>
        <p className="text-xs text-slate-500 mt-0.5 dark:text-slate-400">AI-ready ontology workflow builder</p>
        <div className="mt-3">
          <select
            className="w-full border border-slate-200 rounded-md px-2 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200"
            value={user.userId}
            onChange={(e) => {
              const preset = presets.find((p) => p.userId === e.target.value);
              if (preset) setUser(preset);
            }}
          >
            {presets.map((p) => (
              <option key={p.userId} value={p.userId}>
                {p.userId} ({p.role})
              </option>
            ))}
          </select>
          <div className="text-[10px] text-slate-400 mt-1">{user.companyId} / {user.projectId}</div>
        </div>
      </div>
      <nav className="max-h-64 flex-1 overflow-y-auto p-2 space-y-3 md:max-h-none">
        {GROUPS.map((group) => (
          <div key={group.title}>
            <div className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              {group.title}
            </div>
            {group.items.map((item) => (
              <button
                key={item.key}
                type="button"
                data-testid={`nav-${item.key}`}
                onClick={() => onSelect(item.key)}
                className={`w-full text-left rounded-md px-3 py-2 transition ${
                  current === item.key
                    ? "bg-teal-50 text-teal-800 dark:bg-teal-950/50 dark:text-teal-200"
                    : "hover:bg-slate-50 text-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                }`}
              >
                <div className="text-sm font-medium">{item.label}</div>
                <div className="text-xs text-slate-500 mt-0.5 dark:text-slate-400">{item.description}</div>
              </button>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}
