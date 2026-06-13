"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { Sidebar, type ViewKey } from "@/components/Sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ThemeContextProvider } from "@/context/ThemeContext";
import { UserContextProvider } from "@/context/UserContext";
import { checkHealth } from "@/lib/api";

function ViewSkeleton() {
  return (
    <div data-testid="view-loading" className="grid gap-4 md:grid-cols-2">
      <div className="panel h-48 animate-pulse bg-slate-50" />
      <div className="panel h-48 animate-pulse bg-slate-50" />
      <div className="panel h-64 animate-pulse bg-slate-50 md:col-span-2" />
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
const WorkflowOntologyTrace = dynamic(() => import("@/components/WorkflowOntologyTrace").then((mod) => mod.WorkflowOntologyTrace), { loading: ViewSkeleton });
const DLQDashboard = dynamic(() => import("@/components/WriteBack/DLQDashboard").then((mod) => mod.DLQDashboard), { loading: ViewSkeleton });
const OntologySchemaManager = dynamic(() => import("@/components/OntologySchemaManager").then((mod) => mod.OntologySchemaManager), { loading: ViewSkeleton });
const OntologyInstanceEditor = dynamic(() => import("@/components/OntologyInstanceEditor").then((mod) => mod.OntologyInstanceEditor), { loading: ViewSkeleton });
const OntologyGraphEditor = dynamic(() => import("@/components/OntologyGraphEditor").then((mod) => mod.OntologyGraphEditor), { loading: ViewSkeleton });
const OntologyExplorerCanvas = dynamic(() => import("@/components/OntologyExplorerCanvas").then((mod) => mod.OntologyExplorerCanvas), { loading: ViewSkeleton });
const AuditDashboard = dynamic(() => import("@/components/AuditDashboard").then((mod) => mod.AuditDashboard), { loading: ViewSkeleton });
const IntegrationTestRunner = dynamic(() => import("@/components/IntegrationTestRunner").then((mod) => mod.IntegrationTestRunner), { loading: ViewSkeleton });

const VIEW_TITLES: Record<ViewKey, string> = {
  "dashboard": "대시보드",
  "workflow-home": "Workflow Home",
  "template-gallery": "Template Gallery",
  "explorer": "객체 탐색",
  "ai-query": "온톨로지 질의",
  "sparql-query": "SPARQL 콘솔",
  "rdf-workbench": "RDF Lab",
  "rag-query": "문서 RAG 질의",
  "hybrid-query": "통합 질의",
  "workflow": "승인 워크플로우",
  "workflow-graph": "Workflow Builder",
  "workflow-ontology-trace": "Workflow Trace",
  "writeback-dlq": "Writeback DLQ",
  "audit": "감사 로그",
  "integration-test": "통합 테스트",
  "ontology-schema": "스키마 정의",
  "ontology-instance": "인스턴스 편집",
  "ontology-graph-edit": "관계 그래프 편집",
  "ontology-graph": "온톨로지 그래프",
};

function AppContent() {
  const [view, setView] = useState<ViewKey>("workflow-home");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    checkHealth().then((ok) => setBackendStatus(ok ? "online" : "offline"));
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-100 dark:bg-slate-950 md:flex-row">
      <Sidebar current={view} onSelect={setView} />

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="shrink-0 border-b border-slate-200 bg-white px-4 py-3 flex items-center justify-between dark:border-slate-800 dark:bg-slate-900 md:px-6">
          <h1 data-testid="view-title" className="text-base font-bold text-slate-900 dark:text-slate-100">{VIEW_TITLES[view]}</h1>
          <div className="flex items-center gap-3">
            {backendStatus === "checking" && (
              <span className="text-xs text-slate-400 animate-pulse">연결 확인 중</span>
            )}
            {backendStatus !== "checking" && (
              <div className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
                backendStatus === "online" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
              }`}>
                <span className={`h-1.5 w-1.5 rounded-full ${backendStatus === "online" ? "bg-emerald-500 animate-pulse" : "bg-amber-400"}`} />
                {backendStatus === "online" ? "LIVE" : "DEMO"}
              </div>
            )}
            <ThemeToggle />
          </div>
        </header>

        <main data-testid="app-main" className="flex-1 overflow-y-auto p-3 md:p-6">
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
          {view === "workflow-ontology-trace" && <WorkflowOntologyTrace />}
          {view === "writeback-dlq" && <DLQDashboard />}
          {view === "ontology-schema" && <OntologySchemaManager />}
          {view === "ontology-instance" && <OntologyInstanceEditor />}
          {view === "ontology-graph-edit" && <OntologyGraphEditor />}
          {view === "ontology-graph" && <OntologyExplorerCanvas />}
          {view === "audit" && <AuditDashboard />}
          {view === "integration-test" && <IntegrationTestRunner />}
        </main>
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
