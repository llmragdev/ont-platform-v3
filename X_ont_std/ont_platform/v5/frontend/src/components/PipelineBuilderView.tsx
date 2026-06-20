"use client";

import React, { useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Position,
  Connection,
  addEdge,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  GitBranch, 
  Database, 
  Bot, 
  Wrench, 
  Route, 
  Save, 
  Trash2, 
  Plus, 
  HelpCircle,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

// 노드 카테고리 정의
interface PaletteNode {
  type: string;
  label: string;
  category: 'source' | 'transform' | 'execute' | 'sink';
  description: string;
  icon: React.ComponentType<any>;
  defaultConfig: Record<string, any>;
}

const PALETTE_NODES: PaletteNode[] = [
  // 1. Sources
  { 
    type: 'request_input', 
    label: '웹훅 이벤트 수신', 
    category: 'source', 
    description: '외부 시스템의 HTTP POST 이벤트를 실시간 수집', 
    icon: Database,
    defaultConfig: { mode: 'post', auth_required: false, endpoint: '/api/extn/events' }
  },
  { 
    type: 'batch_polling', 
    label: '배치 폴링 수집', 
    category: 'source', 
    description: '주기적으로 외부 테이블 또는 REST API를 조회', 
    icon: Database,
    defaultConfig: { mode: 'batch', interval_cron: '*/5 * * * *', limit: 10 }
  },
  // 2. Transforms
  { 
    type: 'intent_classify', 
    label: 'LLM 의도/유형 분류', 
    category: 'transform', 
    description: 'LLM을 활용한 유입 텍스트 카테고리 분류', 
    icon: Bot,
    defaultConfig: { model: 'gpt-4o', categories: 'password, billing, refund, general', system_prompt: '고객 문의의 핵심 의도를 분류하시오.' }
  },
  { 
    type: 'equipment_map', 
    label: '설비/자산 매핑', 
    category: 'transform', 
    description: '원문 텍스트 내 공장/설비명을 온톨로지 키와 매핑', 
    icon: Wrench,
    defaultConfig: { ontology_class: 'Equipment', match_threshold: 0.8 }
  },
  { 
    type: 'recurrence_check', 
    label: '반복/재발 여부 판단', 
    category: 'transform', 
    description: '온톨로지 내 최근 장애 이력을 조회하여 재발 판단', 
    icon: Route,
    defaultConfig: { lookback_days: 7, count_threshold: 2 }
  },
  // 3. Executes
  { 
    type: 'knowledge_lookup', 
    label: '지식/RAG 조회', 
    category: 'execute', 
    description: '사내 가이드 및 온톨로지 지식 DB 유사성 검색', 
    icon: Bot,
    defaultConfig: { kb_source: 'ontology_manuals', search_top_k: 3 }
  },
  { 
    type: 'draft_response', 
    label: '조치/답변 초안 생성', 
    category: 'execute', 
    description: '수집된 근거를 조합하여 현장 지침 및 답변 작성', 
    icon: Bot,
    defaultConfig: { temperature: 0.5, max_tokens: 500 }
  },
  // 4. Sinks
  { 
    type: 'customer_mcp_comment_create', 
    label: '고객사 MCP 댓글 등록', 
    category: 'sink', 
    description: '고객사 MCP 계층을 통해 최종 댓글 및 답변 등록', 
    icon: GitBranch,
    defaultConfig: { mcp_server: 'customer_mcp', tool: 'comment.create', port: 8080 }
  },
  { 
    type: 'ontology_write', 
    label: '온톨로지 저장 (Sink)', 
    category: 'sink', 
    description: '이벤트 및 조치 결과를 온톨로지 지식으로 영구 적재', 
    icon: Database,
    defaultConfig: { target_class: 'FaultEvent', relationship_link: 'has_task' }
  },
  { 
    type: 'notify_user', 
    label: '감사 로그 및 알림', 
    category: 'sink', 
    description: '처리 이력 감사로그 기록 및 전송(Teams/Email)', 
    icon: GitBranch,
    defaultConfig: { alert_channel: 'Teams', log_format: 'jsonl' }
  }
];

export function PipelineBuilderView() {
  const [pipelineName, setPipelineName] = useState('신규 데이터 파이프라인');
  const [scenarioId, setScenarioId] = useState('scenario1');
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const loadScenarioTemplate = async () => {
    const templateId = scenarioId === 'scenario1' ? 'service-request-auto-reply' : 'factory-repeated-fault-response';
    try {
      setSaving(true);
      setMessage(null);
      
      const res = await fetch(`/api/workflow-templates/${templateId}`);
      if (!res.ok) {
        throw new Error('템플릿 데이터를 가져오지 못했습니다.');
      }
      const template = await res.json();
      
      const rfNodes = (template.nodes || []).map((n: any) => {
        const pNode = PALETTE_NODES.find((pn) => pn.type === n.type);
        const category = pNode?.category || n.data?.category || 'transform';
        
        return {
          id: n.id,
          type: 'default',
          position: n.position || { x: 100, y: 100 },
          data: {
            label: n.data?.label || n.id,
            type: n.type,
            category,
            config: {
              ...(pNode?.defaultConfig || {}),
              ...(n.data?.config || {}),
            }
          },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        };
      });

      const rfEdges = (template.edges || []).map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: true,
        style: { stroke: '#0d9488', strokeWidth: 2 }
      }));

      setNodes(rfNodes);
      setEdges(rfEdges);
      setPipelineName(template.name || '신규 데이터 파이프라인');
      setSelectedNode(null);
      setMessage({ type: 'success', text: `${template.name} 템플릿을 성공적으로 불러왔습니다.` });
    } catch (err: any) {
      setMessage({ type: 'error', text: `템플릿 불러오기 실패: ${err.message}` });
    } finally {
      setSaving(false);
    }
  };

  // 1. 커넥션 연결 처리 (단방향 DAG)
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#0d9488', strokeWidth: 2 } }, eds)),
    [setEdges]
  );

  // 2. 드래그앤드롭 이벤트 
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow/type');
      const label = event.dataTransfer.getData('application/reactflow/label');
      const category = event.dataTransfer.getData('application/reactflow/category') as any;

      if (typeof type === 'undefined' || !type) return;

      // 마우스 포지션 계산
      const reactFlowBounds = document.querySelector('.react-flow')?.getBoundingClientRect();
      if (!reactFlowBounds) return;

      const position = {
        x: event.clientX - reactFlowBounds.left - 100,
        y: event.clientY - reactFlowBounds.top - 40,
      };

      const paletteNode = PALETTE_NODES.find(n => n.type === type);
      const newId = `node-${type}-${Date.now().toString().slice(-4)}`;

      const newNode: Node = {
        id: newId,
        type: 'default',
        position,
        data: { 
          label,
          type,
          category,
          config: { ...(paletteNode?.defaultConfig || {}) }
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [setNodes]
  );

  // 3. 노드 선택 시 속성 매핑
  const onNodeClick = (_: any, node: Node) => {
    setSelectedNode(node);
  };

  // 4. 노드 설정 값 업데이트
  const updateNodeConfig = (key: string, value: any) => {
    if (!selectedNode) return;
    
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === selectedNode.id) {
          const updatedConfig = {
            ...node.data.config,
            [key]: value
          };
          const updatedNode = {
            ...node,
            data: {
              ...node.data,
              config: updatedConfig
            }
          };
          // 현재 선택된 노드 레퍼런스도 함께 갱신
          setSelectedNode(updatedNode);
          return updatedNode;
        }
        return node;
      })
    );
  };

  // 5. 노드 삭제
  const deleteSelectedNode = () => {
    if (!selectedNode) return;
    setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id));
    setEdges((eds) => eds.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id));
    setSelectedNode(null);
  };

  // 6. 노드 렌더링 스타일 지정
  const styledNodes = useMemo(() => {
    return nodes.map((node) => {
      const isSelected = selectedNode && selectedNode.id === node.id;
      const category = node.data.category;
      
      let borderColors = 'border-slate-300 dark:border-slate-700';
      let bgColors = 'bg-white dark:bg-slate-900';
      let textColors = 'text-slate-800 dark:text-slate-200';

      if (category === 'source') {
        borderColors = isSelected ? 'border-emerald-500' : 'border-emerald-300 dark:border-emerald-800';
        bgColors = 'bg-emerald-50/70 dark:bg-emerald-950/20';
        textColors = 'text-emerald-900 dark:text-emerald-300';
      } else if (category === 'transform') {
        borderColors = isSelected ? 'border-indigo-500' : 'border-indigo-300 dark:border-indigo-800';
        bgColors = 'bg-indigo-50/70 dark:bg-indigo-950/20';
        textColors = 'text-indigo-900 dark:text-indigo-300';
      } else if (category === 'execute') {
        borderColors = isSelected ? 'border-cyan-500' : 'border-cyan-300 dark:border-cyan-800';
        bgColors = 'bg-cyan-50/70 dark:bg-cyan-950/20';
        textColors = 'text-cyan-900 dark:text-cyan-300';
      } else if (category === 'sink') {
        borderColors = isSelected ? 'border-amber-500' : 'border-amber-300 dark:border-amber-800';
        bgColors = 'bg-amber-50/70 dark:bg-amber-950/20';
        textColors = 'text-amber-900 dark:text-amber-300';
      }

      return {
        ...node,
        data: {
          ...node.data,
          label: (
            <div className={`p-3 rounded-lg border-2 shadow-sm ${bgColors} ${borderColors} ${textColors} text-left w-44 font-sans`}>
              <div className="text-[9px] font-extrabold uppercase opacity-60 tracking-wider">
                {node.data.category}
              </div>
              <div className="text-xs font-bold mt-0.5 truncate">
                {node.data.label}
              </div>
              <div className="text-[8px] opacity-75 mt-1 font-mono truncate">
                {node.id}
              </div>
            </div>
          )
        },
        style: { background: 'none', border: 'none', padding: 0 }
      };
    });
  }, [nodes, selectedNode]);

  // 7. 배포 및 저장 호출
  const handleDeploy = async () => {
    if (nodes.length === 0) {
      setMessage({ type: 'error', text: '배포할 노드가 하나도 없습니다.' });
      return;
    }

    setSaving(true);
    setMessage(null);

    // 컴파일: ReactFlow 구조를 백엔드 WorkflowGraph 구조로 변환
    const graphPayload = {
      id: `wfg-builder-${Date.now().toString().slice(-6)}`,
      name: pipelineName,
      scenario_id: scenarioId,
      scenario_version: 'v1',
      graph_kind: 'template_copy',
      execution_mode: 'batch',
      runtime: {
        executor: scenarioId === 'scenario1' ? 'scenario1.customer_question_auto_reply' : 'factory.repeated_fault_response',
        default_mode: 'post',
        allow_post: true,
        batch_status: 'open',
        batch_limit: 10
      },
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.data.type,
        position: n.position,
        data: {
          label: n.data.label,
          category: n.data.category,
          config: n.data.config
        }
      })),
      edges: edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target
      }))
    };

    try {
      const res = await fetch('/api/workflow-graphs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(graphPayload)
      });

      if (!res.ok) {
        throw new Error('파이프라인 배포 서버 응답 실패');
      }

      setMessage({ type: 'success', text: '성공적으로 데이터 파이프라인을 배포했습니다!' });
    } catch (err: any) {
      setMessage({ type: 'error', text: `배포 실패: ${err.message}` });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* 상단 컨트롤 바 */}
      <section className="panel bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex-1 w-full md:w-auto">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">파이프라인 빌더 (Pipeline Builder)</h3>
            <p className="text-xs text-slate-500 mt-1">드래그 앤 드롭 방식으로 데이터 가공, RAG 지식조회, MCP 등록 및 온톨로지 적재 흐름을 시각적으로 설계합니다.</p>
          </div>
          <div className="flex gap-2 w-full md:w-auto justify-end">
            <button 
              className="btn btn-ghost text-xs bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 px-3.5 py-2 rounded-lg text-slate-700 dark:text-slate-300 font-bold"
              onClick={() => {
                setNodes([]);
                setEdges([]);
                setSelectedNode(null);
                setMessage(null);
              }}
            >
              초기화
            </button>
            <button 
              className="btn flex items-center gap-1.5 text-xs bg-teal-650 hover:bg-teal-700 dark:bg-teal-600 dark:hover:bg-teal-500 text-white px-4 py-2 rounded-lg font-bold shadow-md transition-all"
              onClick={handleDeploy}
              disabled={saving}
            >
              <Save className="h-3.5 w-3.5" />
              {saving ? '배포 중...' : '배포 (Deploy)'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
          <label className="block text-xs font-bold text-slate-500">
            <span className="mb-1.5 block">파이프라인 이름</span>
            <input 
              type="text"
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-slate-950 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal-100 dark:focus:ring-teal-950" 
              value={pipelineName}
              onChange={(e) => setPipelineName(e.target.value)}
            />
          </label>
          <div className="flex gap-2 items-end">
            <label className="block flex-1 text-xs font-bold text-slate-500">
              <span className="mb-1.5 block">타겟 시나리오 스코프</span>
              <select 
                className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-slate-950 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal-100 dark:focus:ring-teal-950" 
                value={scenarioId} 
                onChange={(e) => setScenarioId(e.target.value)}
              >
                <option value="scenario1">고객사 문의 자동댓글 (Scenario 1)</option>
                <option value="scenario2">공장 반복 고장 정비지시 (Scenario 2)</option>
              </select>
            </label>
            <button
              type="button"
              onClick={loadScenarioTemplate}
              disabled={saving}
              className="btn text-xs bg-teal-50 border border-teal-200 text-teal-700 hover:bg-teal-100 dark:bg-teal-950/20 dark:border-teal-900/50 dark:text-teal-400 px-3.5 py-2 rounded-lg font-bold shrink-0 transition-all"
            >
              템플릿 불러오기
            </button>
          </div>
          <div className="flex items-end">
            {message && (
              <div className={`w-full text-xs font-bold px-3 py-2 rounded-lg flex items-center gap-1.5 border ${
                message.type === 'success' 
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-900/50' 
                  : 'bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/20 dark:border-rose-900/50'
              }`}>
                {message.type === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                {message.text}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 빌더 캔버스 영역 */}
      <div className="grid gap-4 xl:grid-cols-[260px_1fr_360px] h-[580px]">
        {/* 1. 좌측 노드 팔레트 */}
        <section className="panel border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 h-full flex flex-col overflow-hidden">
          <div className="border-b border-slate-200 dark:border-slate-800 px-4 py-3 bg-slate-50 dark:bg-slate-950 rounded-t-2xl">
            <h4 className="font-bold text-xs text-slate-700 dark:text-slate-300">노드 팔레트</h4>
          </div>
          <div className="flex-1 p-3 overflow-y-auto space-y-4">
            {/* 카테고리별 구분 */}
            {['source', 'transform', 'execute', 'sink'].map((cat) => {
              const catNodes = PALETTE_NODES.filter(n => n.category === cat);
              return (
                <div key={cat} className="space-y-1.5">
                  <div className="text-[10px] font-extrabold uppercase text-slate-400 tracking-wider">
                    {cat === 'source' ? 'Sources (입력)' : cat === 'transform' ? 'Transforms (가공)' : cat === 'execute' ? 'Executes (수행)' : 'Sinks (적재/출력)'}
                  </div>
                  {catNodes.map((pNode) => {
                    const Icon = pNode.icon;
                    return (
                      <div 
                        key={pNode.type}
                        className="flex items-center gap-2 p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:bg-slate-50 dark:hover:bg-slate-950/50 cursor-grab transition-all text-xs text-slate-700 dark:text-slate-300 active:cursor-grabbing"
                        draggable
                        onDragStart={(event) => {
                          event.dataTransfer.setData('application/reactflow/type', pNode.type);
                          event.dataTransfer.setData('application/reactflow/label', pNode.label);
                          event.dataTransfer.setData('application/reactflow/category', pNode.category);
                          event.dataTransfer.effectAllowed = 'move';
                        }}
                      >
                        <div className="p-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                          <Icon className="h-3.5 w-3.5" />
                        </div>
                        <div className="truncate">
                          <div className="font-bold text-[11px]">{pNode.label}</div>
                          <div className="text-[9px] opacity-75 truncate">{pNode.description}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </section>

        {/* 2. 중앙 캔버스 */}
        <section className="panel border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 h-full relative overflow-hidden flex flex-col">
          <div className="border-b border-slate-200 dark:border-slate-800 px-5 py-4 bg-slate-50 dark:bg-slate-950 rounded-t-2xl">
            <h4 className="font-bold text-xs text-slate-700 dark:text-slate-300">파이프라인 디자인 그리드</h4>
          </div>
          <div className="flex-1 w-full bg-slate-50/50 dark:bg-slate-950/20" style={{ height: '100%', minHeight: '450px' }}>
            <ReactFlow
              nodes={styledNodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onDragOver={onDragOver}
              onDrop={onDrop}
              onNodeClick={onNodeClick}
              fitView
              fitViewOptions={{ padding: 0.2 }}
            >
              <Background color="#cbd5e1" gap={16} size={1} />
              <Controls />
              <MiniMap 
                nodeStrokeColor={() => '#cbd5e1'}
                nodeColor={(n) => '#f1f5f9'}
                style={{ backgroundColor: '#0f172a' }}
              />
            </ReactFlow>
          </div>
        </section>

        {/* 3. 우측 속성 패널 */}
        <section className="panel border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 h-full flex flex-col overflow-hidden">
          <div className="border-b border-slate-200 dark:border-slate-800 px-5 py-4 bg-slate-50 dark:bg-slate-950 rounded-t-2xl">
            <h4 className="font-bold text-xs text-slate-700 dark:text-slate-300">속성 패널</h4>
          </div>

          <div className="flex-1 p-5 overflow-y-auto space-y-5 font-sans text-sm">
            {!selectedNode ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs text-center space-y-2">
                <HelpCircle className="h-8 w-8 opacity-55 text-slate-400" />
                <div>캔버스 상의 노드를 마우스 클릭하시면<br />매핑 규칙 및 파라미터 설정을 기재할 수 있습니다.</div>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <div className="text-[10px] font-extrabold uppercase text-slate-400 tracking-wider">노드 ID</div>
                  <div className="font-mono text-xs text-slate-700 dark:text-slate-300 mt-0.5">{selectedNode.id}</div>
                </div>
                <div>
                  <div className="text-[10px] font-extrabold uppercase text-slate-400 tracking-wider">노드 타입</div>
                  <div className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{selectedNode.data.type}</div>
                </div>

                <div className="border-t border-slate-200 dark:border-slate-800 pt-4 space-y-4">
                  <div className="text-xs font-bold text-slate-700 dark:text-slate-300">세부 파라미터 구성</div>
                  
                  {/* 노드 타입별 맞춤형 폼 렌더링 */}
                  {selectedNode.data.type === 'request_input' && (
                    <label className="block text-xs font-bold text-slate-500">
                      <span className="mb-1 block">웹훅 수신 엔드포인트 URL</span>
                      <input 
                        type="text" 
                        className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                        value={selectedNode.data.config.endpoint || ''}
                        onChange={(e) => updateNodeConfig('endpoint', e.target.value)}
                      />
                    </label>
                  )}

                  {selectedNode.data.type === 'batch_polling' && (
                    <div className="space-y-3">
                      <label className="block text-xs font-bold text-slate-500">
                        <span className="mb-1 block">폴링 주기 (Cron Expression)</span>
                        <input 
                          type="text" 
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                          value={selectedNode.data.config.interval_cron || ''}
                          onChange={(e) => updateNodeConfig('interval_cron', e.target.value)}
                        />
                      </label>
                      <label className="block text-xs font-bold text-slate-500">
                        <span className="mb-1 block">수집 처리 리밋 (Limit)</span>
                        <input 
                          type="number" 
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                          value={selectedNode.data.config.limit || 10}
                          onChange={(e) => updateNodeConfig('limit', parseInt(e.target.value))}
                        />
                      </label>
                    </div>
                  )}

                  {selectedNode.data.type === 'intent_classify' && (
                    <div className="space-y-3">
                      <label className="block text-xs font-bold text-slate-500">
                        <span className="mb-1 block">분류 카테고리 (쉼표 구분)</span>
                        <input 
                          type="text" 
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                          value={selectedNode.data.config.categories || ''}
                          onChange={(e) => updateNodeConfig('categories', e.target.value)}
                        />
                      </label>
                      <label className="block text-xs font-bold text-slate-500">
                        <span className="mb-1 block">LLM 분류 지침 (System Prompt)</span>
                        <textarea 
                          rows={4}
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                          value={selectedNode.data.config.system_prompt || ''}
                          onChange={(e) => updateNodeConfig('system_prompt', e.target.value)}
                        />
                      </label>
                    </div>
                  )}

                  {selectedNode.data.type === 'equipment_map' && (
                    <label className="block text-xs font-bold text-slate-500">
                      <span className="mb-1 block">매핑 타겟 온톨로지 클래스</span>
                      <input 
                        type="text" 
                        className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                        value={selectedNode.data.config.ontology_class || ''}
                        onChange={(e) => updateNodeConfig('ontology_class', e.target.value)}
                      />
                    </label>
                  )}

                  {selectedNode.data.type === 'knowledge_lookup' && (
                    <label className="block text-xs font-bold text-slate-500">
                      <span className="mb-1 block">RAG 타겟 지식 소스</span>
                      <input 
                        type="text" 
                        className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                        value={selectedNode.data.config.kb_source || ''}
                        onChange={(e) => updateNodeConfig('kb_source', e.target.value)}
                      />
                    </label>
                  )}

                  {selectedNode.data.type === 'customer_mcp_comment_create' && (
                    <div className="space-y-3">
                      <label className="block text-xs font-bold text-slate-500">
                        <span className="mb-1 block">연동 MCP 서버명</span>
                        <input 
                          type="text" 
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                          value={selectedNode.data.config.mcp_server || ''}
                          onChange={(e) => updateNodeConfig('mcp_server', e.target.value)}
                        />
                      </label>
                      <label className="block text-xs font-bold text-slate-500">
                        <span className="mb-1 block">도출 액션 도구(Tool) 명</span>
                        <input 
                          type="text" 
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                          value={selectedNode.data.config.tool || ''}
                          onChange={(e) => updateNodeConfig('tool', e.target.value)}
                        />
                      </label>
                    </div>
                  )}

                  {selectedNode.data.type === 'ontology_write' && (
                    <div className="space-y-3">
                      <label className="block text-xs font-bold text-slate-500">
                        <span className="mb-1 block">적재 객체 타입 (Class)</span>
                        <input 
                          type="text" 
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                          value={selectedNode.data.config.target_class || ''}
                          onChange={(e) => updateNodeConfig('target_class', e.target.value)}
                        />
                      </label>
                      <label className="block text-xs font-bold text-slate-500">
                        <span className="mb-1 block">생성할 링크 타입 (Link)</span>
                        <input 
                          type="text" 
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                          value={selectedNode.data.config.relationship_link || ''}
                          onChange={(e) => updateNodeConfig('relationship_link', e.target.value)}
                        />
                      </label>
                    </div>
                  )}

                  {/* Fallback for other nodes */}
                  {!['request_input', 'batch_polling', 'intent_classify', 'equipment_map', 'knowledge_lookup', 'customer_mcp_comment_create', 'ontology_write'].includes(selectedNode.data.type) && (
                    <div className="space-y-2">
                      {Object.keys(selectedNode.data.config).map((configKey) => (
                        <label key={configKey} className="block text-xs font-bold text-slate-500">
                          <span className="mb-1 block">{configKey}</span>
                          <input 
                            type="text" 
                            className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-teal-400"
                            value={selectedNode.data.config[configKey] || ''}
                            onChange={(e) => updateNodeConfig(configKey, e.target.value)}
                          />
                        </label>
                      ))}
                    </div>
                  )}

                </div>

                <div className="border-t border-slate-200 dark:border-slate-800 pt-4">
                  <button 
                    className="w-full btn flex items-center justify-center gap-1.5 text-xs bg-rose-50 hover:bg-rose-100 text-rose-600 dark:bg-rose-950/20 dark:hover:bg-rose-950/40 dark:text-rose-400 p-2 rounded-lg font-bold transition-all border border-rose-200 dark:border-rose-900/50"
                    onClick={deleteSelectedNode}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    이 노드 삭제
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
