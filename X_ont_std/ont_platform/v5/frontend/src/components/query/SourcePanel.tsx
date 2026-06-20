'use client';

import React, { useState } from 'react';

// 간단한 Mock UI 컴포넌트들을 사용하여 SourcePanel 구성
export const SourcePanel = ({ sources, level }: { sources: any; level?: number }) => {
  const [activeTab, setActiveTab] = useState<'rag' | 'ontology' | 'expert'>('rag');

  if (!sources || Object.keys(sources).length === 0) return null;

  const ragCount = sources.rag?.length || 0;
  const ontologyCount = sources.ontology?.length || 0;
  const expertCount = sources.expert_opinions?.length || 0;

  return (
    <div className="w-full mt-6 border rounded-lg overflow-hidden bg-white shadow-sm">
      <div className="flex border-b bg-gray-50">
        <button
          className={`flex-1 py-3 font-semibold transition-colors ${activeTab === 'rag' ? 'bg-white border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:bg-gray-100'}`}
          onClick={() => setActiveTab('rag')}
        >
          📄 RAG ({ragCount})
        </button>
        <button
          className={`flex-1 py-3 font-semibold transition-colors ${activeTab === 'ontology' ? 'bg-white border-b-2 border-purple-500 text-purple-600' : 'text-gray-500 hover:bg-gray-100'}`}
          onClick={() => setActiveTab('ontology')}
        >
          🧠 Ontology ({ontologyCount})
        </button>
        <button
          className={`flex-1 py-3 font-semibold transition-colors ${activeTab === 'expert' ? 'bg-white border-b-2 border-green-500 text-green-600' : 'text-gray-500 hover:bg-gray-100'}`}
          onClick={() => setActiveTab('expert')}
        >
          👨‍💼 Expert ({expertCount})
        </button>
      </div>

      <div className="p-4 min-h-[200px]">
        {/* RAG 탭 */}
        {activeTab === 'rag' && (
          <div className="space-y-4">
            {sources.rag?.length > 0 ? sources.rag.map((item: any, idx: number) => {
              const score = item.rerank_score ?? item.relevance_score ?? item.score;
              const scorePercent = typeof score === 'number' ? Math.round(score * 100) : null;
              return (
              <div key={idx} className="p-3 border rounded bg-gray-50 hover:shadow-sm transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-bold text-blue-700">#{idx + 1} {item.filename || '문서'} (p.{item.page || '-'})</h4>
                  <span className="px-2 py-1 text-xs font-bold text-white bg-blue-500 rounded-full">
                    Score: {scorePercent !== null ? `${scorePercent}%` : '-'}
                  </span>
                </div>
                <p className="text-sm text-gray-700 line-clamp-3">{item.content || item.excerpt || item.text || '내용 없음'}</p>
                <button
                  onClick={() => {
                    // PDF 뷰어 팝업 트리거 (부모에서 처리)
                    const event = new CustomEvent('openPDF', {
                      detail: {
                        filename: item.filename || 'document.pdf',
                        page: item.page || 1
                      }
                    });
                    window.dispatchEvent(event);
                  }}
                  className="mt-2 text-xs text-blue-500 hover:underline"
                >
                  📑 PDF 보기
                </button>
              </div>
            )}) : <p className="text-gray-400 text-center py-8">RAG 검색 결과가 없습니다.</p>}
          </div>
        )}

        {/* Ontology 탭 */}
        {activeTab === 'ontology' && (
          <div className="space-y-4">
            <div className="p-4 bg-purple-50 border border-purple-100 rounded text-center text-sm text-purple-600 mb-4">
              [Ontology Graph Visualization Area] (vis-network 연결 예정)
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sources.ontology?.length > 0 ? sources.ontology.map((entity: any, idx: number) => (
                <div key={idx} className="p-3 border border-purple-200 rounded bg-white">
                  <h4 className="font-bold text-purple-700 mb-1">{entity.entity_name || entity.name || '엔티티'}</h4>
                  <p className="text-sm text-gray-600">{entity.description || `${entity.relation} -> ${entity.target}`}</p>
                </div>
              )) : <p className="text-gray-400 text-center py-8 col-span-full">Ontology 검색 결과가 없습니다.</p>}
            </div>
          </div>
        )}

        {/* Expert 탭 */}
        {activeTab === 'expert' && (
          <div className="space-y-4">
            {sources.expert_opinions?.length > 0 ? sources.expert_opinions.map((exp: any, idx: number) => (
              <div key={idx} className="p-4 border-l-4 border-green-500 bg-green-50 rounded-r">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">👨‍💼</span>
                  <h4 className="font-bold text-green-800">{exp.expert_name || '전문가'}</h4>
                  <span className="text-xs text-green-600 font-semibold bg-green-100 px-2 py-0.5 rounded">Verified</span>
                </div>
                <p className="text-sm text-gray-800 italic">"{exp.opinion}"</p>
              </div>
            )) : (
              <div className="text-center py-8">
                <p className="text-gray-400">관련된 전문가 의견(Expert DB)이 없습니다.</p>
                <p className="text-xs text-gray-300 mt-1">Level 4 지식통합 단계에서만 참조됩니다.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
