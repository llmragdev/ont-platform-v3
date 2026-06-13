"use client";

import cytoscape, { type Core } from "cytoscape";
import dagre from "cytoscape-dagre";
import { Maximize2, PlusCircle, ZoomIn, ZoomOut } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { RDFGraphData } from "@/types/rdf";

cytoscape.use(dagre);

type DagreLayoutOptions = cytoscape.LayoutOptions & {
  name: "dagre";
  rankDir: "LR" | "TB";
  nodeSep: number;
  rankSep: number;
};

interface RDFGraphViewerProps {
  data: RDFGraphData;
  highlightPath?: string[];
  onNodeClick?: (nodeId: string) => void;
  onExpandNode?: (nodeId: string) => void;
  expandedNodeIds?: string[];
  loadingNodeId?: string | null;
}

export function RDFGraphViewer({
  data,
  highlightPath = [],
  onNodeClick,
  onExpandNode,
  expandedNodeIds = [],
  loadingNodeId,
}: RDFGraphViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    cyRef.current?.destroy();
    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...data.nodes.map((node) => ({ data: { ...node, expanded: expandedNodeIds.includes(node.id) || node.expanded } })),
        ...data.edges.map((edge) => ({ data: edge })),
      ],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-size": 10,
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": 6,
            color: "#334155",
            width: 44,
            height: 44,
            "border-width": 2,
            "border-color": "#ffffff",
          },
        },
        {
          selector: 'node[type="entity"]',
          style: { "background-color": "#2563eb", shape: "ellipse", width: 58, height: 58, color: "#1e293b" },
        },
        {
          selector: 'node[type="property"]',
          style: { "background-color": "#059669", shape: "round-rectangle", width: 48, height: 34 },
        },
        {
          selector: 'node[type="literal"]',
          style: { "background-color": "#f59e0b", shape: "diamond", width: 42, height: 42 },
        },
        {
          selector: 'node[type="external"]',
          style: { "background-color": "#7c3aed", shape: "hexagon", width: 56, height: 56 },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#94a3b8",
            "target-arrow-color": "#94a3b8",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": 9,
            color: "#475569",
            "text-background-color": "#ffffff",
            "text-background-opacity": 0.9,
            "text-background-padding": "2px",
          },
        },
        {
          selector: ".highlighted",
          style: {
            "background-color": "#e11d48",
            "line-color": "#e11d48",
            "target-arrow-color": "#e11d48",
            "border-color": "#fecdd3",
            "border-width": 4,
          },
        },
        {
          selector: ".selected",
          style: {
            "border-color": "#0f172a",
            "border-width": 5,
          },
        },
        {
          selector: ".expanded",
          style: {
            "border-color": "#f97316",
            "border-width": 5,
          },
        },
      ],
      layout: { name: "dagre", rankDir: "LR", nodeSep: 45, rankSep: 80 } as DagreLayoutOptions,
      wheelSensitivity: 0.2,
    });

    cy.on("tap", "node", (event) => {
      const nodeId = event.target.id();
      setSelectedNode(nodeId);
      onNodeClick?.(nodeId);
    });

    cyRef.current = cy;
    return () => cy.destroy();
  }, [data, expandedNodeIds, onNodeClick]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass("highlighted selected");
    cy.nodes().removeClass("expanded");
    highlightPath.forEach((id) => cy.$id(id).addClass("highlighted"));
    expandedNodeIds.forEach((id) => cy.$id(id).addClass("expanded"));
    if (selectedNode) cy.$id(selectedNode).addClass("selected");
  }, [expandedNodeIds, highlightPath, selectedNode]);

  function zoomBy(delta: number) {
    const cy = cyRef.current;
    if (!cy) return;
    cy.zoom({ level: Math.max(0.3, Math.min(2.5, cy.zoom() + delta)), renderedPosition: { x: 360, y: 220 } });
  }

  return (
    <section data-testid="rdf-graph-viewer" className="panel">
      <div className="panel-header">
        <div>
          <h3 className="text-sm font-semibold">RDF Graph Viewer</h3>
          <p className="text-xs text-slate-500">{data.nodes.length} nodes / {data.edges.length} edges</p>
        </div>
        <div className="flex gap-2">
          <button type="button" data-testid="rdf-zoom-in" className="btn btn-ghost px-2 py-1" aria-label="Zoom in" onClick={() => zoomBy(0.2)}>
            <ZoomIn className="h-4 w-4" />
          </button>
          <button type="button" data-testid="rdf-zoom-out" className="btn btn-ghost px-2 py-1" aria-label="Zoom out" onClick={() => zoomBy(-0.2)}>
            <ZoomOut className="h-4 w-4" />
          </button>
          <button type="button" data-testid="rdf-fit" className="btn btn-ghost px-2 py-1" aria-label="Fit graph" onClick={() => cyRef.current?.fit(undefined, 40)}>
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="panel-body space-y-3">
        <div ref={containerRef} data-testid="rdf-cytoscape-canvas" className="h-[460px] w-full rounded-md border border-slate-200 bg-white dark:border-slate-800" />
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="badge bg-blue-100 text-blue-700">Entity</span>
          <span className="badge bg-emerald-100 text-emerald-700">Property</span>
          <span className="badge bg-amber-100 text-amber-700">Literal</span>
          <span className="badge bg-violet-100 text-violet-700">External</span>
          {selectedNode && (
            <span data-testid="rdf-selected-node" className="ml-auto inline-flex items-center gap-2 text-slate-500">
              Selected: {selectedNode}
              {onExpandNode && (
                <button
                  type="button"
                  data-testid="rdf-expand-selected"
                  className="btn btn-ghost px-2 py-1 text-xs"
                  disabled={loadingNodeId === selectedNode}
                  onClick={() => onExpandNode(selectedNode)}
                >
                  <PlusCircle className="mr-1 h-3.5 w-3.5" />
                  {loadingNodeId === selectedNode ? "Loading" : "Expand"}
                </button>
              )}
            </span>
          )}
        </div>
      </div>
    </section>
  );
}
