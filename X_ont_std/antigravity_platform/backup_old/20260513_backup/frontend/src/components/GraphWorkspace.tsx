"use client";

import React, { useCallback, useEffect, useState } from "react";
import ReactFlow, { 
  Background, 
  Controls, 
  Node, 
  Edge, 
  useNodesState, 
  useEdgesState, 
  Handle, 
  Position 
} from "reactflow";
import "reactflow/dist/style.css";
import { Users, ShoppingCart, Package, Box, Shield, Zap, Target } from "lucide-react";

const iconMap: Record<string, any> = {
  Customer: Users,
  Order: ShoppingCart,
  Product: Package,
  Box: Box
};

const CustomNode = ({ data, selected }: any) => {
  const Icon = iconMap[data.type] || Box;
  
  return (
    <div className={`
      relative group transition-all duration-500
      ${selected ? 'scale-105' : 'hover:scale-102'}
    `}>
      {/* Node Body */}
      <div className={`
        px-5 py-4 rounded-[24px] bg-white border-2 transition-all duration-300 min-w-[180px]
        ${selected 
          ? 'border-indigo-500 shadow-[0_20px_40px_rgba(99,102,241,0.15)] bg-white' 
          : 'border-slate-100 shadow-[0_10px_20px_rgba(0,0,0,0.02)] group-hover:border-indigo-200 group-hover:shadow-lg'}
      `}>
        <Handle type="target" position={Position.Top} className="opacity-0" />
        
        <div className="flex items-center gap-4">
          <div className={`
            p-3 rounded-2xl transition-colors
            ${selected ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-100' : 'bg-slate-50 text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-500'}
          `}>
            <Icon size={22} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-300 group-hover:text-indigo-300 transition-colors mb-0.5">
              {data.type}
            </div>
            <div className="text-sm font-bold text-slate-800 truncate leading-tight">
              {data.label}
            </div>
          </div>
        </div>

        <Handle type="source" position={Position.Bottom} className="opacity-0" />
      </div>

      {/* Selected Indicator Ring */}
      {selected && (
        <div className="absolute -inset-2 border-2 border-indigo-500/20 rounded-[32px] animate-pulse" />
      )}
    </div>
  );
};

const nodeTypes = {
  ontologyNode: CustomNode
};

export default function GraphWorkspace({ data, onNodeClick }: { data: any, onNodeClick: (node: any) => void }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!data) return;

    const initialNodes: Node[] = data.nodes.map((n: any, idx: number) => ({
      id: n.id,
      type: "ontologyNode",
      position: { x: 100 + (idx * 250), y: 150 + (idx * 60) },
      data: { ...n }
    }));

    const initialEdges: Edge[] = data.edges.map((e: any) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: true,
      type: 'smoothstep',
      style: { stroke: "#cbd5e1", strokeWidth: 2 },
      labelStyle: { fill: '#94a3b8', fontWeight: 700, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em' },
      labelBgPadding: [8, 4],
      labelBgBorderRadius: 4,
      labelBgStyle: { fill: '#f8fafc', fillOpacity: 0.8 }
    }));

    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [data, setNodes, setEdges]);

  return (
    <div className="w-full h-full bg-[#f8fafc] relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => onNodeClick(node)}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Background color="#e2e8f0" gap={30} size={1} />
        <Controls className="!bg-white !border-none !shadow-xl !rounded-xl" />
      </ReactFlow>
      
      {/* Floating Info Badge */}
      <div className="absolute top-6 left-6 z-10 px-4 py-2 bg-white/70 backdrop-blur-md rounded-2xl border border-white shadow-lg pointer-events-none">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-[10px] font-black text-slate-800 uppercase tracking-widest">Active Ontology Workspace</span>
          </div>
      </div>
    </div>
  );
}
