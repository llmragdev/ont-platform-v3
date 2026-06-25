"use client";

import {
  Activity,
  AppWindow,
  ChevronsLeft,
  ChevronsRight,
  Boxes,
  Bot,
  Database,
  FileSearch,
  GitBranch,
  History,
  Layers3,
  LayoutDashboard,
  Network,
  Route,
  ScrollText,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Wrench,
  Workflow,
} from "lucide-react";
import type { ComponentType } from "react";
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
  | "skills"
  | "app-builder"
  | "workflow-ontology-trace"
  | "writeback-dlq"
  | "audit"
  | "integration-test"
  | "ontology-schema"
  | "ontology-instance"
  | "ontology-graph-edit"
  | "data-flow"
  | "pipeline-builder";

type SidebarItem = {
  key: ViewKey;
  label: string;
  description: string;
  icon: ComponentType<{ className?: string }>;
};

type SidebarGroup = {
  title: string;
  summary: string;
  items: SidebarItem[];
};

const GROUPS: SidebarGroup[] = [
  {
    title: "워크플로우",
    summary: "템플릿, 실행, 추적",
    items: [
      { key: "workflow-home", label: "워크플로우 홈", description: "템플릿과 최근 실행 현황", icon: LayoutDashboard },
      { key: "template-gallery", label: "템플릿 갤러리", description: "복제해서 시작하는 업무 흐름", icon: Layers3 },
      { key: "workflow-graph", label: "빌더와 실행", description: "캔버스 편집, 실행, 온톨로지 매핑", icon: Workflow },
      { key: "skills", label: "스킬 관리", description: "워크플로우 실행 기능 카탈로그", icon: Wrench },
      { key: "pipeline-builder", label: "파이프라인 빌더", description: "시각적 노드 조립형 데이터 파이프라인 설계", icon: GitBranch },
      { key: "workflow-ontology-trace", label: "실행 추적", description: "실행 결과와 온톨로지 흐름", icon: Route },
      { key: "data-flow", label: "데이터 흐름", description: "수집부터 온톨로지 저장까지 흐름 추적", icon: Route },
      { key: "workflow", label: "승인 워크플로우", description: "상태 전이와 담당자 액션", icon: ShieldCheck },
      { key: "writeback-dlq", label: "Writeback DLQ", description: "외부 등록 실패 큐 모니터링", icon: History },
    ],
  },
  {
    title: "앱 빌더",
    summary: "Streamlit 스타일 앱",
    items: [
      {
        key: "app-builder",
        label: "Streamlit 앱",
        description: "질의 결과를 업무 앱과 공유 화면으로 구성",
        icon: AppWindow,
      },
    ],
  },
  {
    title: "온톨로지",
    summary: "객체, 관계, 스키마",
    items: [
      { key: "ontology-graph", label: "관계 탐색", description: "객체와 관계를 그래프로 조회", icon: Network },
      { key: "ontology-schema", label: "스키마 관리", description: "엔티티와 관계 타입 정의", icon: Settings2 },
      { key: "ontology-instance", label: "인스턴스 편집", description: "객체 데이터 생성과 수정", icon: Boxes },
      { key: "ontology-graph-edit", label: "관계 그래프 편집", description: "객체 연결과 배치 편집", icon: GitBranch },
      { key: "rdf-workbench", label: "RDF 워크벤치", description: "RDF 가져오기와 연결 데이터", icon: Database },
    ],
  },
  {
    title: "질의와 분석",
    summary: "AI, RAG, SPARQL",
    items: [
      { key: "dashboard", label: "대시보드", description: "주요 지표와 작업 큐", icon: Activity },
      { key: "explorer", label: "객체 탐색", description: "온톨로지 엔티티 빠른 조회", icon: Search },
      { key: "ai-query", label: "온톨로지 질의", description: "AI 기반 업무 질의", icon: Bot },
      { key: "hybrid-query", label: "통합 질의", description: "온톨로지와 RAG 결합 분석", icon: Sparkles },
      { key: "rag-query", label: "문서 RAG 질의", description: "문서 근거 기반 답변", icon: FileSearch },
      { key: "sparql-query", label: "SPARQL 콘솔", description: "정형 그래프 쿼리 실행", icon: ScrollText },
    ],
  },
  {
    title: "운영과 검증",
    summary: "감사, 테스트",
    items: [
      { key: "audit", label: "감사 로그", description: "사용자와 외부 호출 기록", icon: ScrollText },
      { key: "integration-test", label: "통합 테스트", description: "질의와 근거 품질 검증", icon: ShieldCheck },
    ],
  },
];

export function Sidebar({
  current,
  onSelect,
  collapsed = false,
  onCollapsedChange,
}: {
  current: ViewKey;
  onSelect: (view: ViewKey) => void;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
}) {
  const { user, setUser, presets } = useUserContext();

  return (
    <aside className={`flex w-full shrink-0 flex-col border-b border-slate-200 bg-white transition-all duration-200 md:h-screen md:border-b-0 md:border-r ${collapsed ? "md:w-16" : "md:w-64"}`}>
      <div className={`border-b border-slate-200 px-3 py-4 md:py-5 ${collapsed ? "md:px-2" : "md:px-4"}`}>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-700 text-white shadow-sm">
            <Network className="h-5 w-5 text-teal-100" />
          </div>
          <div className={`min-w-0 ${collapsed ? "md:hidden" : ""}`}>
            <h1 className="truncate text-sm font-extrabold tracking-wide text-slate-900 uppercase">Ontology Console v5</h1>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Workflow Workbench</p>
          </div>
          <button
            type="button"
            onClick={() => onCollapsedChange?.(!collapsed)}
            className={`ml-auto hidden h-8 w-8 items-center justify-center rounded-md border border-slate-200 text-slate-500 hover:bg-slate-50 md:inline-flex ${collapsed ? "md:ml-0" : ""}`}
            title={collapsed ? "메뉴 펼치기" : "메뉴 접기"}
          >
            {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
          </button>
        </div>

        <div className={`mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 ${collapsed ? "md:hidden" : ""}`}>
          <label className="text-[9px] font-extrabold uppercase tracking-wider text-slate-500">현재 사용자</label>
          <select
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900 transition focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100"
            value={user.userId}
            onChange={(event) => {
              const preset = presets.find((item) => item.userId === event.target.value);
              if (preset) setUser(preset);
            }}
          >
            {presets.map((preset) => (
              <option key={preset.userId} value={preset.userId}>
                {preset.userId} ({preset.role})
              </option>
            ))}
          </select>
          <div className="mt-2.5 flex flex-wrap gap-1.5 text-[9px] font-bold tracking-wider uppercase">
            <span className="rounded-md bg-white border border-slate-200 px-2.5 py-0.5 text-slate-500">{user.companyId}</span>
            <span className="rounded-md bg-white border border-slate-200 px-2.5 py-0.5 text-slate-500">{user.projectId}</span>
          </div>
        </div>
      </div>

      <nav className={`max-h-72 flex-1 overflow-y-auto p-2.5 md:max-h-none ${collapsed ? "md:px-2" : ""}`}>
        <div className={collapsed ? "space-y-2 md:space-y-1" : "space-y-4"}>
          {GROUPS.map((group) => (
            <section key={group.title} className="space-y-1">
              <div className={`mb-1.5 px-2.5 ${collapsed ? "md:hidden" : ""}`}>
                <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500">{group.title}</div>
                <div className="text-[9px] font-medium tracking-wide text-slate-600">{group.summary}</div>
              </div>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = current === item.key;
                  return (
                    <button
                      key={item.key}
                      type="button"
                      data-testid={`nav-${item.key}`}
                      onClick={() => onSelect(item.key)}
                      title={collapsed ? item.label : undefined}
                      className={`group flex w-full items-start gap-2.5 rounded-lg px-3 py-2.5 text-left transition-all duration-150 ${collapsed ? "md:justify-center md:px-2" : ""} ${
                        active
                          ? "bg-teal-50 text-teal-900 border border-teal-200"
                          : "text-slate-600 border border-transparent hover:bg-slate-50 hover:text-slate-900"
                      }`}
                    >
                      <span className={`mt-0.5 flex h-7.5 w-7.5 shrink-0 items-center justify-center rounded-lg transition-colors ${
                        active 
                          ? "bg-teal-700 text-white shadow-sm" 
                          : "bg-slate-100 border border-slate-200 text-slate-500 group-hover:text-teal-700 group-hover:border-teal-200"
                      }`}>
                        <Icon className="h-3.5 w-3.5" />
                      </span>
                      <span className={`min-w-0 ${collapsed ? "md:hidden" : ""}`}>
                        <span className="block truncate text-xs font-bold tracking-wide">{item.label}</span>
                        <span className="mt-0.5 block text-[10px] leading-4 text-slate-500 group-hover:text-slate-600 transition-colors">{item.description}</span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      </nav>
    </aside>
  );
}
