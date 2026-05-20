"use client";

export type ViewKey =
  | "dashboard"
  | "explorer"
  | "ontology-graph"
  | "ai-query"
  | "rag-query"
  | "hybrid-query"
  | "workflow"
  | "workflow-graph"
  | "audit"
  | "ontology-schema"
  | "ontology-instance"
  | "ontology-graph-edit";

type SidebarGroup = {
  title: string;
  items: { key: ViewKey; label: string; description: string; badge?: string }[];
};

const GROUPS: SidebarGroup[] = [
  {
    title: "분석 · 질의",
    items: [
      { key: "dashboard",    label: "대시보드",       description: "승인 대기 주문 및 주요 지표" },
      { key: "explorer",     label: "객체 탐색",      description: "온톨로지 객체와 관계 조회 (표)" },
      { key: "ai-query",     label: "온톨로지 질의",   description: "객체 ID 기반 AI 의사결정 분석" },
      { key: "rag-query",    label: "문서 RAG 질의",  description: "PDF 업로드 + 자유 질문 답변" },
      { key: "hybrid-query", label: "통합 질의",      description: "온톨로지 + RAG 복합 분석" },
    ],
  },
  {
    title: "온톨로지 관리",
    items: [
      { key: "ontology-schema",     label: "스키마 정의",      description: "엔티티·관계 유형 관리" },
      { key: "ontology-instance",   label: "인스턴스 편집",    description: "추출된 엔티티 수정·추가" },
      { key: "ontology-graph-edit", label: "관계 그래프 편집", description: "React Flow 노드·엣지 편집" },
      { key: "ontology-graph",      label: "온톨로지 그래프",  description: "객체-관계 시각화 캔버스" },
    ],
  },
  {
    title: "워크플로우",
    items: [
      { key: "workflow",       label: "승인 워크플로우",   description: "상태 전이 액션" },
      { key: "workflow-graph", label: "워크플로우 그래프", description: "React Flow 캔버스 + 노드 실행" },
    ],
  },
  {
    title: "운영",
    items: [
      { key: "audit", label: "감사 로그", description: "운영 이벤트 기록" },
    ],
  },
];

export function Sidebar({
  current,
  onSelect,
  llmProvider,
}: {
  current: ViewKey;
  onSelect: (view: ViewKey) => void;
  llmProvider?: string;
}) {
  return (
    <aside className="w-64 shrink-0 border-r border-slate-200 bg-white">
      <div className="px-4 py-5 border-b border-slate-200">
        <h1 className="text-lg font-bold text-slate-900">Ontology Console</h1>
        <p className="text-xs text-slate-500 mt-0.5">claud 통합 · AI 업무 의사결정 플랫폼</p>
        {llmProvider && (
          <span className={`badge mt-2 ${llmProvider === "gemini" ? "badge-low" : "badge-medium"}`}>
            LLM: {llmProvider}
          </span>
        )}
      </div>
      <nav className="p-2 space-y-3">
        {GROUPS.map((group) => (
          <div key={group.title}>
            <div className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              {group.title}
            </div>
            {group.items.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => onSelect(item.key)}
                className={`w-full text-left rounded-md px-3 py-2 transition ${
                  current === item.key ? "bg-blue-50 text-blue-700" : "hover:bg-slate-50 text-slate-700"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] bg-slate-200 text-slate-500 rounded px-1 py-0.5 leading-none">
                      {item.badge}
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">{item.description}</div>
              </button>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}
