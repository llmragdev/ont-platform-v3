"use client";

import React, { useEffect, useState } from "react";
import { Database, Plus, Save, RefreshCcw } from "lucide-react";

export default function OntologyPage() {
  const [schema, setSchema] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/ontology/schema")
      .then(res => res.json())
      .then(data => setSchema(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="p-8">
      <header className="flex justify-between items-center mb-10">
        <div>
          <h1 className="mb-1">온톨로지 설정</h1>
          <p className="text-gray-400 text-sm">엔터프라이즈 업무 객체와 관계 정의를 관리합니다.</p>
        </div>
        <div className="flex gap-3">
          <button className="glass-card px-4 py-2 flex items-center gap-2 hover:bg-white/5 transition-all">
            <RefreshCcw size={16} />
            새로고침
          </button>
          <button className="bg-primary px-4 py-2 rounded-xl flex items-center gap-2 font-bold shadow-[0_0_15px_rgba(59,130,246,0.3)]">
            <Plus size={16} />
            객체 추가
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <Database className="text-primary" size={18} />
            Object Types
          </h3>
          <div className="space-y-4">
            {schema?.object_types?.map((obj: any) => (
              <div key={obj.name} className="p-4 bg-white/5 border border-white/10 rounded-xl hover:border-primary/30 transition-all cursor-pointer">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold text-white">{obj.name}</span>
                  <span className="text-[10px] bg-primary/20 text-primary px-2 py-1 rounded-full uppercase">Type</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {obj.properties.map((prop: any) => (
                    <span key={prop.name} className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded">
                      {prop.name}: {prop.type}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <RefreshCcw className="text-secondary" size={18} />
            Relationship Types
          </h3>
          <div className="space-y-4">
            {schema?.relationship_types?.map((rel: any) => (
              <div key={rel.name} className="p-4 bg-white/5 border border-white/10 rounded-xl">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-bold text-white">{rel.name}</span>
                  <span className="text-[10px] bg-secondary/20 text-secondary px-2 py-1 rounded-full uppercase">Link</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <div className="px-3 py-1 bg-white/5 rounded-lg border border-white/10">{rel.source_type}</div>
                  <ChevronRight size={14} className="text-gray-600" />
                  <div className="px-3 py-1 bg-white/5 rounded-lg border border-white/10">{rel.target_type}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ChevronRight(props: any) {
  return (
    <svg 
      {...props} 
      xmlns="http://www.w3.org/2000/svg" 
      width="24" 
      height="24" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}
