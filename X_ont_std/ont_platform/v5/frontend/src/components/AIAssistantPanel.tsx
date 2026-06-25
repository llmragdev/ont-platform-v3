"use client";

import { Bot, CheckCircle2, Clipboard, Code2, Loader2, MessageSquareText, PanelRightClose, Send, Sparkles, Workflow, X } from "lucide-react";
import { useEffect, useMemo, useState, useRef } from "react";
import { api, getCurrentTenant } from "@/lib/api";
import type { AssistantChatResponse, AssistantContext } from "@/types/api";
import type { ViewKey } from "@/components/Sidebar";

const VIEW_LABELS: Partial<Record<ViewKey, string>> = {
  "workflow-home": "워크플로우 홈",
  "template-gallery": "템플릿 갤러리",
  "workflow-graph": "빌더와 실행",
  "app-builder": "Streamlit 앱",
  skills: "스킬 관리",
  "workflow-ontology-trace": "실행 추적",
  workflow: "승인 워크플로우",
  "writeback-dlq": "Writeback DLQ",
  "ontology-graph": "관계 탐색",
  "ontology-schema": "스키마 관리",
  "ontology-instance": "인스턴스 편집",
  "ontology-graph-edit": "관계 그래프 편집",
  "rdf-workbench": "RDF 워크벤치",
  dashboard: "대시보드",
  explorer: "객체 탐색",
  "ai-query": "온톨로지 질의",
  "hybrid-query": "통합 질의",
  "rag-query": "문서 RAG 질의",
  "sparql-query": "SPARQL 콘솔",
  audit: "감사 로그",
  "integration-test": "통합 테스트",
};

const QUICK_PROMPTS = [
  "현재 화면을 시연용으로 설명해줘",
  "최근 7일 반복 고장 설비를 조회하는 온톨로지 쿼리 만들어줘",
  "공장 반복 고장 분석 앱을 만들어줘",
  "댓글이 안 달릴 때 점검 순서를 알려줘",
];

const ASSISTANT_SELECTION_KEY = "ont.aiAssistant.selection";
const ASSISTANT_APPLY_CODE_EVENT = "assistant-apply-code";

type AssistantSelection = Pick<
  AssistantContext,
  | "selected_app_id"
  | "selected_app_name"
  | "selected_folder_id"
  | "selected_folder_name"
  | "selected_file_path"
  | "selected_file_name"
  | "selected_language"
>;

function intentLabel(intent?: string) {
  switch (intent) {
    case "create_app":
      return "앱 생성";
    case "edit_streamlit_program":
      return "코딩";
    case "generate_ontology_query":
      return "질의 생성";
    case "analyze_failure":
      return "장애 분석";
    case "suggest_workflow_change":
      return "워크플로우 제안";
    case "explain_current_view":
      return "화면 설명";
    default:
      return "Assistant";
  }
}

function extractPythonCode(text: string) {
  const fenced = text.match(/```python\s*([\s\S]*?)```/i) ?? text.match(/```\s*([\s\S]*?)```/);
  return fenced?.[1]?.trim() ?? "";
}

function renderAnswerText(text: string) {
  // Split by markdown code blocks: ```lang ... ```
  const parts = text.split(/(```[a-zA-Z]*\n[\s\S]*?\n```)/g);
  return parts.map((part, index) => {
    if (part.startsWith("```")) {
      const match = part.match(/```([a-zA-Z]*)\n([\s\S]*?)\n```/);
      const lang = match?.[1] || "";
      const code = match?.[2] || part.replace(/```[a-zA-Z]*\n|```$/g, "");
      return (
        <div key={index} className="my-1.5 overflow-hidden rounded-md border border-slate-200 dark:border-slate-800">
          <div className="bg-slate-50 px-2 py-1 text-[9px] font-bold text-slate-500 border-b border-slate-200 dark:bg-slate-900 dark:border-slate-800 flex justify-between items-center">
            <span>{lang.toUpperCase() || "CODE"}</span>
            <button
              type="button"
              onClick={() => navigator.clipboard.writeText(code)}
              className="text-teal-700 hover:text-teal-900 dark:text-teal-400 dark:hover:text-teal-200"
            >
              복사
            </button>
          </div>
          <pre className="max-h-36 overflow-auto bg-slate-950 p-2 text-[10px] leading-4 text-slate-200 font-mono">
            <code>{code}</code>
          </pre>
        </div>
      );
    }
    return (
      <span key={index} className="whitespace-pre-wrap text-[11px] leading-relaxed text-slate-700 dark:text-slate-200 font-sans block">
        {part}
      </span>
    );
  });
}


export function AIAssistantPanel({
  view,
  open,
  onOpenChange,
}: {
  view: ViewKey;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [responses, setResponses] = useState<Array<{ question: string; response: AssistantChatResponse }>>([]);
  const [selection, setSelection] = useState<AssistantSelection | null>(null);
  const [appliedResponseIds, setAppliedResponseIds] = useState<string[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [responses]);

  useEffect(() => {
    function readSelection() {
      if (typeof window === "undefined") return;
      const raw = window.localStorage.getItem(ASSISTANT_SELECTION_KEY);
      setSelection(raw ? JSON.parse(raw) as AssistantSelection : null);
    }

    function handleSelection(event: Event) {
      const custom = event as CustomEvent<AssistantSelection>;
      setSelection(custom.detail ?? null);
    }

    readSelection();
    window.addEventListener("assistant-selection-change", handleSelection);
    window.addEventListener("storage", readSelection);
    return () => {
      window.removeEventListener("assistant-selection-change", handleSelection);
      window.removeEventListener("storage", readSelection);
    };
  }, []);

  const context = useMemo<AssistantContext>(() => {
    const tenant = getCurrentTenant();
    return {
      current_view: view,
      view_title: VIEW_LABELS[view] ?? view,
      company_id: tenant.companyId,
      project_id: tenant.projectId,
      user_id: tenant.userId,
      role: tenant.role,
      ...selection,
    };
  }, [view, selection]);

  function applyCodeToSelectedEditor(code: string) {
    if (!selection?.selected_app_id || !selection.selected_file_path || !code.trim()) return;
    window.dispatchEvent(new CustomEvent(ASSISTANT_APPLY_CODE_EVENT, {
      detail: {
        selected_app_id: selection.selected_app_id,
        selected_file_path: selection.selected_file_path,
        code,
      },
    }));
  }

  async function send(text = message) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.assistant.chat({ message: trimmed, context });
      const code = extractPythonCode(response.answer);
      if (code && selection?.selected_file_path) {
        applyCodeToSelectedEditor(code);
        setAppliedResponseIds((ids) => [...ids, response.conversation_id]);
      }
      setResponses((items) => [...items, { question: trimmed, response }]);
      setMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function copyText(text: string) {
    await navigator.clipboard.writeText(text);
  }

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={() => onOpenChange(true)}
          className="fixed bottom-5 right-5 z-40 inline-flex h-13 w-13 items-center justify-center rounded-full bg-teal-700 text-white shadow-lg shadow-teal-900/20 transition hover:bg-teal-800 focus:outline-none focus:ring-4 focus:ring-teal-200"
          aria-label="AI Assistant 열기"
          title="AI Assistant"
        >
          <Bot className="h-6 w-6" />
        </button>
      )}

      {open && (
        <aside className="flex h-full w-[460px] shrink-0 flex-col border-l border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-slate-950">
            <header className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-teal-700 text-white">
                      <Sparkles className="h-4 w-4" />
                    </span>
                    <div>
                      <h2 className="text-xs font-extrabold text-slate-950 dark:text-slate-100">AI Assistant</h2>
                      <p className="text-[10px] text-slate-500 dark:text-slate-400">
                        {context.view_title}
                        {selection?.selected_file_path && ` (파일: ${selection.selected_file_path})`}
                      </p>
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1 text-[9px] font-bold uppercase tracking-wide">
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-600 dark:bg-slate-900 dark:text-slate-300">{context.company_id}</span>
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-600 dark:bg-slate-900 dark:text-slate-300">{context.project_id}</span>
                    <span className="rounded bg-teal-50 px-1.5 py-0.5 text-teal-800 dark:bg-teal-950 dark:text-teal-100">{context.role}</span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => onOpenChange(false)}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
                  aria-label="AI Assistant 닫기"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </header>

            <main className="flex-1 space-y-3 overflow-y-auto px-4 py-3 bg-slate-50/50 dark:bg-slate-900/10">
              {responses.length === 0 && !error && (
                <div className="space-y-4">
                  <div className="rounded-xl border border-dashed border-slate-200 bg-white p-4 text-center dark:border-slate-850 dark:bg-slate-950 shadow-sm">
                    <MessageSquareText className="mx-auto h-7 w-7 text-teal-700 opacity-80" />
                    <p className="mt-2 text-xs font-bold text-slate-800 dark:text-slate-100">현재 화면 기준으로 바로 물어보세요</p>
                    <p className="mt-1 text-[11px] leading-4 text-slate-500 dark:text-slate-400">
                      온톨로지 질의, Streamlit 스타일 앱 초안, 워크플로우 설명, 장애 점검을 현재 화면 맥락으로 도와줍니다.
                    </p>
                  </div>
                  
                  {/* 퀵 프롬프트를 대화가 비어 있을 때만 컴팩트 카드로 노출 */}
                  <div className="space-y-1">
                    <div className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wide px-1">추천 질문</div>
                    <div className="grid gap-1.5 grid-cols-1">
                      {QUICK_PROMPTS.map((prompt) => (
                        <button
                          key={prompt}
                          type="button"
                          onClick={() => send(prompt)}
                          className="rounded border border-slate-200 bg-white px-2.5 py-1.5 text-left text-[10px] font-medium text-slate-600 transition hover:border-teal-200 hover:bg-teal-50 hover:text-teal-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300 dark:hover:bg-teal-950/30"
                        >
                          {prompt}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {responses.map(({ question, response }) => (
                <section key={response.conversation_id} className="space-y-2">
                  <div className="ml-auto max-w-[85%] rounded-lg rounded-tr-none bg-teal-700 px-2.5 py-1.5 text-[11px] font-medium text-white shadow-sm">
                    {question}
                  </div>
                  <div className="rounded-lg rounded-tl-none border border-slate-200 bg-white p-2.5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                    <div className="mb-2 flex items-center gap-1.5">
                      <span className="rounded bg-teal-50 px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wide text-teal-800 dark:bg-teal-950 dark:text-teal-100">
                        {intentLabel(response.intent)}
                      </span>
                      <span className="text-[11px] font-bold text-slate-400">{response.summary}</span>
                    </div>
                    
                    {selection?.selected_file_path && extractPythonCode(response.answer) && (
                      <div className="mb-2.5 rounded-lg border border-teal-200 bg-teal-50/50 p-2.5 dark:border-teal-900/30 dark:bg-teal-950/20">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="min-w-0 text-[11px] text-teal-900 dark:text-teal-100">
                            <span className="font-extrabold">적용 대상:</span>
                            <span className="ml-1 break-all font-semibold text-teal-750 dark:text-teal-350">{selection.selected_file_path}</span>
                            {appliedResponseIds.includes(response.conversation_id) && (
                              <span className="mt-0.5 flex items-center gap-1 font-bold text-emerald-600 dark:text-emerald-300">
                                <CheckCircle2 className="h-3 w-3" />
                                코드 자동 적용됨
                              </span>
                            )}
                          </div>
                          <button
                            type="button"
                            onClick={() => applyCodeToSelectedEditor(extractPythonCode(response.answer))}
                            className="inline-flex items-center gap-1 rounded bg-teal-700 px-2 py-1 text-[10px] font-bold text-white hover:bg-teal-800"
                          >
                            <Code2 className="h-3 w-3" />
                            코드창 적용
                          </button>
                        </div>
                      </div>
                    )}
                    <div className="space-y-1.5 break-words">
                      {renderAnswerText(response.answer)}
                    </div>

                    {response.generated_queries.map((query) => (
                      <div key={query.query_id} className="mt-3 overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
                        <div className="flex items-center justify-between gap-2 border-b border-slate-200 bg-slate-50 px-2.5 py-1.5 dark:border-slate-800 dark:bg-slate-950">
                          <div className="min-w-0">
                            <div className="flex items-center gap-1.5">
                              <Code2 className="h-3.5 w-3.5 text-teal-700" />
                              <p className="truncate text-[10px] font-extrabold text-slate-800 dark:text-slate-100">{query.title}</p>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => copyText(query.query)}
                            className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded border border-slate-200 bg-white text-slate-500 hover:text-teal-700 dark:border-slate-800 dark:bg-slate-900"
                            title="쿼리 복사"
                          >
                            <Clipboard className="h-3 w-3" />
                          </button>
                        </div>
                        <pre className="max-h-48 overflow-auto bg-slate-950 p-2.5 text-[10px] leading-4 text-slate-200 font-mono">
                          <code>{query.query}</code>
                        </pre>
                        {query.warnings.length > 0 && (
                          <div className="space-y-0.5 bg-amber-50 px-2.5 py-1.5 text-[10px] text-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
                            {query.warnings.map((warning) => <p key={warning}>- {warning}</p>)}
                          </div>
                        )}
                      </div>
                    ))}

                    {response.app_spec_preview && (
                      <div className="mt-3 rounded-lg border border-teal-200 bg-teal-50/30 p-2.5 dark:border-teal-900/30 dark:bg-teal-950/20">
                        <div className="flex items-center gap-1.5">
                          <Workflow className="h-3.5 w-3.5 text-teal-700 dark:text-teal-200" />
                          <p className="text-[11px] font-extrabold text-teal-900 dark:text-teal-100">{response.app_spec_preview.title}</p>
                        </div>
                        <p className="mt-0.5 text-[10px] leading-4 text-teal-800 dark:text-teal-250">{response.app_spec_preview.description}</p>
                        <div className="mt-2.5 grid gap-1.5 sm:grid-cols-2">
                          {response.app_spec_preview.layout.map((widget) => (
                            <div key={`${widget.type}-${widget.title}`} className="rounded border border-teal-100 bg-white px-2 py-1 dark:border-slate-800 dark:bg-slate-950">
                              <p className="text-[8px] font-extrabold uppercase tracking-wide text-teal-650 dark:text-teal-350">{widget.type}</p>
                              <p className="mt-0.5 text-[10px] font-bold text-slate-700 dark:text-slate-350">{widget.title}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {response.suggested_actions.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {response.suggested_actions.map((action) => (
                          <button
                            key={action.id}
                            type="button"
                            disabled={!action.enabled}
                            className="rounded border border-slate-200 px-2 py-1 text-[10px] font-bold text-slate-600 disabled:cursor-not-allowed disabled:opacity-50 hover:border-teal-250 hover:text-teal-800 dark:border-slate-800 dark:text-slate-350"
                            title={action.description}
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </section>
              ))}

              {error && (
                <div className="rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-2 text-xs text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-100">
                  {error}
                </div>
              )}
              
              {/* 대화 스크롤 엔드 트래커 */}
              <div ref={messagesEndRef} />
            </main>

            <footer className="border-t border-slate-200 p-3.5 dark:border-slate-800">
              {selection?.selected_file_path && (
                <div className="mb-2 rounded-lg border border-emerald-200 bg-emerald-50 px-2.5 py-1.5 text-[11px] text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950/20 dark:text-emerald-100">
                  <span className="font-extrabold text-emerald-800 dark:text-emerald-250">대상: </span>
                  <span className="break-all font-semibold">{selection.selected_folder_name} / {selection.selected_file_path}</span>
                </div>
              )}
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  send();
                }}
                className="flex items-end gap-2"
              >
                <div className="flex-1">
                  <textarea
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        if (message.trim()) send();
                      }
                    }}
                    rows={2}
                    placeholder={selection?.selected_file_path ? "의견 전송... (Enter 전송, Shift+Enter 줄바꿈)" : "질문 전송... (Enter 전송, Shift+Enter 줄바꿈)"}
                    className="min-h-11 w-full resize-none rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading || !message.trim()}
                  className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-teal-700 text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label="전송"
                >
                  {loading ? <Loader2 className="h-4.5 w-4.5 animate-spin" /> : <Send className="h-4 w-4" />}
                </button>
              </form>
            </footer>
        </aside>
      )}
    </>
  );
}
