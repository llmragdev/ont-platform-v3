"use client";

import dynamic from "next/dynamic";
import { Network, Route } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";
import { mockNeighborhood, mockRDFGraph } from "@/lib/rdf-mock";
import type { RDFGraphData } from "@/types/rdf";
import { ImportPreviewDialog } from "./ImportPreviewDialog";
import { LinkedDataViewer } from "./LinkedDataViewer";
import { OntologyImporter } from "./OntologyImporter";
import { OntologyMappingPanel } from "./OntologyMappingPanel";
import { RDFGraphStats } from "./RDFGraphStats";

const RDFGraphViewer = dynamic(() => import("./RDFGraphViewer").then((mod) => mod.RDFGraphViewer), {
  ssr: false,
  loading: () => (
    <section data-testid="rdf-graph-viewer" className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">RDF Graph Viewer</h3>
      </div>
      <div className="panel-body">
        <div className="h-[460px] rounded-md border border-slate-200 bg-slate-50 animate-pulse" />
      </div>
    </section>
  ),
});

const PATHS = [
  ["entity:project-alpha", "entity:supplier-42"],
  ["entity:project-alpha", "property:status", "literal:approved"],
  ["entity:project-alpha", "dbpedia:Machine_learning", "wikidata:Q11660"],
];

export function RDFWorkbench({ data = mockRDFGraph }: { data?: RDFGraphData }) {
  const [graphData, setGraphData] = useState<RDFGraphData>(data);
  const [selectedNode, setSelectedNode] = useState("entity:project-alpha");
  const [pathIndex, setPathIndex] = useState(0);
  const [expandedNodeIds, setExpandedNodeIds] = useState<string[]>([]);
  const [loadingNodeId, setLoadingNodeId] = useState<string | null>(null);
  const [maxVisibleNodes] = useState(500);

  const selected = useMemo(
    () => graphData.nodes.find((node) => node.id === selectedNode) ?? graphData.nodes[0],
    [graphData.nodes, selectedNode]
  );

  function mergeGraph(next: RDFGraphData) {
    setGraphData((current) => {
      const nodeMap = new Map(current.nodes.map((node) => [node.id, node]));
      next.nodes.forEach((node) => {
        if (!nodeMap.has(node.id) && nodeMap.size < maxVisibleNodes) nodeMap.set(node.id, node);
      });
      const edgeMap = new Map(current.edges.map((edge) => [edge.id, edge]));
      next.edges.forEach((edge) => {
        if (!edgeMap.has(edge.id)) edgeMap.set(edge.id, edge);
      });
      return { nodes: [...nodeMap.values()], edges: [...edgeMap.values()] };
    });
  }

  async function expandNode(nodeId: string) {
    if (expandedNodeIds.includes(nodeId)) return;
    setLoadingNodeId(nodeId);
    try {
      const subgraph = await api.rdf.neighbors(nodeId, 30);
      mergeGraph(subgraph);
    } catch {
      mergeGraph(mockNeighborhood(nodeId));
    } finally {
      setExpandedNodeIds((prev) => [...prev, nodeId]);
      setLoadingNodeId(null);
    }
  }

  return (
    <div data-testid="rdf-workbench" className="grid gap-4 xl:grid-cols-[minmax(520px,1.35fr)_minmax(360px,0.9fr)]">
      <div className="space-y-4">
        <section className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <Network className="h-4 w-4 text-blue-600" />
              <h3 className="text-sm font-semibold">RDF + External Ontology Lab</h3>
            </div>
            <button
              type="button"
              data-testid="highlight-path-button"
              className="btn btn-ghost text-xs"
              onClick={() => setPathIndex((current) => (current + 1) % PATHS.length)}
            >
              <Route className="mr-1.5 h-3.5 w-3.5" />
              Highlight path
            </button>
          </div>
          <div className="panel-body grid gap-3 text-sm md:grid-cols-3">
            <div>
              <div className="text-xs font-semibold uppercase text-slate-500">Selected node</div>
              <div data-testid="rdf-workbench-selected" className="mt-1 font-mono text-xs">{selected?.id}</div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase text-slate-500">Node type</div>
              <div className="mt-1">{selected?.type}</div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase text-slate-500">Source</div>
              <div className="mt-1">{selected?.source ?? "local"}</div>
            </div>
          </div>
        </section>
        <RDFGraphViewer
          data={graphData}
          highlightPath={PATHS[pathIndex]}
          onNodeClick={setSelectedNode}
          onExpandNode={(nodeId) => void expandNode(nodeId)}
          expandedNodeIds={expandedNodeIds}
          loadingNodeId={loadingNodeId}
        />
      </div>
      <div className="space-y-4">
        <RDFGraphStats data={graphData} maxVisibleNodes={maxVisibleNodes} />
        <OntologyImporter />
        <ImportPreviewDialog request={{ type: "rdf_file", identifier: "ai_domain_sample.ttl", domain_id: "ai" }} />
        <OntologyMappingPanel selectedNode={selected} />
        <LinkedDataViewer entityId={selected?.id ?? "entity:project-alpha"} />
      </div>
    </div>
  );
}
