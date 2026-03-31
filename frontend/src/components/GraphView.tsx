import { useCallback, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import dagre from "@dagrejs/dagre";
import type { GraphResponse } from "@/lib/api";
import type { GraphFilters } from "./GraphFilterPanel";

// ── Colors & config ──

const TYPE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  company:    { bg: "#1e293b", border: "#6366f1", text: "#a5b4fc" },
  person:     { bg: "#1e293b", border: "#0ea5e9", text: "#7dd3fc" },
  article:    { bg: "#1e293b", border: "#f97316", text: "#fdba74" },
  repository: { bg: "#1e293b", border: "#10b981", text: "#6ee7b7" },
  event:      { bg: "#1e293b", border: "#a855f7", text: "#c4b5fd" },
};

const TYPE_ICONS: Record<string, string> = {
  company: "domain",
  person: "person",
  article: "article",
  repository: "code",
  event: "event",
};

const DEFAULT_COLOR = { bg: "#1e293b", border: "#334155", text: "#94a3b8" };

// ── Custom Node ──

function OntologyNode({ data }: { data: { label: string; type: string } }) {
  const color = TYPE_COLORS[data.type] ?? DEFAULT_COLOR;
  return (
    <div
      style={{
        background: color.bg,
        border: `2px solid ${color.border}`,
        borderRadius: "4px",
        padding: "6px 14px",
        minWidth: 80,
        maxWidth: 200,
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: color.border, width: 6, height: 6 }} />
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span
          className="material-symbols-outlined"
          style={{ fontSize: 14, color: color.border }}
        >
          {TYPE_ICONS[data.type] ?? "category"}
        </span>
        <div>
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: "#f8fafc",
              fontFamily: "Space Grotesk, sans-serif",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              maxWidth: 150,
            }}
          >
            {data.label}
          </div>
          <div
            style={{
              fontSize: 8,
              color: color.text,
              fontFamily: "Space Grotesk, sans-serif",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
            }}
          >
            {data.type}
          </div>
        </div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: color.border, width: 6, height: 6 }} />
    </div>
  );
}

const nodeTypes = { ontology: OntologyNode };

// ── Layout functions ──

function layoutDagre(
  nodes: Node[],
  edges: Edge[],
  direction: "LR" | "TB"
): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction, nodesep: 60, ranksep: 120 });

  nodes.forEach((n) => g.setNode(n.id, { width: 180, height: 50 }));
  edges.forEach((e) => g.setEdge(e.source, e.target));

  dagre.layout(g);

  return nodes.map((n) => {
    const pos = g.node(n.id);
    return { ...n, position: { x: pos.x - 90, y: pos.y - 25 } };
  });
}

function layoutRadial(nodes: Node[]): Node[] {
  if (nodes.length === 0) return nodes;
  const cx = 400, cy = 400;
  return nodes.map((n, i) => {
    if (i === 0) return { ...n, position: { x: cx, y: cy } };
    const angle = ((i - 1) / (nodes.length - 1)) * 2 * Math.PI;
    const radius = 250 + Math.floor(i / 12) * 150;
    return {
      ...n,
      position: {
        x: cx + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius,
      },
    };
  });
}

// ── Main Component ──

interface GraphViewProps {
  data: GraphResponse;
  filters: GraphFilters;
  onNodeClick?: (key: string) => void;
}

export function GraphView({ data, filters, onNodeClick }: GraphViewProps) {
  // Filter nodes and edges
  const filtered = useMemo(() => {
    const visibleNodes = data.nodes.filter((n) =>
      filters.nodeTypes.has(n.type)
    );
    const visibleIds = new Set(visibleNodes.map((n) => n.id));
    const visibleEdges = data.edges.filter(
      (e) =>
        filters.linkTypes.has(e.label) &&
        visibleIds.has(e.source) &&
        visibleIds.has(e.target)
    );
    return { nodes: visibleNodes, edges: visibleEdges };
  }, [data, filters.nodeTypes, filters.linkTypes]);

  // Build React Flow nodes
  const rawNodes: Node[] = useMemo(
    () =>
      filtered.nodes.map((n) => ({
        id: n.id,
        type: "ontology",
        position: { x: 0, y: 0 },
        data: {
          label: (n.data.label as string) ?? n.id,
          type: n.type,
        },
      })),
    [filtered.nodes]
  );

  // Build React Flow edges
  const flowEdges: Edge[] = useMemo(
    () =>
      filtered.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: filters.showLabels ? e.label.replace(/_/g, " ") : undefined,
        animated: false,
        style: { stroke: "#334155", strokeWidth: 1.5 },
        labelStyle: {
          fill: "#64748b",
          fontSize: 9,
          fontFamily: "Space Grotesk",
        },
        labelBgStyle: { fill: "#020617", fillOpacity: 0.9 },
      })),
    [filtered.edges, filters.showLabels]
  );

  // Apply layout
  const layoutNodes = useMemo(() => {
    if (rawNodes.length === 0) return rawNodes;
    if (filters.layout === "dagre-lr") return layoutDagre(rawNodes, flowEdges, "LR");
    if (filters.layout === "dagre-tb") return layoutDagre(rawNodes, flowEdges, "TB");
    return layoutRadial(rawNodes);
  }, [rawNodes, flowEdges, filters.layout]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  );

  return (
    <div className="w-full h-[600px] bg-surface border border-outline">
      <ReactFlow
        nodes={layoutNodes}
        edges={flowEdges}
        onNodeClick={handleNodeClick}
        nodesDraggable={false}
        nodesConnectable={false}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
        minZoom={0.1}
        maxZoom={2}
      >
        <Background color="#1e293b" gap={40} size={1} />
        <Controls
          style={{
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: "4px",
          }}
        />
        <MiniMap
          style={{ background: "#0f172a", border: "1px solid #334155" }}
          nodeColor={(n) => (TYPE_COLORS[n.data?.type as string] ?? DEFAULT_COLOR).border}
          maskColor="rgba(2, 6, 23, 0.8)"
        />
      </ReactFlow>
    </div>
  );
}
