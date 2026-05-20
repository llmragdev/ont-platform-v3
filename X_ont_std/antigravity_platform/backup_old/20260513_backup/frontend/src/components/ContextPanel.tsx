"use client";

import React, { useState } from "react";
import { Info, MessageSquare, ChevronRight, FileText, Share2, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function ContextPanel({ selectedObject, onAsk }: { selectedObject: any, onAsk: (q: string) => void }) {
  const [question, setQuestion] = useState("");

  if (!selectedObject) {
    return (
      <aside className="w-[400px] border-l border-slate-200 bg-white/80 backdrop-blur-md p-10 flex flex-col items-center justify-center text-center">
        <div className="w-20 h-20 bg-slate-50 rounded-[30%] flex items-center justify-center text-slate-200 mb-6 border border-slate-100 rotate-12">
          <Info size={40} />
        </div>
        <h3 className="text-slate-800 font-bold text-lg font-outfit">Object Explorer</h3>
        <p className="text-slate-400 text-sm mt-3 leading-relaxed">
          그래프에서 노드를 선택하여<br/>
          상세 속성 및 AI 컨텍스트를 확인하세요.
        </p>
      </aside>
    );
  }

  const { object, related_objects } = selectedObject;

  return (
    <aside className="w-[400px] border-l border-slate-200 bg-white flex flex-col overflow-hidden z-20 shadow-[-10px_0_30px_rgba(0,0,0,0.02)]">
      {/* Header */}
      <div className="p-8 border-b border-slate-100 bg-slate-50/30">
        <div className="flex items-center gap-2 text-indigo-600 mb-2">
          <Sparkles size={14} fill="currentColor" fillOpacity={0.2} />
          <span className="text-[10px] font-black uppercase tracking-[0.2em]">{object.type}</span>
        </div>
        <h2 className="text-2xl font-bold text-slate-900 font-outfit tracking-tight">{object.values.name || object.id}</h2>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8 space-y-10 scrollbar-hide">
        
        {/* Properties Section */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.15em] flex items-center gap-2">
              <FileText size={14} className="text-indigo-400" /> Attributes
            </h3>
            <span className="px-2 py-0.5 bg-slate-100 rounded text-[9px] font-bold text-slate-500 uppercase">Static</span>
          </div>
          <div className="grid grid-cols-1 gap-3">
            {Object.entries(object.values).map(([key, value]: [string, any]) => (
              <div key={key} className="p-4 rounded-2xl bg-slate-50/50 border border-slate-100/50 hover:bg-white hover:shadow-md hover:border-indigo-100 transition-all duration-300 group">
                <div className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mb-1 group-hover:text-indigo-400 transition-colors">{key}</div>
                <div className="text-sm text-slate-800 font-semibold break-words">
                  {typeof value === 'string' && value.includes('Restricted') ? (
                    <span className="px-2 py-0.5 bg-rose-50 text-rose-500 rounded text-[10px] border border-rose-100">Hidden</span>
                  ) : String(value)}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Relations Section */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.15em] flex items-center gap-2">
              <Share2 size={14} className="text-violet-400" /> Linked Entities
            </h3>
          </div>
          <div className="space-y-3">
            {related_objects.length > 0 ? related_objects.map((rel: any) => (
              <motion.div 
                whileHover={{ x: 5 }}
                key={rel.id} 
                className="p-4 rounded-2xl border border-slate-100 flex items-center justify-between group cursor-pointer hover:bg-indigo-50/30 hover:border-indigo-100 transition-all"
              >
                <div>
                  <div className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mb-0.5">{rel.type}</div>
                  <div className="text-sm text-slate-800 font-bold">{rel.values.name || rel.id}</div>
                </div>
                <div className="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center text-slate-300 group-hover:bg-white group-hover:text-indigo-500 transition-all shadow-sm">
                  <ChevronRight size={16} />
                </div>
              </motion.div>
            )) : (
              <div className="text-center py-6 border-2 border-dashed border-slate-100 rounded-2xl">
                <p className="text-[11px] text-slate-300 font-bold uppercase">No active links</p>
              </div>
            )}
          </div>
        </section>
      </div>

      {/* AI Analyst Input Section - Sticky at Bottom */}
      <div className="p-8 border-t border-slate-100 bg-white">
        <div className="mb-4 flex items-center gap-2">
          <MessageSquare size={14} className="text-indigo-500" />
          <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">AI Analytical Query</span>
        </div>
        <div className="relative group">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="이 객체의 승인 근거를 분석해줘..."
            className="w-full h-28 p-4 text-sm rounded-2xl border border-slate-200 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none resize-none bg-slate-50/30 group-hover:bg-white transition-all duration-300 shadow-inner"
          />
          <button
            onClick={() => { if(question.trim()) { onAsk(question); setQuestion(""); } }}
            disabled={!question.trim()}
            className="absolute bottom-3 right-3 px-5 py-2.5 bg-slate-900 hover:bg-indigo-600 disabled:bg-slate-200 text-white rounded-xl text-xs font-bold transition-all shadow-xl shadow-slate-200 flex items-center gap-2 active:scale-95"
          >
            <Sparkles size={14} /> Analyze
          </button>
        </div>
      </div>
    </aside>
  );
}
