"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Search, 
  Send, 
  Cpu, 
  MessageSquare, 
  Combine, 
  Loader2, 
  ChevronRight,
  Database,
  FileText
} from "lucide-react";

interface QueryConsoleProps {
  mode: 'rag' | 'ontology' | 'hybrid';
  title: string;
  description: string;
}

export default function QueryConsole({ mode, title, description }: QueryConsoleProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleQuery = async () => {
    if (!query) return;
    setLoading(true);
    setResult(null);

    try {
      // mode에 따라 다른 엔드포인트 호출 (여기서는 예시로 통합 질의 API 사용)
      const endpoint = mode === 'hybrid' ? "ask" : (mode === 'rag' ? "ask" : "ask");
      const response = await fetch(`http://localhost:8000/api/v1/hybrid/${endpoint}?question=${encodeURIComponent(query)}`, {
        method: "POST",
      });

      if (!response.ok) throw new Error("API call failed");
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getModeIcon = () => {
    switch (mode) {
      case 'rag': return <MessageSquare className="text-accent" />;
      case 'ontology': return <Cpu className="text-secondary" />;
      case 'hybrid': return <Combine className="text-primary" />;
    }
  };

  return (
    <div className="space-y-8">
      <header>
        <h1 className="mb-1 flex items-center gap-3">
          {getModeIcon()}
          {title}
        </h1>
        <p className="text-gray-400 text-sm">{description}</p>
      </header>

      <div className="glass-card p-2 flex items-center gap-2 pr-4 focus-within:border-primary/50 transition-all">
        <div className="p-3">
          <Search className="text-gray-500" size={20} />
        </div>
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          placeholder="질문을 입력하세요..." 
          className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-gray-600 py-4"
        />
        <button 
          onClick={handleQuery}
          disabled={loading || !query}
          className="bg-primary p-3 rounded-xl hover:bg-primary/80 transition-all disabled:opacity-50"
        >
          {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
        </button>
      </div>

      <AnimatePresence>
        {result && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Answer Card */}
            <div className="glass-card p-8 bg-gradient-to-br from-primary/5 to-transparent">
              <h3 className="text-lg font-semibold mb-4 text-primary">AI Answer</h3>
              <p className="text-lg leading-relaxed text-gray-200">
                {result.answer}
              </p>
            </div>

            {/* Evidence/Source Panel */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Ontology Results */}
              <div className="glass-card p-6">
                <h4 className="text-sm font-bold uppercase tracking-widest text-secondary mb-4 flex items-center gap-2">
                  <Database size={16} />
                  Ontology Entities
                </h4>
                <div className="space-y-3">
                  {result.sources?.filter((s:any) => s.type === 'ontology').map((source: any, i: number) => (
                    <div key={i} className="p-3 bg-white/5 border border-white/5 rounded-lg text-sm">
                      <span className="font-bold text-secondary mr-2">[{source.entity_type}]</span>
                      {source.name || source.id}
                    </div>
                  )) || <p className="text-xs text-gray-500">관련 엔티티 없음</p>}
                </div>
              </div>

              {/* RAG Results */}
              <div className="glass-card p-6">
                <h4 className="text-sm font-bold uppercase tracking-widest text-accent mb-4 flex items-center gap-2">
                  <FileText size={16} />
                  Document Sources
                </h4>
                <div className="space-y-3">
                  {result.sources?.filter((s:any) => s.type === 'document').map((source: any, i: number) => (
                    <div key={i} className="p-3 bg-white/5 border border-white/5 rounded-lg text-sm">
                      <p className="font-medium text-accent mb-1 line-clamp-1">{source.file_name}</p>
                      <p className="text-xs text-gray-400 line-clamp-2">{source.snippet}</p>
                    </div>
                  )) || <p className="text-xs text-gray-500">관련 문서 없음</p>}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
