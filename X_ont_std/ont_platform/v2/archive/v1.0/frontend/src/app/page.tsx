"use client";
import { useCallback, useEffect, useState } from "react";
import { api, ApiClientError } from "@/lib/api";
import type { Customer, Order, OrderContext, User, WorkflowQueueRow } from "@/types/api";
import { Sidebar, type ViewKey } from "@/components/Sidebar";
import { ContextPanel } from "@/components/ContextPanel";
import { Dashboard } from "@/components/Dashboard";
import { Explorer } from "@/components/Explorer";
import { AIQuery } from "@/components/AIQuery";
import { RAGQuery } from "@/components/RAGQuery";
import { HybridQuery } from "@/components/HybridQuery";
import { Workflow } from "@/components/Workflow";
import { WorkflowGraphPanel } from "@/components/WorkflowGraph";
import { OntologyExplorerCanvas } from "@/components/OntologyExplorerCanvas";
import { OntologySchemaManager } from "@/components/OntologySchemaManager";
import { OntologyInstanceEditor } from "@/components/OntologyInstanceEditor";
import { OntologyGraphEditor } from "@/components/OntologyGraphEditor";
import { Audit } from "@/components/Audit";
import { UserSwitcher } from "@/components/UserSwitcher";
import { TenantUserSwitcher } from "@/components/TenantUserSwitcher";
import { LoginPanel } from "@/components/LoginPanel";
import { clearSession, getStoredUser, getToken } from "@/lib/auth";

const titles: Record<ViewKey, [string, string]> = {
  dashboard:               ["대시보드",         "승인 대기 주문 및 주요 지표를 확인합니다."],
  explorer:                ["객체 탐색",        "온톨로지 객체와 관계를 탐색합니다."],
  "ontology-graph":        ["온톨로지 그래프",   "객체와 관계를 React Flow 캔버스로 시각화합니다."],
  "ai-query":              ["온톨로지 질의",     "객체 ID(O001, C002 등)를 포함한 질문으로 AI 의사결정 분석."],
  "rag-query":             ["문서 RAG 질의",    "PDF 파일을 업로드하고 내용에 대해 자유롭게 질문합니다."],
  "hybrid-query":          ["통합 질의",        "질문 유형 자동 감지 → 온톨로지 구조형 질의 + RAG 혼합 답변."],
  workflow:                ["승인 워크플로우",   "역할/리스크/금액에 따라 허용된 액션만 실행됩니다."],
  "workflow-graph":        ["워크플로우 그래프", "React Flow 캔버스로 노드를 배치하고 시뮬레이션 실행합니다."],
  audit:                   ["감사 로그",        "운영 이벤트 기록을 확인합니다."],
  "ontology-schema":       ["스키마 정의",      "엔티티 유형·관계 유형을 등록하고 관리합니다."],
  "ontology-instance":     ["인스턴스 편집",    "PDF에서 추출된 엔티티를 조회·수정·추가합니다."],
  "ontology-graph-edit":   ["관계 그래프 편집", "React Flow 캔버스에서 노드와 엣지를 직접 편집합니다."],
};

type AuthMode = "demo" | "jwt";
const AUTH_REQUIRED = process.env.NEXT_PUBLIC_AUTH_REQUIRED === "true";

export default function HomePage() {
  const [authMode, setAuthMode] = useState<AuthMode>("demo");
  const [authReady, setAuthReady] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [currentUserKey, setCurrentUserKey] = useState<string>("analyst");
  const [view, setView] = useState<ViewKey>("dashboard");
  const [orders, setOrders] = useState<Order[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [queue, setQueue] = useState<WorkflowQueueRow[]>([]);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [context, setContext] = useState<OrderContext | null>(null);
  const [contextError, setContextError] = useState<string | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [llmProvider, setLlmProvider] = useState<string | undefined>(undefined);
  const [globalError, setGlobalError] = useState<string | null>(null);

  useEffect(() => {
    // 마운트 시 JWT 토큰 확인 — 있으면 jwt 모드로 진입
    const token = getToken();
    const stored = getStoredUser();
    if (token && stored) {
      setAuthMode("jwt");
      setCurrentUserKey(stored.key ?? stored.id);
    }
    setAuthReady(true);
  }, []);

  useEffect(() => {
    if (!authReady) return;
    if (AUTH_REQUIRED && authMode !== "jwt") return; // 로그인 강제 시 데이터 안 가져옴
    (async () => {
      try {
        const [usersRes, health] = await Promise.all([api.users(), api.health()]);
        setUsers(usersRes.users);
        setLlmProvider(health.llm_provider);
      } catch (err) {
        setGlobalError(err instanceof Error ? err.message : String(err));
      }
    })();
  }, [authReady, authMode]);

  function handleLogout() {
    clearSession();
    setAuthMode("demo");
    setCurrentUserKey("analyst");
  }

  function handleLoginSuccess() {
    const stored = getStoredUser();
    if (stored) {
      setAuthMode("jwt");
      setCurrentUserKey(stored.key ?? stored.id);
    }
  }

  const refreshData = useCallback(async () => {
    try {
      const [ordersRes, customersRes, queueRes] = await Promise.all([
        api.orders(currentUserKey),
        api.customers(currentUserKey),
        api.workflowQueue(currentUserKey),
      ]);
      setOrders(ordersRes.orders);
      setCustomers(customersRes.customers);
      setQueue(queueRes.queue);
      if (!selectedOrderId && ordersRes.orders[0]) {
        setSelectedOrderId(ordersRes.orders[0].id);
      }
      setGlobalError(null);
    } catch (err) {
      setGlobalError(err instanceof Error ? err.message : String(err));
    }
  }, [currentUserKey, selectedOrderId]);

  useEffect(() => {
    void refreshData();
  }, [refreshData]);

  useEffect(() => {
    if (!selectedOrderId) {
      setContext(null);
      return;
    }
    let cancelled = false;
    setContextLoading(true);
    setContextError(null);
    (async () => {
      try {
        const response = await api.orderContext(currentUserKey, selectedOrderId);
        if (!cancelled) setContext(response);
      } catch (err) {
        if (!cancelled) {
          if (err instanceof ApiClientError) {
            setContextError(`[${err.code}] ${err.message}`);
          } else {
            setContextError(err instanceof Error ? err.message : String(err));
          }
          setContext(null);
        }
      } finally {
        if (!cancelled) setContextLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [currentUserKey, selectedOrderId]);

  const [viewTitle, viewDesc] = titles[view];

  // 인증 강제 모드 + 미로그인 → 로그인 화면
  if (authReady && AUTH_REQUIRED && authMode !== "jwt") {
    return <LoginPanel onSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="flex h-screen">
      <Sidebar current={view} onSelect={setView} llmProvider={llmProvider} />
      <main className="flex-1 overflow-y-auto">
        <header className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-white">
          <div>
            <h2 className="text-xl font-bold">{viewTitle}</h2>
            <p className="text-xs text-slate-500 mt-0.5">{viewDesc}</p>
          </div>
          <div className="flex items-center gap-3">
            {selectedOrderId && (
              <span className="badge badge-neutral">선택: {selectedOrderId}</span>
            )}
            {/* 기존 워크플로우 사용자 전환 */}
            <UserSwitcher
              users={users}
              current={currentUserKey}
              onChange={setCurrentUserKey}
              authMode={authMode}
              onLogout={handleLogout}
            />
            {/* 테넌트 사용자 전환 (멀티테넌트 권한 관리) */}
            <TenantUserSwitcher />
          </div>
        </header>

        <div className="px-6 py-6">
          {globalError && (
            <div className="mb-4 rounded-md bg-rose-50 border border-rose-200 text-rose-700 text-sm px-3 py-2">
              {globalError}
            </div>
          )}
          {view === "dashboard" && (
            <Dashboard orders={orders} queue={queue} onSelect={setSelectedOrderId} selectedId={selectedOrderId} />
          )}
          {view === "explorer" && (
            <Explorer customers={customers} orders={orders} onSelectOrder={setSelectedOrderId} selectedId={selectedOrderId} />
          )}
          {view === "ai-query" && <AIQuery user={currentUserKey} />}
          {view === "rag-query" && <RAGQuery user={currentUserKey} />}
          {view === "hybrid-query" && <HybridQuery user={currentUserKey} />}
          {view === "workflow" && <Workflow user={currentUserKey} queue={queue} onAfterExecute={refreshData} />}
          {view === "ontology-graph" && <OntologyExplorerCanvas user={currentUserKey} />}
          {view === "workflow-graph" && <WorkflowGraphPanel user={currentUserKey} />}
          {view === "audit" && <Audit />}
          {view === "ontology-schema" && <OntologySchemaManager />}
          {view === "ontology-instance" && <OntologyInstanceEditor />}
          {view === "ontology-graph-edit" && <OntologyGraphEditor />}
        </div>
      </main>
      <ContextPanel context={context} loading={contextLoading} error={contextError} />
    </div>
  );
}
