import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Import after mocking
import { api } from "../lib/api";

describe("api client", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("listObjects calls correct URL", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0 }),
    });

    const result = await api.listObjects({ type: "company" });

    expect(mockFetch).toHaveBeenCalledOnce();
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/objects");
    expect(url).toContain("type=company");
    expect(result.total).toBe(0);
  });

  it("getObject calls correct URL", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          id: "1",
          key: "apple",
          type: "company",
          properties: {},
          sources: {},
        }),
    });

    const result = await api.getObject("apple");

    expect(result.key).toBe("apple");
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/objects/apple");
  });

  it("search calls correct URL with params", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });

    await api.search("test query", "company");

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/search");
    expect(url).toContain("q=test+query");
    expect(url).toContain("type=company");
  });

  it("getGraph calls correct URL", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ nodes: [], edges: [] }),
    });

    const result = await api.getGraph("apple", 2);

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/graph");
    expect(url).toContain("root=apple");
    expect(url).toContain("depth=2");
    expect(result.nodes).toEqual([]);
  });

  it("triggerSync calls POST", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ status: "queued", source: "wikipedia" }),
    });

    const result = await api.triggerSync("wikipedia");

    expect(mockFetch).toHaveBeenCalledWith("/api/sync/wikipedia", {
      method: "POST",
    });
    expect(result.status).toBe("queued");
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
    });

    await expect(api.getObject("missing")).rejects.toThrow("API error");
  });
});
