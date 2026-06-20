"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { Activity, CheckCircle2, CloudOff, FolderGit2 } from "lucide-react";
import { Sidebar, type ViewKey } from "@/components/Sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { AIAssistantPanel } from "@/components/AIAssistantPanel";
import { ThemeContextProvider } from "@/context/ThemeContext";
import { UserContextProvider, useUserContext } from "@/context/UserContext";
import { checkHealth } from "@/lib/api";

function ViewSkeleton() {
  return (
    <div data-testid="view-loading" className="grid gap-4 md:grid-cols-2">
      <div className="panel h-48 animate-pulse bg-slate-50 dark:bg-slate-900" />
      <div className="panel h-48 animate-pulse bg-slate-50 dark:bg-slate-900" />
      <div className="panel h-64 animate-pulse bg-slate-50 dark:bg-slate-900 md:col-span-2" />
    </div>
  );
}

const Dashboard = dynamic(() => import("@/components/Dashboard").then((mod) => mod.Dashboard), { loading: ViewSkeleton });
const WorkflowHome = dynamic(() => import("@/components/WorkflowHome").then((mod) => mod.WorkflowHome), { loading: ViewSkeleton });
const TemplateGallery = dynamic(() => import("@/components/TemplateGallery").then((mod) => mod.TemplateGallery), { loading: ViewSkeleton });
const Explorer = dynamic(() => import("@/components/Explorer").then((mod) => mod.Explorer), { loading: ViewSkeleton });
const AIQuery = dynamic(() => import("@/components/AIQuery").then((mod) => mod.AIQuery), { loading: ViewSkeleton });
const HybridQuery = dynamic(() => import("@/components/HybridQuery").then((mod) => mod.HybridQuery), { loading: ViewSkeleton });
const SPARQLWorkbench = dynamic(() => import("@/components/SPARQLWorkbench").then((mod) => mod.SPARQLWorkbench), { loading: ViewSkeleton });
const RDFWorkbench = dynamic(() => import("@/components/RDF/RDFWorkbench").then((mod) => mod.RDFWorkbench), { loading: ViewSkeleton });
const RAGQuery = dynamic(() => import("@/components/RAGQuery").then((mod) => mod.RAGQuery), { loading: ViewSkeleton });
const Workflow = dynamic(() => import("@/components/Workflow").then((mod) => mod.Workflow), { loading: ViewSkeleton });
const WorkflowGraphPanel = dynamic(() => import("@/components/WorkflowGraph").then((mod) => mod.WorkflowGraphPanel), { loading: ViewSkeleton });
const SkillManager = dynamic(() => import("@/components/SkillManager").then((mod) => mod.SkillManager), { loading: ViewSkeleton });
const StreamlitAppBuilder = dynamic(() => import("@/components/StreamlitAppBuilder").then((mod) => mod.StreamlitAppBuilder), { loading: ViewSkeleton });
const WorkflowOntologyTrace = dynamic(() => import("@/components/WorkflowOntologyTrace").then((mod) => mod.WorkflowOntologyTrace), { loading: ViewSkeleton });
const DataFlowView = dynamic(() => import("@/components/DataFlowView").then((mod) => mod.DataFlowView), { loading: ViewSkeleton });
const DLQDashboard = dynamic(() => import("@/components/WriteBack/DLQDashboard").then((mod) => mod.DLQDashboard), { loading: ViewSkeleton });
const OntologySchemaManager = dynamic(() => import("@/components/OntologySchemaManager").then((mod) => mod.OntologySchemaManager), { loading: ViewSkeleton });
const OntologyInstanceEditor = dynamic(() => import("@/components/OntologyInstanceEditor").then((mod) => mod.OntologyInstanceEditor), { loading: ViewSkeleton });
const OntologyGraphEditor = dynamic(() => import("@/components/OntologyGraphEditor").then((mod) => mod.OntologyGraphEditor), { loading: ViewSkeleton });
const OntologyExplorerCanvas = dynamic(() => import("@/components/OntologyExplorerCanvas").then((mod) => mod.OntologyExplorerCanvas), { loading: ViewSkeleton });
const AuditDashboard = dynamic(() => import("@/components/AuditDashboard").then((mod) => mod.AuditDashboard), { loading: ViewSkeleton });
const IntegrationTestRunner = dynamic(() => import("@/components/IntegrationTestRunner").then((mod) => mod.IntegrationTestRunner), { loading: ViewSkeleton });
const PipelineBuilderView = dynamic(() => import("@/components/PipelineBuilderView").then((mod) => mod.PipelineBuilderView), { loading: ViewSkeleton });

const VIEW_META: Record<ViewKey, { title: string; section: string; description: string }> = {
  dashboard: { title: "대시보드", section: "질의와 분석", description: "주요 지표, 작업 큐, 운영 상태를 확인합니다." },
  "workflow-home": { title: "워크플로우 홈", section: "워크플로우", description: "템플릿, 실행 현황, 최근 작업을 한 곳에서 시작합니다." },
  "template-gallery": { title: "템플릿 갤러리", section: "워크플로우", description: "시나리오 템플릿을 복제해서 프로젝트 워크플로우로 만듭니다." },
  explorer: { title: "객체 탐색", section: "질의와 분석", description: "온톨로지 객체와 속성을 빠르게 검색합니다." },
  "ai-query": { title: "온톨로지 질의", section: "질의와 분석", description: "AI가 온톨로지 근거를 바탕으로 업무 질문에 답합니다." },
  "sparql-query": { title: "SPARQL 콘솔", section: "질의와 분석", description: "정형 그래프 쿼리를 작성하고 실행합니다." },
  "rdf-workbench": { title: "RDF 워크벤치", section: "온톨로지", description: "RDF 가져오기, 매핑, 연결 데이터 확인을 수행합니다." },
  "rag-query": { title: "문서 RAG 질의", section: "질의와 분석", description: "문서 근거를 기반으로 답변을 생성합니다." },
  "hybrid-query": { title: "통합 질의", section: "질의와 분석", description: "온톨로지와 문서 RAG를 결합해 분석합니다." },
  workflow: { title: "승인 워크플로우", section: "워크플로우", description: "승인, 대기, 반려 같은 상태 전이 작업을 처리합니다." },
  "workflow-graph": { title: "빌더와 실행", section: "워크플로우", description: "캔버스에서 업무 흐름을 편집하고 실행 결과를 확인합니다." },
  skills: { title: "스킬 관리", section: "워크플로우", description: "워크플로우 노드에서 재사용할 실행 기능과 외부 연동 스킬을 관리합니다." },
  "app-builder": { title: "Streamlit 앱", section: "앱 빌더", description: "질의 결과와 App Spec을 업무 앱, 미리보기, 공유 화면으로 구성합니다." },
  "workflow-ontology-trace": { title: "실행 추적", section: "워크플로우", description: "워크플로우 실행이 온톨로지 객체와 관계로 어떻게 남았는지 봅니다." },
  "data-flow": { title: "데이터 흐름", section: "워크플로우", description: "외부 데이터 유입부터 워크플로우 처리, 온톨로지 저장까지의 흐름을 계보로 모니터링합니다." },
  "writeback-dlq": { title: "Writeback DLQ", section: "워크플로우", description: "외부 시스템 등록 실패와 재처리 대상을 모니터링합니다." },
  audit: { title: "감사 로그", section: "운영과 검증", description: "사용자 작업, 외부 호출, 시스템 이벤트를 추적합니다." },
  "integration-test": { title: "통합 테스트", section: "운영과 검증", description: "질의 품질과 근거 연결 상태를 테스트합니다." },
  "ontology-schema": { title: "스키마 관리", section: "온톨로지", description: "엔티티 타입과 관계 타입을 관리합니다." },
  "ontology-instance": { title: "인스턴스 편집", section: "온톨로지", description: "실제 객체 데이터를 생성하고 수정합니다." },
  "ontology-graph-edit": { title: "관계 그래프 편집", section: "온톨로지", description: "객체 간 관계를 배치하고 연결합니다." },
  "ontology-graph": { title: "관계 탐색", section: "온톨로지", description: "온톨로지 객체와 관계 흐름을 시각적으로 탐색합니다." },
  "pipeline-builder": { title: "파이프라인 빌더", section: "워크플로우", description: "드래그 앤 드롭 방식으로 데이터 수집, 가공, 적재 흐름을 시각적으로 설계하고 배포합니다." },
};

function StatusPill({ status }: { status: "checking" | "online" | "offline" }) {
  if (status === "checking") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
        <Activity className="h-3.5 w-3.5 animate-pulse" />
        연결 확인 중
      </span>
    );
  }

  const online = status === "online";
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
      online ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200" : "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-200"
    }`}>
      {online ? <CheckCircle2 className="h-3.5 w-3.5" /> : <CloudOff className="h-3.5 w-3.5" />}
      {online ? "LIVE" : "DEMO"}
    </span>
  );
}

function AppHeader({
  view,
  backendStatus,
}: {
  view: ViewKey;
  backendStatus: "checking" | "online" | "offline";
}) {
  const { user } = useUserContext();
  const meta = VIEW_META[view];

  return (
    <header className="shrink-0 border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900 md:px-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <span>{meta.section}</span>
            <span>/</span>
            <span>{user.role}</span>
          </div>
          <h1 data-testid="view-title" className="mt-0.5 truncate text-xl font-bold text-slate-950 dark:text-slate-100">{meta.title}</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{meta.description}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
            <FolderGit2 className="h-3.5 w-3.5" />
            {user.companyId} / {user.projectId}
          </span>
          <StatusPill status={backendStatus} />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

function RenderView({ view, setView }: { view: ViewKey; setView: (view: ViewKey) => void }) {
  return (
    <>
      {view === "dashboard" && <Dashboard />}
      {view === "workflow-home" && <WorkflowHome onNavigate={setView} />}
      {view === "template-gallery" && <TemplateGallery onNavigate={setView} />}
      {view === "explorer" && <Explorer />}
      {view === "ai-query" && <AIQuery />}
      {view === "sparql-query" && <SPARQLWorkbench />}
      {view === "rdf-workbench" && <RDFWorkbench />}
      {view === "rag-query" && <RAGQuery />}
      {view === "hybrid-query" && <HybridQuery />}
      {view === "workflow" && <Workflow />}
      {view === "workflow-graph" && <WorkflowGraphPanel />}
      {view === "skills" && <SkillManager />}
      {view === "app-builder" && <StreamlitAppBuilder />}
      {view === "workflow-ontology-trace" && <WorkflowOntologyTrace />}
      {view === "data-flow" && <DataFlowView />}
      {view === "writeback-dlq" && <DLQDashboard />}
      {view === "ontology-schema" && <OntologySchemaManager />}
      {view === "ontology-instance" && <OntologyInstanceEditor />}
      {view === "ontology-graph-edit" && <OntologyGraphEditor />}
      {view === "ontology-graph" && <OntologyExplorerCanvas />}
      {view === "audit" && <AuditDashboard />}
      {view === "integration-test" && <IntegrationTestRunner />}
      {view === "pipeline-builder" && <PipelineBuilderView />}
    </>
  );
}

function AppContent() {
  const [view, setView] = useState<ViewKey>("workflow-home");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);

  useEffect(() => {
    checkHealth().then((ok) => setBackendStatus(ok ? "online" : "offline"));
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-100 dark:bg-slate-950 md:flex-row">
      <Sidebar current={view} onSelect={setView} collapsed={sidebarCollapsed} onCollapsedChange={setSidebarCollapsed} />

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <AppHeader view={view} backendStatus={backendStatus} />

        <div className="flex min-h-0 flex-1 overflow-hidden">
          <main data-testid="app-main" className="min-w-0 flex-1 overflow-y-auto p-3 md:p-6">
            <RenderView view={view} setView={setView} />
          </main>
          <AIAssistantPanel view={view} open={assistantOpen} onOpenChange={setAssistantOpen} />
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <ThemeContextProvider>
      <UserContextProvider>
        <AppContent />
      </UserContextProvider>
    </ThemeContextProvider>
  );
}
