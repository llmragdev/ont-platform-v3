"use client";

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  Node, 
  Edge, 
  Position 
} from 'reactflow';
import 'reactflow/dist/style.css';

// HSL 테마별 노드 스타일 정의
const NODE_COLORS: Record<string, { bg: string, border: string, text: string }> = {
  ready: { bg: 'bg-slate-100 dark:bg-slate-900', border: 'border-slate-300 dark:border-slate-700', text: 'text-slate-500 dark:text-slate-400' },
  running: { bg: 'bg-blue-50 dark:bg-blue-950/30 animate-pulse', border: 'border-blue-300 dark:border-blue-800', text: 'text-blue-700 dark:text-blue-300' },
  success: { bg: 'bg-teal-50 dark:bg-teal-950/30', border: 'border-teal-300 dark:border-teal-800', text: 'text-teal-700 dark:text-teal-300' },
  failed: { bg: 'bg-rose-50 dark:bg-rose-950/30', border: 'border-rose-300 dark:border-rose-800', text: 'text-rose-700 dark:text-rose-300' },
  skipped: { bg: 'bg-slate-50 dark:bg-slate-950/10 opacity-60', border: 'border-slate-200 dark:border-slate-800', text: 'text-slate-400 dark:text-slate-600' }
};

interface FlowNodeData {
  label: string;
  type: string;
  description: string;
  status: string;
  details?: {
    inputs?: any;
    outputs?: any;
    error?: string;
    started_at?: string;
    completed_at?: string;
    execution_time_ms?: number;
  };
}

export function DataFlowView() {
  const [flows, setFlows] = useState<Array<{ flow_id: string; name: string; scenario_id: string; description: string }>>([]);
  const [selectedFlowId, setSelectedFlowId] = useState('');
  const [runs, setRuns] = useState<any[]>([]);
  const [selectedRunId, setSelectedRunId] = useState('');
  
  const [flowData, setFlowData] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'info' | 'data' | 'logs'>('info');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. 초기 데이터 흐름 시나리오 목록 조회
  useEffect(() => {
    const loadFlows = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/data-flows');
        if (!res.ok) throw new Error('데이터 흐름 목록 로드 실패');
        const list = await res.json();
        setFlows(list);
        if (list.length > 0) {
          setSelectedFlowId(list[0].flow_id);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadFlows();
  }, []);

  // 2. 선택한 시나리오에 따른 워크플로우 실행(Runs) 목록 로드
  useEffect(() => {
    if (!selectedFlowId) return;
    const loadRuns = async () => {
      try {
        // 백엔드 workflow_graphs에서 시나리오에 맵핑된 graph를 찾아 실행 리스트 조회
        // 여기서는 기존 workflow api를 활용
        const wfsRes = await fetch('/api/workflow-graphs');
        const wfs = await wfsRes.json();
        
        // scenario_id가 일치하는 그래프 탐색
        const targetFlow = flows.find(f => f.flow_id === selectedFlowId);
        const scenarioId = targetFlow ? targetFlow.scenario_id : '';
        const matchingGraph = wfs.find((w: any) => w.scenario_id === scenarioId || w.id === selectedFlowId);

        if (matchingGraph) {
          const runsRes = await fetch(`/api/workflow-graphs/${matchingGraph.id}/runs`);
          const runsJson = await runsRes.json();
          const list = Array.isArray(runsJson.runs) ? runsJson.runs : [];
          setRuns(list);
          if (list.length > 0) {
            setSelectedRunId(list[0].run_id);
          } else {
            setSelectedRunId('');
          }
        } else {
          setRuns([]);
          setSelectedRunId('');
        }
      } catch (err: any) {
        console.error('실행 이력 로드 실패', err);
        setRuns([]);
        setSelectedRunId('');
      }
    };
    loadRuns();
  }, [selectedFlowId, flows]);

  // 3. 선택한 시나리오 및 실행 ID 기반의 상세 흐름(Dynamic Lineage) 로드
  const loadFlowDetails = useCallback(async () => {
    if (!selectedFlowId) return;
    setLoading(true);
    setError(null);
    try {
      let url = `/api/data-flows/${selectedFlowId}`;
      if (selectedRunId) {
        url += `/runs/${selectedRunId}`;
      }
      const res = await fetch(url);
      if (!res.ok) throw new Error('상세 데이터 흐름 로드 실패');
      const data = await res.json();
      setFlowData(data);
      
      // 기존에 선택된 노드가 있다면 갱신
      if (selectedNode) {
        const updatedNode = data.nodes.find((n: any) => n.id === selectedNode.id);
        if (updatedNode) setSelectedNode(updatedNode);
      }
    } catch (err: any) {
      setError(err.message);
      setFlowData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedFlowId, selectedRunId, selectedNode]);

  useEffect(() => {
    loadFlowDetails();
  }, [selectedFlowId, selectedRunId]);

  // 4. ReactFlow 노드 및 엣지 파싱
  const reactFlowNodes = useMemo<Node[]>(() => {
    if (!flowData || !flowData.nodes) return [];
    
    // 노드를 좌측에서 우측으로 수평 배치하기 위한 위치 계산
    return flowData.nodes.map((node: any, idx: number) => {
      const status = node.status || 'ready';
      const colors = NODE_COLORS[status] || NODE_COLORS.ready;
      
      return {
        id: node.id,
        // ReactFlow 기본 노드 형태 커스터마이징
        data: { 
          label: (
            <div className={`p-4 rounded-xl border-2 transition-all ${colors.bg} ${colors.border} ${colors.text} shadow-md text-left w-48 font-sans`}>
              <div className="text-[10px] font-extrabold uppercase opacity-60 tracking-wider">
                {node.type}
              </div>
              <div className="text-xs font-bold mt-1">
                {node.label}
              </div>
              <div className="flex justify-between items-center mt-2.5 pt-1.5 border-t border-slate-200/55 dark:border-slate-800/40">
                <span className="text-[9px] font-bold tracking-wider uppercase opacity-85">
                  {status}
                </span>
                {node.details?.execution_time_ms && (
                  <span className="text-[9px] opacity-75 font-mono">
                    {node.details.execution_time_ms}ms
                  </span>
                )}
              </div>
            </div>
          )
        },
        // 수평 정렬 배치: x 간격 250px, y축은 꼬임 방지를 위해 약간 지그재그
        position: { x: idx * 240 + 40, y: 150 + (idx % 2 === 0 ? 0 : 35) },
        style: { background: 'none', border: 'none', padding: 0 },
        // 데이터 양방향 정렬을 위한 Handle Position
        sourcePosition: Position.Right,
        targetPosition: Position.Left
      };
    });
  }, [flowData]);

  const reactFlowEdges = useMemo<Edge[]>(() => {
    if (!flowData || !flowData.edges) return [];
    return flowData.edges.map((edge: any, idx: number) => ({
      id: `e-${idx}`,
      source: edge.source,
      target: edge.target,
      animated: true,
      style: { stroke: '#0d9488', strokeWidth: 2 } // teal 색상 선
    }));
  }, [flowData]);

  const onNodeClick = (_: any, node: Node) => {
    if (!flowData) return;
    const originalNode = flowData.nodes.find((n: any) => n.id === node.id);
    if (originalNode) {
      setSelectedNode(originalNode);
    }
  };

  return (
    <div className="space-y-4">
      {/* 상단 컨트롤 패널 */}
      <section className="panel bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">데이터 워크플로우 라인리지</h3>
            <p className="text-xs text-slate-500 mt-1">외부 데이터 유입부터 가공, 워크플로우 처리, 외부 MCP 등록 및 온톨로지 적재 타임라인을 모니터링합니다.</p>
          </div>
          <button className="btn btn-ghost text-xs bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 px-3 py-1.5 rounded-lg text-slate-700 dark:text-slate-300 font-bold" onClick={loadFlowDetails}>
            새로고침
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
          <label className="block text-xs font-bold text-slate-500">
            <span className="mb-1.5 block">데이터 흐름 시나리오</span>
            <select 
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal-100 dark:focus:ring-teal-950" 
              value={selectedFlowId} 
              onChange={(e) => setSelectedFlowId(e.target.value)}
            >
              {flows.map((f) => (
                <option key={f.flow_id} value={f.flow_id}>{f.name}</option>
              ))}
            </select>
          </label>
          <label className="block text-xs font-bold text-slate-500">
            <span className="mb-1.5 block">연동된 워크플로우 실행 회차</span>
            <select 
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal-100 dark:focus:ring-teal-950" 
              value={selectedRunId} 
              onChange={(e) => setSelectedRunId(e.target.value)}
            >
              {runs.length === 0 && <option value="">실행 이력 없음 (정적 계보만 표시)</option>}
              {runs.map((run) => (
                <option key={run.run_id} value={run.run_id}>
                  {new Date(run.started_at).toLocaleString('ko-KR')} / {run.status} / {run.run_id.substring(0, 10)}...
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 dark:bg-rose-950/20 px-4 py-3 text-sm text-rose-700 dark:text-rose-300">{error}</div>}
      {loading && <div className="text-sm text-slate-400">계보 데이터 로딩 중...</div>}

      {/* 메인 라인리지 시각화 영역 */}
      <div className="grid gap-4 xl:grid-cols-[1fr_360px] h-[550px]">
        
        {/* 캔버스 (ReactFlow) */}
        <section className="panel border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 h-full relative overflow-hidden flex flex-col">
          <div className="border-b border-slate-200 dark:border-slate-800 px-5 py-4 flex justify-between items-center bg-slate-50 dark:bg-slate-950 rounded-t-2xl">
            <h4 className="font-bold text-xs text-slate-700 dark:text-slate-300">데이터 계보 캔버스</h4>
            <div className="flex gap-3 text-[10px] font-bold text-slate-500">
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-teal-500"></span>Success</span>
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-blue-500"></span>Running</span>
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-rose-500"></span>Failed</span>
            </div>
          </div>
          <div className="flex-1 w-full bg-slate-50/50 dark:bg-slate-950/20" style={{ height: '100%', minHeight: '450px' }}>
            {reactFlowNodes.length > 0 ? (
              <ReactFlow
                nodes={reactFlowNodes}
                edges={reactFlowEdges}
                onNodeClick={onNodeClick}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                minZoom={0.5}
                maxZoom={1.5}
              >
                <Background color="#cbd5e1" gap={16} size={1} />
                <Controls />
                <MiniMap 
                  nodeStrokeColor={() => '#cbd5e1'}
                  nodeColor={(n) => '#f1f5f9'}
                  style={{ backgroundColor: '#0f172a' }}
                />
              </ReactFlow>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                데이터 흐름 정보가 존재하지 않습니다.
              </div>
            )}
          </div>
        </section>

        {/* 우측 상세 패널 */}
        <section className="panel border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 h-full flex flex-col">
          <div className="border-b border-slate-200 dark:border-slate-800 px-5 py-4 bg-slate-50 dark:bg-slate-950 rounded-t-2xl">
            <h4 className="font-bold text-xs text-slate-700 dark:text-slate-300">선택 단계 상세</h4>
          </div>

          <div className="flex-1 p-5 overflow-y-auto space-y-4 font-sans text-sm">
            {!selectedNode ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                데이터 흐름 노드를 선택하시면 실행 결과 및 입출력 상세 명세가 여기에 노출됩니다.
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <div className="text-[10px] font-extrabold uppercase text-slate-400 tracking-wider">단계 유형</div>
                  <div className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{selectedNode.type.toUpperCase()}</div>
                </div>
                <div>
                  <div className="text-[10px] font-extrabold uppercase text-slate-400 tracking-wider">단계 이름</div>
                  <div className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{selectedNode.label}</div>
                </div>
                <div>
                  <div className="text-[10px] font-extrabold uppercase text-slate-400 tracking-wider">단계 요약 설명</div>
                  <div className="text-slate-600 dark:text-slate-400 text-xs mt-1 leading-relaxed">{selectedNode.description}</div>
                </div>

                <div className="border-t border-slate-200 dark:border-slate-800 pt-3">
                  {/* 탭 버튼 */}
                  <div className="flex border-b border-slate-200 dark:border-slate-800 text-xs mb-3 font-bold">
                    <button className={`pb-2 pr-4 ${activeTab === 'info' ? 'text-teal-600 border-b-2 border-teal-500' : 'text-slate-400'}`} onClick={() => setActiveTab('info')}>실행 정보</button>
                    <button className={`pb-2 px-4 ${activeTab === 'data' ? 'text-teal-600 border-b-2 border-teal-500' : 'text-slate-400'}`} onClick={() => setActiveTab('data')}>입출력 데이터</button>
                  </div>

                  {/* 탭 컨텐츠 */}
                  {activeTab === 'info' && (
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 py-1">
                        <span className="text-slate-400">현재 상태</span>
                        <span className="font-bold uppercase text-teal-600">{selectedNode.status || 'ready'}</span>
                      </div>
                      <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 py-1">
                        <span className="text-slate-400">시작 시각</span>
                        <span className="text-slate-700 dark:text-slate-300 font-mono">{selectedNode.details?.started_at ? new Date(selectedNode.details.started_at).toLocaleString() : '-'}</span>
                      </div>
                      <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 py-1">
                        <span className="text-slate-400">완료 시각</span>
                        <span className="text-slate-700 dark:text-slate-300 font-mono">{selectedNode.details?.completed_at ? new Date(selectedNode.details.completed_at).toLocaleString() : '-'}</span>
                      </div>
                      {selectedNode.details?.execution_time_ms && (
                        <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 py-1">
                          <span className="text-slate-400">소요 시간</span>
                          <span className="text-slate-700 dark:text-slate-300 font-mono">{selectedNode.details.execution_time_ms}ms</span>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'data' && (
                    <div className="space-y-3">
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 block mb-1">INPUT (입력)</span>
                        <div className="bg-slate-950 border border-slate-850 p-2.5 rounded-lg text-[11px] font-mono text-emerald-400 max-h-36 overflow-y-auto">
                          {selectedNode.details?.inputs ? JSON.stringify(selectedNode.details.inputs, null, 2) : '{}'}
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 block mb-1">OUTPUT (출력)</span>
                        <div className="bg-slate-950 border border-slate-850 p-2.5 rounded-lg text-[11px] font-mono text-blue-450 max-h-36 overflow-y-auto">
                          {selectedNode.details?.outputs ? JSON.stringify(selectedNode.details.outputs, null, 2) : '{}'}
                        </div>
                      </div>
                      {selectedNode.details?.error && (
                        <div>
                          <span className="text-[10px] font-bold text-rose-400 block mb-1">ERROR (에러)</span>
                          <div className="bg-rose-950/20 border border-rose-900/50 p-2.5 rounded-lg text-[11px] font-mono text-rose-500">
                            {selectedNode.details.error}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </section>

      </div>
    </div>
  );
}
