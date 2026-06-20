'use client';

// Author: Claude
// Date: 2026-06-20
// Purpose: Level별 동적 답변 렌더링 (보완책 #1, #2 구현)

import React from 'react';
import { useQueryStore, QueryMessage } from '@/store/useQueryStore';
import { SourcePanel } from './SourcePanel';

export const AnswerDisplay = () => {
  const currentQuery = useQueryStore(state => state.currentQuery);
  const mode = useQueryStore(state => state.mode);

  if (!currentQuery) {
    return (
      <div className="p-8 text-center text-gray-400">
        <p>질의를 입력하면 답변이 여기 표시됩니다.</p>
      </div>
    );
  }

  const level = currentQuery.coverage_level || 1;
  const confidence = currentQuery.confidence_score || 0;
  const isStreaming = currentQuery.isStreaming;

  // Level별 색상 및 배지
  const levelConfig = {
    1: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      badge: '❌ 관련정보 없음',
      badgeBg: 'bg-red-100 text-red-700',
    },
    2: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      badge: '⚠️ 부분설명',
      badgeBg: 'bg-yellow-100 text-yellow-700',
    },
    3: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      badge: '✅ 정상설명',
      badgeBg: 'bg-green-100 text-green-700',
    },
    4: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      badge: '🎯 지식통합',
      badgeBg: 'bg-blue-100 text-blue-700',
    },
  };

  const config = levelConfig[level as keyof typeof levelConfig] || levelConfig[1];

  return (
    <div className="w-full space-y-4">
      {/* Level 1: 붉은 경고 (특별 UI) */}
      {level === 1 && (
        <div className={`p-6 rounded-lg border-2 ${config.bg} ${config.border}`}>
          <div className="flex items-center gap-4">
            <div className="text-5xl">❌</div>
            <div>
              <h3 className="text-2xl font-bold text-red-700">관련 정보를 찾을 수 없습니다</h3>
              <p className="text-red-600 mt-2">
                죄송합니다. 현재 문서에서 '{currentQuery.question}'에 대한 관련 정보를 찾을 수 없습니다.
              </p>
              <p className="text-red-500 text-sm mt-3">
                💡 팁: 다른 방식으로 질문해보세요. 예: "이것은 어떻게 하나요?" → "절차는?"
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Level 2-4: 일반 답변 UI */}
      {level >= 2 && (
        <div className={`rounded-lg border-2 border-l-4 ${config.bg} ${config.border} p-6`}>
          {/* 배지 + 신뢰도 */}
          <div className="flex items-center justify-between mb-4">
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${config.badgeBg}`}>
              {config.badge}
            </span>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                신뢰도: <span className="font-bold text-gray-800">{(confidence * 100).toFixed(0)}%</span>
              </span>
              {/* 신뢰도 바 */}
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    level === 1 ? 'bg-red-500' :
                    level === 2 ? 'bg-yellow-500' :
                    level === 3 ? 'bg-green-500' :
                    'bg-blue-500'
                  }`}
                  style={{ width: `${confidence * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* 스트리밍 인디케이터 */}
          {isStreaming && (
            <div className="mb-4 flex items-center gap-2 text-sm text-gray-600 animate-pulse">
              <span>⌨️</span>
              <span>답변을 생성하고 있습니다...</span>
              <span>...</span>
            </div>
          )}

          {/* 메인 답변 텍스트 */}
          <div className="prose prose-sm max-w-none text-gray-800 mb-6">
            <p className="whitespace-pre-wrap leading-relaxed">
              {currentQuery.answer}
            </p>
          </div>

          {/* Level 2: 한계점 섹션 */}
          {level === 2 && currentQuery.limitations && currentQuery.limitations.length > 0 && (
            <div className="mt-6 pt-6 border-t-2 border-yellow-200">
              <h4 className="font-bold text-yellow-700 mb-3 flex items-center gap-2">
                <span>📝</span>
                <span>한계점 및 누락된 정보</span>
              </h4>
              <ul className="space-y-2">
                {currentQuery.limitations.map((limitation, idx) => (
                  <li key={idx} className="text-sm text-yellow-600 flex gap-2">
                    <span>•</span>
                    <span>{limitation}</span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-yellow-500 mt-4 italic">
                위의 정보는 업로드된 문서에 기반합니다. 더 자세한 정보가 필요하면 추가 문서를 업로드해주세요.
              </p>
            </div>
          )}

          {/* Level 4: 전문가 의견 아코디언 */}
          {level === 4 && (
            <details className="mt-6 pt-6 border-t-2 border-blue-200 group">
              <summary className="cursor-pointer font-semibold text-blue-700 flex items-center gap-2 select-none">
                <span className="text-lg">👨‍💼</span>
                <span>전문가 의견 (사내 Expert DB 기반)</span>
                <span className="ml-auto text-gray-400 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="mt-4 pl-4 border-l-2 border-blue-200 space-y-3">
                <p className="text-sm text-gray-700">
                  {currentQuery.answer}와 함께 다음의 전문가 의견을 참고하세요:
                </p>

                {/* Expert Opinions 렌더링 */}
                {currentQuery.sources?.expert_opinions &&
                 currentQuery.sources.expert_opinions.length > 0 ? (
                  currentQuery.sources.expert_opinions.map((exp: any, idx: number) => (
                    <div key={idx} className="p-3 rounded bg-blue-100 border-l-4 border-blue-500">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-blue-700">
                          {exp.expert_name || '전문가'}
                        </span>
                        <span className="text-xs bg-blue-200 text-blue-700 px-2 py-0.5 rounded">
                          검증됨
                        </span>
                      </div>
                      <p className="text-sm text-gray-800 italic">
                        "{exp.opinion}"
                      </p>
                      {exp.confidence && (
                        <p className="text-xs text-gray-600 mt-1">
                          신뢰도: {(exp.confidence * 100).toFixed(0)}%
                        </p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-600 italic">
                    등록된 전문가 의견이 없습니다.
                  </p>
                )}
              </div>
            </details>
          )}

          {/* Follow-up Suggestions */}
          {!isStreaming && currentQuery.follow_up_suggestions &&
           currentQuery.follow_up_suggestions.length > 0 && (
            <div className="mt-6 pt-6 border-t-2 border-gray-200">
              <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <span>💡</span>
                <span>다음으로 물어볼 수 있는 질문</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {currentQuery.follow_up_suggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    className="p-3 text-left text-sm bg-gray-100 hover:bg-gray-200 rounded border border-gray-300 transition-colors"
                  >
                    <p className="font-semibold text-gray-700">{suggestion.question}</p>
                    {suggestion.reason && (
                      <p className="text-xs text-gray-600 mt-1">{suggestion.reason}</p>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 출처 패널 (모든 level에서 표시) - Level 1도 포함 */}
      {currentQuery.sources && (
        <div className={`mt-8 ${level === 1 ? 'border-t-2 border-red-200 pt-6' : ''}`}>
          <SourcePanel sources={currentQuery.sources} level={level} />
        </div>
      )}
    </div>
  );
};
