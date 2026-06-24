'use client';

import React, { useState } from 'react';
import type { OntologyGraphResponse } from '@/types/api';
import { OntologyGraphRenderer } from './ontology/OntologyGraphRenderer';

// Status 타입 정의
type ResultStatus = 'USED' | 'FILTERED' | 'FILTERED_THRESHOLD' | 'FILTERED_REQUIRED_TERMS';

interface Source {
  filename?: string;
  page?: number;
  score?: number;
  text?: string;
  content?: string;
  excerpt?: string;
  _status?: ResultStatus;
  _reason?: string;
  [key: string]: any;
}

interface OntologySource {
  entity_name?: string;
  name?: string;
  description?: string;
  relation?: string;
  target?: string;
  _status?: ResultStatus;
  _reason?: string;
  [key: string]: any;
}

// Status에 따른 스타일 및 아이콘 반환
const getStatusStyle = (status?: ResultStatus) => {
  switch (status) {
    case 'USED':
      return {
        container: 'border-l-4 border-green-500 bg-green-50',
        badge: 'bg-green-100 text-green-800',
        icon: '✓',
      };
    case 'FILTERED_THRESHOLD':
      return {
        container: 'border-l-4 border-gray-400 bg-gray-50',
        badge: 'bg-gray-100 text-gray-600',
        icon: '✗',
      };
    case 'FILTERED':
      return {
        container: 'border-l-4 border-red-400 bg-red-50',
        badge: 'bg-red-100 text-red-700',
        icon: '⛔',
      };
    case 'FILTERED_REQUIRED_TERMS':
      return {
        container: 'border-l-4 border-yellow-400 bg-yellow-50',
        badge: 'bg-yellow-100 text-yellow-700',
        icon: '⚠',
      };
    default:
      return {
        container: 'border-l-4 border-blue-400 bg-blue-50',
        badge: 'bg-blue-100 text-blue-700',
        icon: 'ℹ',
      };
  }
};

const getStatusLabel = (status?: ResultStatus) => {
  switch (status) {
    case 'USED':
      return '사용됨';
    case 'FILTERED_THRESHOLD':
      return '필터됨 (유사도)';
    case 'FILTERED':
      return '필터됨 (답변 차단)';
    case 'FILTERED_REQUIRED_TERMS':
      return '필터됨 (키워드)';
    default:
      return '확인';
  }
};

// 간단한 Mock UI 컴포넌트들을 사용하여 SourcePanel 구성
export const SourcePanel = ({ sources, level }: { sources: any; level?: number }) => {
  const [activeTab, setActiveTab] = useState<'rag' | 'ontology' | 'expert'>('rag');

  if (!sources || Object.keys(sources).length === 0) return null;

  const ontologyGraphResponse: OntologyGraphResponse | undefined =
    sources.ontology_graph_response ||
    (sources.ontology_graph
      ? {
          ontology_contract_version: sources.ontology_contract_version || 'v2',
          ontology_graph: sources.ontology_graph,
          ontology: sources.ontology,
        }
      : undefined);

  const ragResults = (sources.rag || []) as Source[];
  const ontologyResults = (sources.ontology || []) as OntologySource[];

  const ragCount = ragResults.length;
  const ragUsedCount = ragResults.filter((r) => r._status === 'USED' && r.used !== false).length;
  const ragFilteredCount = ragCount - ragUsedCount;

  const ontologyCount = ontologyResults.length;
  const ontologyUsedCount = ontologyResults.filter((r) => r._status === 'USED' && r.used !== false).length;
  const ontologyFilteredCount = ontologyCount - ontologyUsedCount;

  const expertCount = sources.expert_opinions?.length || 0;

  return (
    <div className="w-full mt-6 border rounded-lg overflow-hidden bg-white shadow-sm">
      <div className="flex border-b bg-gray-50">
        <button
          className={`flex-1 py-3 font-semibold transition-colors ${activeTab === 'rag' ? 'bg-white border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:bg-gray-100'}`}
          onClick={() => setActiveTab('rag')}
        >
          📄 RAG ({ragCount}) {ragUsedCount > 0 && <span className="text-xs text-green-600 ml-1">✓{ragUsedCount}</span>}
        </button>
        <button
          className={`flex-1 py-3 font-semibold transition-colors ${activeTab === 'ontology' ? 'bg-white border-b-2 border-purple-500 text-purple-600' : 'text-gray-500 hover:bg-gray-100'}`}
          onClick={() => setActiveTab('ontology')}
        >
          🧠 Ontology ({ontologyCount}) {ontologyUsedCount > 0 && <span className="text-xs text-green-600 ml-1">✓{ontologyUsedCount}</span>}
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
            {ragCount > 0 ? (
              <>
                {/* 요약 정보 */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <h5 className="font-bold text-blue-900 mb-2">📊 검색 결과 분석</h5>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-blue-600 font-bold">{ragCount}</span>
                      <span className="text-gray-600">개 검색됨</span>
                    </div>
                    <div>
                      <span className="text-green-600 font-bold">✓ {ragUsedCount}</span>
                      <span className="text-gray-600">개 사용됨</span>
                    </div>
                    <div>
                      <span className="text-gray-600 font-bold">✗ {ragFilteredCount}</span>
                      <span className="text-gray-600">개 필터됨</span>
                    </div>
                  </div>
                </div>

                {/* 사용된 문서 */}
                {ragUsedCount > 0 && (
                  <div>
                    <h5 className="font-bold text-green-700 mb-2">✓ 사용된 문서 ({ragUsedCount})</h5>
                    <div className="space-y-3">
                      {ragResults
                        .filter((item) => item._status === 'USED' && item.used !== false)
                        .map((item, idx) => {
                          const score = item.score || 0;
                          const scorePercent = typeof score === 'number' ? Math.round(score * 100) : null;
                          const statusStyle = getStatusStyle('USED');
                          return (
                            <div key={idx} className={`p-3 border rounded ${statusStyle.container} hover:shadow-sm transition-shadow`}>
                              <div className="flex justify-between items-start mb-2">
                                <h4 className="font-bold text-green-700">
                                  {statusStyle.icon} {item.filename || '문서'} (p.{item.page || '-'})
                                </h4>
                                <span className={`px-2 py-1 text-xs font-bold rounded-full ${statusStyle.badge}`}>
                                  점수: {scorePercent !== null ? `${scorePercent}%` : '-'}
                                </span>
                              </div>
                              <p className="text-sm text-gray-700 line-clamp-2">{item.text || item.content || item.excerpt || '내용 없음'}</p>
                              {item._reason && <p className="text-xs text-green-600 mt-1">ℹ {item._reason}</p>}
                              <button
                                onClick={() => {
                                  const event = new CustomEvent('openPDF', {
                                    detail: {
                                      filename: item.filename || 'document.pdf',
                                      page: item.page || 1
                                    }
                                  });
                                  window.dispatchEvent(event);
                                }}
                                className="mt-2 text-xs text-green-600 hover:underline font-medium"
                              >
                                📑 PDF 보기
                              </button>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}

                {/* 필터링된 문서 */}
                {ragFilteredCount > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-300">
                    <h5 className="font-bold text-gray-700 mb-2">✗ 필터링된 문서 ({ragFilteredCount})</h5>
                    <p className="text-xs text-gray-500 mb-3">※ 다음 문서들은 검색되었지만 품질 기준에 맞지 않아 답변에 사용되지 않았습니다.</p>
                    <div className="space-y-2">
                      {ragResults
                        .filter((item) => item._status !== 'USED' || item.used === false)
                        .map((item, idx) => {
                          const score = item.score || 0;
                          const scorePercent = typeof score === 'number' ? Math.round(score * 100) : null;
                          const statusStyle = getStatusStyle(item._status);
                          return (
                            <div key={idx} className={`p-2 border rounded text-xs ${statusStyle.container}`}>
                              <div className="flex justify-between items-start">
                                <span className="font-medium">
                                  {statusStyle.icon} {item.filename || '문서'} (p.{item.page || '-'})
                                </span>
                                <span className={`px-2 py-0.5 rounded-full ${statusStyle.badge}`}>
                                  {getStatusLabel(item._status)} · {scorePercent}%
                                </span>
                              </div>
                              {item._reason && (
                                <p className="text-gray-600 mt-1">
                                  사유: {item._reason}
                                </p>
                              )}
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p className="text-gray-400 text-center py-8">RAG 검색 결과가 없습니다.</p>
            )}
          </div>
        )}

        {/* Ontology 탭 */}
        {activeTab === 'ontology' && (
          <div className="space-y-4">
            {/* v2 ontology_graph 구조 지원 */}
            {ontologyGraphResponse ? (
              <OntologyGraphRenderer response={ontologyGraphResponse} />
            ) : ontologyCount > 0 ? (
              /* Fallback: 기존 구조 */
              <>
                {/* 요약 정보 */}
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                  <h5 className="font-bold text-purple-900 mb-2">📊 온톨로지 검색 결과</h5>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-purple-600 font-bold">{ontologyCount}</span>
                      <span className="text-gray-600">개 검색됨</span>
                    </div>
                    <div>
                      <span className="text-green-600 font-bold">✓ {ontologyUsedCount}</span>
                      <span className="text-gray-600">개 사용됨</span>
                    </div>
                    <div>
                      <span className="text-gray-600 font-bold">✗ {ontologyFilteredCount}</span>
                      <span className="text-gray-600">개 필터됨</span>
                    </div>
                  </div>
                </div>

                {/* 사용된 엔티티 */}
                {ontologyUsedCount > 0 && (
                  <div>
                    <h5 className="font-bold text-green-700 mb-2">✓ 사용된 엔티티 ({ontologyUsedCount})</h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {ontologyResults
                        .filter((entity) => entity._status === 'USED' && entity.used !== false)
                        .map((entity, idx) => {
                          const statusStyle = getStatusStyle('USED');
                          return (
                            <div
                              key={idx}
                              className={`p-3 border rounded ${statusStyle.container} hover:shadow-sm transition-shadow`}
                            >
                              <div className="flex items-start gap-2">
                                <span className="text-green-600 font-bold text-lg">{statusStyle.icon}</span>
                                <div className="flex-1">
                                  <h4 className="font-bold text-green-700 mb-1">
                                    {entity.entity_name || entity.name || '엔티티'}
                                  </h4>
                                  <p className="text-sm text-gray-600">
                                    {entity.description || `${entity.relation} → ${entity.target}`}
                                  </p>
                                  {entity._reason && (
                                    <p className="text-xs text-green-600 mt-1">ℹ {entity._reason}</p>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}

                {/* 필터링된 엔티티 */}
                {ontologyFilteredCount > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-300">
                    <h5 className="font-bold text-gray-700 mb-2">✗ 필터링된 엔티티 ({ontologyFilteredCount})</h5>
                    <p className="text-xs text-gray-500 mb-3">※ 다음 엔티티들은 검색되었지만 품질 기준에 맞지 않아 답변에 사용되지 않았습니다.</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {ontologyResults
                        .filter((entity) => entity._status !== 'USED' || entity.used === false)
                        .map((entity, idx) => {
                          const statusStyle = getStatusStyle(entity._status);
                          return (
                            <div key={idx} className={`p-2 border rounded text-xs ${statusStyle.container}`}>
                              <div className="flex items-start gap-2">
                                <span className="font-bold text-sm">{statusStyle.icon}</span>
                                <div className="flex-1">
                                  <h6 className="font-medium">
                                    {entity.entity_name || entity.name || '엔티티'}
                                  </h6>
                                  {entity._reason && (
                                    <p className="text-gray-600 mt-0.5">
                                      사유: {entity._reason}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p className="text-gray-400 text-center py-8">Ontology 검색 결과가 없습니다.</p>
            )}
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
