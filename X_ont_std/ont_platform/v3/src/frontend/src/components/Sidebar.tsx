"use client";
import { useUserContext } from "@/context/UserContext";

export type ViewKey =
  | "dashboard"
  | "explorer"
  | "ontology-graph"
  | "ai-query"
  | "sparql-query"
  | "rag-query"
  | "hybrid-query"
  | "workflow"
  | "workflow-graph"
  | "audit"
  | "integration-test"
  | "ontology-schema"
  | "ontology-instance"
  | "ontology-graph-edit"
  | "metadata";

type SidebarGroup = {
  title: string;
  items: { key: ViewKey; label: string; description: string }[];
};

const GROUPS: SidebarGroup[] = [
  {
    title: "분석 · 질의",
    items: [
      { key: "dashboard",    label: "대시보드",       description: "승인 대기 및 주요 지표" },
      { key: "explorer",     label: "객체 탐색",      description: "온톨로지 엔티티 조회" },
      { key: "ai-query",     label: "온톨로지 질의",  description: "AI 하이브리드 질의" },
      { key: "sparql-query", label: "SPARQL 콘솔",    description: "표준 쿼리 실행·성능 확인" },
      { key: "rag-query",    label: "문서 RAG 질의",  description: "PDF 업로드 + 질문 답변" },
      { key: "hybrid-query", label: "통합 질의",      description: "온톨로지 + RAG 복합 분석" },
    ],
  },
  {
    title: "온톨로지 관리",
    items: [
      { key: "ontology-schema",     label: "스키마 정의",      description: "엔티티·관계 유형 관리" },
      { key: "ontology-instance",   label: "인스턴스 편집",    description: "엔티티 수정·추가" },
      { key: "ontology-graph-edit", label: "관계 그래프 편집", description: "React Flow 노드·엣지 편집" },
      { key: "metadata",            label: "메타데이터",       description: "계보·품질·감사 추적" },
      { key: "ontology-graph",      label: "온톨로지 그래프",  description: "객체-관계 시각화" },
    ],
  },
  {
    title: "워크플로우",
    items: [
      { key: "workflow",       label: "승인 워크플로우",   description: "상태 전이 액션" },
      { key: "workflow-graph", label: "워크플로우 그래프", description: "React Flow 캔버스 + 실행" },
    ],
  },
  {
    title: "운영",
    items: [
      { key: "audit",            label: "감사 로그",   description: "운영 이벤트 기록" },
      { key: "integration-test", label: "통합 테스트", description: "온톨로지+RAG 자동 검증" },
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
    <aside className="w-full shrink-0 border-b border-slate-200 bg-white flex flex-col dark:bg-slate-900 dark:border-slate-800 md:h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="px-4 py-4 border-b border-slate-200 dark:border-slate-800 md:py-5">
        <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">Ontology Console</h1>
        <p className="text-xs text-slate-500 mt-0.5 dark:text-slate-400">v2.0 · AI 업무 의사결정 플랫폼</p>
        <div className="mt-2">
          <select
            className="w-full border border-slate-200 rounded px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200"
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
      <nav className="max-h-52 flex-1 overflow-y-auto p-2 space-y-3 md:max-h-none">
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
                    ? "bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-200"
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
