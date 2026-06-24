'use client';

// Author: Claude / Restored by Antigravity
// Date: 2026-06-20
// Purpose: Week 4 - Mock API → Real API 전환 (Restored by Antigravity)

import React, { useState } from 'react';
import { useQueryStore, AnswerMode } from '@/store/useQueryStore';
import { api } from '@/lib/api';

export const AdaptiveQueryInterface = () => {
  const [queryText, setQueryText] = useState('');
  const [selectedMode, setSelectedMode] = useState<AnswerMode>('expert_mode');

  const [hideIrrelevant, setHideIrrelevant] = useState(true);
  const [allowPartial, setAllowPartial] = useState(true);
  const [separateGeneral, setSeparateGeneral] = useState(true);
  const [allowGeneral, setAllowGeneral] = useState(true);

  React.useEffect(() => {
    if (selectedMode === 'document_only') {
      setHideIrrelevant(true);
      setAllowPartial(false);
      setSeparateGeneral(true);
      setAllowGeneral(false);
    } else if (selectedMode === 'document_with_limits') {
      setHideIrrelevant(true);
      setAllowPartial(true);
      setSeparateGeneral(true);
      setAllowGeneral(false);
    } else if (selectedMode === 'expert_mode') {
      setHideIrrelevant(true);
      setAllowPartial(true);
      setSeparateGeneral(true);
      setAllowGeneral(true);
    }
  }, [selectedMode]);

  const startQuery = useQueryStore(state => state.startQuery);
  const updateStreamChunk = useQueryStore(state => state.updateStreamChunk);
  const finishQuery = useQueryStore(state => state.finishQuery);
  const currentQuery = useQueryStore(state => state.currentQuery);
  const currentProjectId = useQueryStore(state => state.currentProjectId);
  const isLoading = useQueryStore(state => state.isLoading);

  const handleSubmit = async () => {
    if (!queryText.trim() || isLoading) return;

    startQuery(queryText);

    try {
      // Week 4: 실제 Backend API와 연결
      // 프로젝트 ID는 window 전역 변수에서 가져옴 (QueryTab에서 설정함)
      const projectId = currentProjectId || (typeof window !== 'undefined' && (window as any).__projectId) || 'proj-deafe1fe';
      const sessionId = `session-${Date.now()}`;

      // SSE 스트림 실행
      api.queryStream(
        projectId,
        sessionId,
        queryText,
        selectedMode as 'document_only' | 'document_with_limits' | 'expert_mode',
        {
          hide_irrelevant: hideIrrelevant,
          allow_partial: allowPartial,
          separate_sources: separateGeneral,
          allow_general: allowGeneral,
          onSources: (sources) => {
            console.log('📊 Sources:', sources);
            useQueryStore.getState().updateSources(sources);
          },
          onToken: (token) => {
            console.log('📝 Token:', token);
            updateStreamChunk(token);
          },
          onLimitations: (limitations) => {
            console.log('⚠️ Limitations:', limitations);
            useQueryStore.getState().updateLimitations(limitations);
          },
          onFollowUps: (suggestions) => {
            console.log('💡 Follow-ups:', suggestions);
            useQueryStore.getState().updateFollowUps(suggestions);
          },
          onComplete: (meta) => {
            console.log('✅ Complete:', meta);
            finishQuery({
              coverage_level: meta.level ?? meta.relevance_level ?? 1,
              confidence_score: meta.confidence ?? meta.confidence_score ?? 0,
              v5_3: meta.v5_3,
              sources: meta.sources || useQueryStore.getState().currentQuery?.sources || { rag: [], ontology: [], expert_opinions: [] },
              limitations: meta.limitations || [],
              follow_up_suggestions: meta.follow_up_suggestions || []
            });
          },
          onError: (error) => {
            console.error('❌ Error:', error);
            useQueryStore.getState().setError(error);
          }
        }
      );

    } catch (error) {
      console.error("Query submission error:", error);
      useQueryStore.getState().setError(error instanceof Error ? error : new Error('알 수 없는 오류'));
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 border rounded shadow-sm bg-white">
      <div className="flex flex-col gap-2">
        <label className="font-semibold">질의를 입력하세요</label>
        <textarea
          className="p-2 border rounded resize-none"
          rows={3}
          value={queryText}
          onChange={e => setQueryText(e.target.value)}
          placeholder="데이터 손실 발생 시 어떻게 조치해야 하나요?"
        />
      </div>

      <div className="flex items-center gap-4">
        <select
          className="p-2 border rounded bg-gray-50"
          value={selectedMode}
          onChange={e => setSelectedMode(e.target.value as AnswerMode)}
        >
          <option value="document_only">📄 문서만 (보수적)</option>
          <option value="document_with_limits">⚠️ 한계점포함 (균형)</option>
          <option value="expert_mode">🎯 전문가모드 (지식통합)</option>
        </select>

        <button
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
          onClick={handleSubmit}
          disabled={isLoading || !queryText.trim()}
        >
          {isLoading ? '답변 생성 중...' : '질의 실행'}
        </button>
      </div>

      <div className="flex flex-col gap-2 p-3 bg-gray-50 border rounded text-sm">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={hideIrrelevant} onChange={e => setHideIrrelevant(e.target.checked)} />
          무관한 검색 결과 숨기기
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={allowPartial} onChange={e => setAllowPartial(e.target.checked)} />
          부분 답변 허용
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={separateGeneral} onChange={e => setSeparateGeneral(e.target.checked)} />
          출처 없는 일반 설명 분리
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={allowGeneral} onChange={e => setAllowGeneral(e.target.checked)} />
          문서 근거 없는 일반 설명 허용
        </label>
      </div>

      {currentQuery && (
        <div className="mt-4 p-4 bg-gray-100 rounded">
          <h3 className="font-bold mb-2">답변:</h3>
          <p className="whitespace-pre-wrap">{currentQuery.answer}</p>

          {!currentQuery.isStreaming && (
            <div className="mt-4 text-sm text-gray-600">
              <p>신뢰도: {(currentQuery.confidence_score * 100).toFixed(0)}%</p>
              <p>레벨: {currentQuery.coverage_level}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
