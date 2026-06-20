'use client';

// Author: Claude
// Date: 2026-06-20
// Purpose: 하이브리드 질의 히스토리 관리 및 재실행

import React from 'react';
import { useQueryStore, QueryMessage } from '@/store/useQueryStore';

export const HybridQueryHistory = () => {
  const previousQueries = useQueryStore(state => state.previousQueries);
  const currentQuery = useQueryStore(state => state.currentQuery);
  const clearHistory = useQueryStore(state => state.clearHistory);

  const handleQueryClick = (query: QueryMessage) => {
    // 히스토리의 질의를 선택하면, 입력창에 채워지고 자동 실행
    const event = new CustomEvent('loadHistory', { detail: query });
    window.dispatchEvent(event);
  };

  if (!previousQueries || previousQueries.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-sm text-gray-400 text-center">
          아직 실행한 질의가 없습니다.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-3 p-4 border rounded-lg bg-white shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-800">📜 질의 히스토리</h3>
        <button
          onClick={clearHistory}
          className="text-xs text-gray-400 hover:text-gray-600 underline"
        >
          전체 삭제
        </button>
      </div>

      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {previousQueries.map((query, idx) => {
          const levelColor = {
            1: 'bg-red-50 border-red-200',
            2: 'bg-yellow-50 border-yellow-200',
            3: 'bg-green-50 border-green-200',
            4: 'bg-blue-50 border-blue-200',
          }[query.coverage_level as keyof typeof levelColor] || 'bg-gray-50 border-gray-200';

          const levelBadge = {
            1: '❌',
            2: '⚠️',
            3: '✅',
            4: '🎯',
          }[query.coverage_level as keyof typeof levelBadge] || '❓';

          const isActive = currentQuery?.question === query.question && currentQuery?.coverage_level === query.coverage_level;

          return (
            <button
              key={idx}
              onClick={() => handleQueryClick(query)}
              className={`w-full text-left p-3 border rounded-lg transition-all hover:shadow-md ${
                isActive
                  ? `${levelColor} ring-2 ring-offset-1`
                  : `${levelColor} hover:shadow-sm`
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{levelBadge}</span>
                  <span className="text-xs font-semibold text-gray-600">
                    Level {query.coverage_level}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  신뢰도 {(query.confidence_score * 100).toFixed(0)}%
                </span>
              </div>

              <p className="text-sm font-medium text-gray-800 line-clamp-2 mb-1">
                {query.question}
              </p>

              <div className="text-xs text-gray-600 line-clamp-1">
                {query.answer || '(답변 없음)'}
              </div>

              {/* 소스 요약 */}
              <div className="flex gap-2 mt-2 text-xs text-gray-600">
                {query.sources?.rag?.length > 0 && (
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                    RAG {query.sources.rag.length}
                  </span>
                )}
                {query.sources?.ontology?.length > 0 && (
                  <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                    Ontology {query.sources.ontology.length}
                  </span>
                )}
                {query.sources?.expert_opinions?.length > 0 && (
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">
                    Expert {query.sources.expert_opinions.length}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* 통계 */}
      <div className="pt-3 border-t border-gray-200">
        <div className="grid grid-cols-4 gap-2 text-xs">
          <div className="text-center">
            <p className="text-gray-500">전체</p>
            <p className="font-bold text-gray-800">{previousQueries.length}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-500">Level 4</p>
            <p className="font-bold text-blue-600">
              {previousQueries.filter(q => q.coverage_level === 4).length}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500">평균 신뢰도</p>
            <p className="font-bold text-gray-800">
              {(
                previousQueries.reduce((sum, q) => sum + q.confidence_score, 0) /
                previousQueries.length *
                100
              ).toFixed(0)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500">한계점</p>
            <p className="font-bold text-yellow-600">
              {previousQueries.filter(q => q.limitations?.length > 0).length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
