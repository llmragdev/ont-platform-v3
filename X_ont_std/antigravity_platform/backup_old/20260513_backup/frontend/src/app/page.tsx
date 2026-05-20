"use client";

import DocumentManager from "@/components/DocumentManager";

export default function HomePage() {
  const [currentView, setCurrentView] = useState("graph");
  const [graphData, setGraphData] = useState<any>(null);
  const [selectedObject, setSelectedObject] = useState<any>(null);
  const [userRole, setUserRole] = useState("analyst");
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatQuestion, setChatQuestion] = useState("이 객체 승인 근거 분석해줘");

  useEffect(() => {
    refreshGraph();
  }, [userRole]);

  const refreshGraph = async () => {
    try {
      const res = await api.getGraph(userRole);
      setGraphData(res.data);
    } catch (err) {
      console.error("Failed to fetch graph", err);
    }
  };

  const handleNodeClick = async (node: any) => {
    try {
      const res = await api.getObject(node.id, userRole);
      setSelectedObject(res.data);
      setAiResponse(null);
      setEvidence([]);
    } catch (err) {
      console.error("Failed to fetch object", err);
    }
  };

  const handleAsk = async (question: string) => {
    setAiResponse("");
    setIsStreaming(true);
    setEvidence([]);

    try {
      if (selectedObject) {
        // 기존 객체 중심 스트리밍 질의 (기존 로직 유지)
        const url = api.getAskStream(question, selectedObject.object.id, userRole);
        const eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.token) setAiResponse((prev) => (prev || "") + data.token);
          if (data.event === "finished") {
            setEvidence(data.evidence || []);
            setIsStreaming(false);
            eventSource.close();
          }
        };
        eventSource.onerror = () => {
          setIsStreaming(false);
          eventSource.close();
        };
      } else {
        // 하이브리드 질의 (신규)
        const res = await api.askHybrid(question);
        setAiResponse(res.data.answer);
        setEvidence(res.data.vector_evidence || []);
        setIsStreaming(false);
      }
    } catch (err) {
      console.error("Ask failed", err);
      setAiResponse("질의 처리 중 오류가 발생했습니다.");
      setIsStreaming(false);
    }
  };

  const handleChatSubmit = () => {
    if (!chatQuestion.trim()) return;
    handleAsk(chatQuestion.trim());
    setChatOpen(false);
  };

  return (
    <div className="flex h-screen w-screen bg-[#f8fafc] text-slate-900 overflow-hidden font-sans">
      {/* Sidebar */}
      <Sidebar 
        currentRole={userRole} 
        onRoleChange={setUserRole} 
        currentView={currentView}
        onViewChange={setCurrentView}
      />

      {/* Center & Right Wrapper */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Main Workspace - Center */}
        <main className="flex-1 flex flex-col relative min-w-0">
          <header className="h-16 border-b border-slate-200/60 flex items-center justify-between px-8 bg-white/50 backdrop-blur-md z-20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-700 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-200">
                <Shield size={22} fill="white" fillOpacity={0.2} />
              </div>
              <div>
                <h1 className="font-bold text-xl tracking-tight leading-none">Antigravity <span className="text-indigo-600">Ontology</span></h1>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Enterprise Decision Support</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
               <div className="flex items-center gap-2 px-4 py-2 bg-indigo-50 rounded-full text-[11px] font-bold text-indigo-600 border border-indigo-100/50">
                 <Database size={14} /> Schema: Live Engine
               </div>
            </div>
          </header>

          <div className="flex-1 relative overflow-hidden">
            {currentView === "graph" ? (
              <GraphWorkspace data={graphData} onNodeClick={handleNodeClick} />
            ) : currentView === "documents" ? (
              <DocumentManager />
            ) : (
              <div className="flex items-center justify-center h-full text-slate-300 font-bold text-xl">
                Preparing View...
              </div>
            )}

            {/* Floating AI Chat Button */}
            <div className="fixed bottom-6 right-[430px] z-50 flex flex-col items-end gap-3">
              <AnimatePresence>
                {chatOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 12, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 12, scale: 0.96 }}
                    className="w-80 rounded-3xl border border-slate-200 bg-white shadow-2xl shadow-slate-300/60 overflow-hidden"
                  >
                    <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-indigo-50">
                      <div className="flex items-center gap-2 text-indigo-700">
                        <Sparkles size={16} />
                        <span className="text-xs font-black uppercase tracking-widest">Hybrid AI Chat</span>
                      </div>
                      <button
                        onClick={() => setChatOpen(false)}
                        className="p-1 rounded-full hover:bg-white text-slate-400"
                      >
                        <X size={16} />
                      </button>
                    </div>
                    <div className="p-4 space-y-3">
                      <div className="text-xs text-slate-500 leading-relaxed">
                        {selectedObject
                          ? `${selectedObject.object.id} (${selectedObject.object.type}) 기준으로 질의합니다.`
                          : "전체 지식 기반(RAG+온톨로지)으로 질의합니다."}
                      </div>
                      <textarea
                        value={chatQuestion}
                        onChange={(event) => setChatQuestion(event.target.value)}
                        className="w-full h-24 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 resize-none"
                        placeholder="예: 이 객체 승인 근거 분석해줘 또는 Snowflake의 과금 모델은?"
                      />
                      <button
                        onClick={handleChatSubmit}
                        disabled={!chatQuestion.trim()}
                        className="w-full px-4 py-3 rounded-2xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 transition-colors flex items-center justify-center gap-2"
                      >
                        <Send size={15} />
                        질문 보내기
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <button
                onClick={() => setChatOpen((value) => !value)}
                className="h-16 px-5 rounded-full bg-slate-950 text-white shadow-2xl shadow-slate-400/60 hover:bg-indigo-600 transition-all flex items-center gap-3 font-black"
              >
                <span className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                  <MessageCircle size={22} />
                </span>
                Hybrid Chat
              </button>
            </div>
            
            {/* AI Response Overlay */}
            <AnimatePresence>
              {aiResponse !== null && (
                <motion.div 
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 30 }}
                  className="absolute bottom-6 left-6 right-6 max-h-[45%] bg-white/80 backdrop-blur-2xl border border-white shadow-[0_20px_50px_rgba(0,0,0,0.1)] rounded-3xl z-30 overflow-hidden flex flex-col"
                >
                  <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-indigo-600/5">
                     <div className="flex items-center gap-2 text-indigo-600">
                       <Sparkles size={18} className="animate-pulse" />
                       <span className="text-sm font-bold font-outfit uppercase tracking-wider">AI Analytical Insight</span>
                     </div>
                     <button onClick={() => setAiResponse(null)} className="p-1.5 hover:bg-slate-200/50 rounded-full transition-colors text-slate-400">
                       <X size={18} />
                     </button>
                  </div>
                  <div className="p-6 overflow-y-auto scrollbar-hide">
                    <p className="text-slate-700 leading-relaxed font-medium whitespace-pre-wrap">
                      {aiResponse}
                      {isStreaming && <span className="inline-block w-1.5 h-4 bg-indigo-500 animate-pulse ml-1 align-middle" />}
                    </p>
                    
                    {evidence.length > 0 && (
                      <div className="mt-8 pt-6 border-t border-slate-100">
                        <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] mb-4">Verification Evidence</h4>
                        <div className="flex flex-wrap gap-3">
                          {evidence.map((ev) => (
                            <div key={ev.id} className="px-4 py-2 bg-white rounded-xl border border-slate-100 shadow-sm text-[11px] flex items-center gap-3 hover:border-indigo-200 transition-colors cursor-default">
                               <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full shadow-[0_0_8px_rgba(99,102,241,0.5)]" />
                               <span className="font-bold text-slate-600">{ev.title}</span>
                               <span className="text-[10px] text-indigo-400 font-bold px-1.5 py-0.5 bg-indigo-50 rounded">{(ev.score * 100).toFixed(0)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>

        {/* Context Panel - Right (폭 고정) */}
        <ContextPanel selectedObject={selectedObject} onAsk={handleAsk} />
      </div>
    </div>
  );
}
