import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  GraphFilterPanel,
  defaultFilters,
  ALL_NODE_TYPES,
  ALL_LINK_TYPES,
} from "../components/GraphFilterPanel";
import type { GraphFilters } from "../components/GraphFilterPanel";

describe("defaultFilters", () => {
  it("includes all node types", () => {
    const f = defaultFilters();
    ALL_NODE_TYPES.forEach((t) => expect(f.nodeTypes.has(t)).toBe(true));
  });

  it("includes all link types", () => {
    const f = defaultFilters();
    ALL_LINK_TYPES.forEach((t) => expect(f.linkTypes.has(t)).toBe(true));
  });

  it("defaults to dagre-lr layout", () => {
    expect(defaultFilters().layout).toBe("dagre-lr");
  });

  it("defaults to show labels", () => {
    expect(defaultFilters().showLabels).toBe(true);
  });
});

describe("GraphFilterPanel", () => {
  it("renders all node type toggles", () => {
    const setFilters = vi.fn();
    render(
      <GraphFilterPanel
        filters={defaultFilters()}
        setFilters={setFilters}
        stats={{ nodes: 10, edges: 5, byType: { company: 3, article: 7 } }}
      />
    );

    ALL_NODE_TYPES.forEach((type) => {
      expect(screen.getByText(type)).toBeInTheDocument();
    });
  });

  it("renders all link type toggles", () => {
    const setFilters = vi.fn();
    render(
      <GraphFilterPanel
        filters={defaultFilters()}
        setFilters={setFilters}
      />
    );

    ALL_LINK_TYPES.forEach((type) => {
      expect(
        screen.getByText(type.replace(/_/g, " "))
      ).toBeInTheDocument();
    });
  });

  it("renders layout options", () => {
    render(
      <GraphFilterPanel
        filters={defaultFilters()}
        setFilters={vi.fn()}
      />
    );

    expect(screen.getByText("Horizontal")).toBeInTheDocument();
    expect(screen.getByText("Vertical")).toBeInTheDocument();
    expect(screen.getByText("Radial")).toBeInTheDocument();
  });

  it("renders stats when provided", () => {
    render(
      <GraphFilterPanel
        filters={defaultFilters()}
        setFilters={vi.fn()}
        stats={{ nodes: 42, edges: 15, byType: {} }}
      />
    );

    expect(screen.getByText("42 nodes")).toBeInTheDocument();
    expect(screen.getByText("15 edges")).toBeInTheDocument();
  });

  it("calls setFilters when node type toggled", () => {
    const setFilters = vi.fn();
    render(
      <GraphFilterPanel
        filters={defaultFilters()}
        setFilters={setFilters}
      />
    );

    fireEvent.click(screen.getByText("article"));
    expect(setFilters).toHaveBeenCalled();
  });

  it("calls setFilters when layout changed", () => {
    const setFilters = vi.fn();
    render(
      <GraphFilterPanel
        filters={defaultFilters()}
        setFilters={setFilters}
      />
    );

    fireEvent.click(screen.getByText("Vertical"));
    expect(setFilters).toHaveBeenCalled();
  });
});
