import { useEffect, useRef, useMemo } from "react";
import cytoscape, { Core, NodeSingular } from "cytoscape";
import cola from "cytoscape-cola";
import fcose from "cytoscape-fcose";
import type { GraphResponse } from "@/lib/api";
import type { GraphFilters } from "./GraphFilterPanel";

cytoscape.use(cola);
cytoscape.use(fcose);

// ── Node styles per type ──

const NODE_STYLES: Record<string, { bg: string; border: string; shape: string }> = {
  company:    { bg: "#1e1b4b", border: "#818cf8", shape: "roundrectangle" },
  person:     { bg: "#0c1a2e", border: "#38bdf8", shape: "ellipse" },
  article:    { bg: "#1c1917", border: "#fb923c", shape: "rectangle" },
  repository: { bg: "#052e16", border: "#4ade80", shape: "roundrectangle" },
  event:      { bg: "#2d1b69", border: "#a78bfa", shape: "diamond" },
};

const EDGE_COLORS: Record<string, string> = {
  mentions:       "#fb923c",
  owns_repo:      "#4ade80",
  filed:          "#a78bfa",
  is_ceo_of:      "#38bdf8",
  contributed_to: "#34d399",
  competitor_of:  "#ef4444",
  invented:       "#f472b6",
  in_sector:      "#94a3b8",
};

// ── Layouts ──

const LAYOUTS: Record<string, object> = {
  force: {
    name: "fcose",
    quality: "default",
    randomize: true,
    animate: true,
    animationDuration: 600,
    nodeRepulsion: 8000,
    idealEdgeLength: 120,
    edgeElasticity: 0.45,
    numIter: 2500,
    fit: true,
    padding: 40,
  },
  cola: {
    name: "cola",
    animate: true,
    animationDuration: 600,
    maxSimulationTime: 2000,
    fit: true,
    padding: 40,
    nodeSpacing: 50,
    edgeLength: 150,
  },
  concentric: {
    name: "concentric",
    fit: true,
    padding: 40,
    minNodeSpacing: 40,
    concentric: (node: NodeSingular) => {
      const t = node.data("nodeType");
      return t === "company" ? 3 : t === "person" ? 2 : 1;
    },
    levelWidth: () => 2,
  },
  grid: {
    name: "grid",
    fit: true,
    padding: 40,
    avoidOverlap: true,
  },
};

// ── Component ──

interface GraphViewProps {
  data: GraphResponse;
  filters: GraphFilters;
  onNodeClick?: (key: string, type: string) => void;
}

export function GraphView({ data, filters, onNodeClick }: GraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  const elements = useMemo(() => {
    const visibleNodes = data.nodes.filter((n) => filters.nodeTypes.has(n.type));
    const visibleIds = new Set(visibleNodes.map((n) => n.id));
    const visibleEdges = data.edges.filter(
      (e) =>
        filters.linkTypes.has(e.label) &&
        visibleIds.has(e.source) &&
        visibleIds.has(e.target)
    );

    const connectedIds = new Set<string>();
    visibleEdges.forEach((e) => {
      connectedIds.add(e.source);
      connectedIds.add(e.target);
    });

    const nodes = visibleNodes
      .filter((n) => n.type === "company" || n.type === "person" || connectedIds.has(n.id))
      .map((n) => ({
        data: {
          id: n.id,
          label: ((n.data.label as string) ?? n.id).slice(0, 35),
          nodeType: n.type,
        },
      }));

    const nodeIds = new Set(nodes.map((n) => n.data.id));
    const edges = visibleEdges
      .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map((e) => ({
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          linkType: e.label,
          label: filters.showLabels ? e.label.replace(/_/g, " ") : "",
        },
      }));

    return [...nodes, ...edges];
  }, [data, filters.nodeTypes, filters.linkTypes, filters.showLabels]);

  const layoutKey = useMemo(() => {
    const map: Record<string, string> = {
      "dagre-lr": "cola",
      "dagre-tb": "concentric",
      "radial": "force",
      force: "force",
      cola: "cola",
      concentric: "concentric",
      grid: "grid",
    };
    return map[filters.layout] ?? "force";
  }, [filters.layout]);

  useEffect(() => {
    if (!containerRef.current || elements.length === 0) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#1e293b",
            "border-width": 2,
            "border-color": "#475569",
            label: "data(label)",
            color: "#f8fafc",
            "font-size": 11,
            "font-family": "Space Grotesk, sans-serif",
            "text-valign": "center",
            "text-halign": "center",
            "text-wrap": "ellipsis",
            "text-max-width": "120px",
            padding: "8px",
            "min-zoomed-font-size": 8,
          },
        },
        ...Object.entries(NODE_STYLES).map(([type, s]) => ({
          selector: `node[nodeType="${type}"]`,
          style: {
            "background-color": s.bg,
            "border-color": s.border,
            shape: s.shape as any,
            width: type === "company" ? 65 : type === "person" ? 50 : 40,
            height: type === "company" ? 65 : type === "person" ? 50 : 40,
          },
        })),
        {
          selector: "node[nodeType='company']",
          style: { "font-size": 13, "font-weight": "bold" as any },
        },
        {
          selector: "node:selected",
          style: { "border-width": 4, "border-color": "#ffffff" },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#334155",
            "target-arrow-color": "#334155",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "arrow-scale": 0.8,
            label: "data(label)",
            "font-size": 9,
            color: "#64748b",
            "text-rotation": "autorotate" as any,
            "text-margin-y": -8,
            "font-family": "Space Grotesk, sans-serif",
            "min-zoomed-font-size": 10,
          },
        },
        ...Object.entries(EDGE_COLORS).map(([type, color]) => ({
          selector: `edge[linkType="${type}"]`,
          style: { "line-color": color, "target-arrow-color": color },
        })),
        {
          selector: ".highlighted",
          style: { "border-color": "#ffffff", "border-width": 3, opacity: 1 },
        },
        {
          selector: ".faded",
          style: { opacity: 0.12 },
        },
      ],
    });

    cy.layout(LAYOUTS[layoutKey] as any).run();

    cy.on("tap", "node", (evt) => {
      const node = evt.target;
      onNodeClick?.(node.id(), node.data("nodeType"));
      cy.elements().addClass("faded");
      node.removeClass("faded").addClass("highlighted");
      node.neighborhood().removeClass("faded").addClass("highlighted");
    });

    cy.on("tap", (evt) => {
      if (evt.target === cy) {
        cy.elements().removeClass("faded highlighted");
      }
    });

    cyRef.current = cy;
    return () => cy.destroy();
  }, [elements, layoutKey, onNodeClick]);

  return (
    <div
      ref={containerRef}
      className="w-full bg-surface border border-outline"
      style={{ height: 640 }}
    />
  );
}
