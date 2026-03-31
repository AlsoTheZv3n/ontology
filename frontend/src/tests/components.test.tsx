import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { SourceBadge } from "../components/SourceBadge";
import { ObjectCard } from "../components/ObjectCard";

describe("SourceBadge", () => {
  it("renders source name", () => {
    render(<SourceBadge source="wikipedia" />);
    expect(screen.getByText("wikipedia")).toBeInTheDocument();
  });

  it("replaces underscore with space", () => {
    render(<SourceBadge source="yahoo_finance" />);
    expect(screen.getByText("yahoo finance")).toBeInTheDocument();
  });
});

describe("ObjectCard", () => {
  const mockObject = {
    id: "test-id",
    type: "company",
    key: "apple",
    properties: {
      name: "Apple Inc.",
      description: "A technology company",
    },
    sources: { wikipedia: {}, github: {} },
    created_at: "2026-01-01T00:00:00",
    updated_at: "2026-01-01T00:00:00",
  };

  it("renders object name", () => {
    render(
      <BrowserRouter>
        <ObjectCard object={mockObject} />
      </BrowserRouter>
    );
    expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
  });

  it("renders description", () => {
    render(
      <BrowserRouter>
        <ObjectCard object={mockObject} />
      </BrowserRouter>
    );
    expect(screen.getByText("A technology company")).toBeInTheDocument();
  });

  it("renders source badges", () => {
    render(
      <BrowserRouter>
        <ObjectCard object={mockObject} />
      </BrowserRouter>
    );
    expect(screen.getByText("wikipedia")).toBeInTheDocument();
    expect(screen.getByText("github")).toBeInTheDocument();
  });

  it("links to company page for company type", () => {
    render(
      <BrowserRouter>
        <ObjectCard object={mockObject} />
      </BrowserRouter>
    );
    const link = screen.getByRole("link");
    expect(link.getAttribute("href")).toBe("/company/apple");
  });

  it("links to graph page for non-company type", () => {
    render(
      <BrowserRouter>
        <ObjectCard object={{ ...mockObject, type: "person" }} />
      </BrowserRouter>
    );
    const link = screen.getByRole("link");
    expect(link.getAttribute("href")).toBe("/graph/apple");
  });

  it("uses key as name fallback", () => {
    render(
      <BrowserRouter>
        <ObjectCard
          object={{ ...mockObject, properties: {} }}
        />
      </BrowserRouter>
    );
    expect(screen.getByText("apple")).toBeInTheDocument();
  });
});
