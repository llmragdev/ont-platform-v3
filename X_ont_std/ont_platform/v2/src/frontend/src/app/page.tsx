"use client";

import { useEffect, useState } from "react";
import { Sidebar, type ViewKey } from "@/components/Sidebar";
import { Dashboard } from "@/components/Dashboard";
import { Explorer } from "@/components/Explorer";
import { AIQuery } from "@/components/AIQuery";
import { HybridQuery } from "@/components/HybridQuery";
import { RAGQuery } from "@/components/RAGQuery";
import { Workflow } from "@/components/Workflow";
import { WorkflowGraphPanel } from "@/components/WorkflowGraph";
import { OntologySchemaManager } from "@/components/OntologySchemaManager";
import { OntologyInstanceEditor } from "@/components/OntologyInstanceEditor";
import { OntologyGraphEditor } from "@/components/OntologyGraphEditor";
import { OntologyExplorerCanvas } from "@/components/OntologyExplorerCanvas";
import { Audit } from "@/components/Audit";
import { UserContextProvider } from "@/context/UserContext";
import { checkHealth } from "@/lib/api";

const VIEW_TITLES: Record<ViewKey, string> = {
  "dashboard":          "대시보드",
  "explorer":           "객체 탐색",
  "ai-query":           "온톨로지 질의",
  "rag-query":          "문서 RAG 질의",
  "hybrid-query":       "통합 질의",
  "workflow":           "승인 워크플로우",
  "workflow-graph":     "워크플로우 그래프",
  "audit":              "감사 로그",
  "ontology-schema":    "스키마 정의",
  "ontology-instance":  "인스턴스 편집",
  "ontology-graph-edit":"관계 그래프 편집",
  "ontology-graph":     "온톨로지 그래프",
};

function AppContent() {
  const [view, setView] = useState<ViewKey>("dashboard");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    checkHealth().then((ok) => setBackendStatus(ok ? "online" : "offline"));
  }, []);

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden">
      <Sidebar current={view} onSelect={setView} />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="shrink-0 bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
          <h1 className="text-base font-bold text-slate-900">{VIEW_TITLES[view]}</h1>
          <div className="flex items-center gap-3">
            {backendStatus === "checking" && (
              <span className="text-xs text-slate-400 animate-pulse">연결 확인 중…</span>
            )}
            {backendStatus !== "checking" && (
              <div className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
                backendStatus === "online" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${backendStatus === "online" ? "bg-emerald-500 animate-pulse" : "bg-amber-400"}`} />
                {backendStatus === "online" ? "LIVE" : "DEMO"}
              </div>
            )}
          </div>
        </header>

        {/* Main scroll area */}
        <main className="flex-1 overflow-y-auto p-6">
          {view === "dashboard"          && <Dashboard />}
          {view === "explorer"           && <Explorer />}
          {view === "ai-query"           && <AIQuery />}
          {view === "rag-query"          && <RAGQuery />}
          {view === "hybrid-query"       && <HybridQuery />}
          {view === "workflow"           && <Workflow />}
          {view === "workflow-graph"     && <WorkflowGraphPanel />}
          {view === "ontology-schema"    && <OntologySchemaManager />}
          {view === "ontology-instance"  && <OntologyInstanceEditor />}
          {view === "ontology-graph-edit"&& <OntologyGraphEditor />}
          {view === "ontology-graph"     && <OntologyExplorerCanvas />}
          {view === "audit"              && <Audit />}
        </main>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <UserContextProvider>
      <AppContent />
    </UserContextProvider>
  );
}
