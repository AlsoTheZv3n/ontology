import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useObjects(params?: { type?: string; missing?: string }) {
  return useQuery({
    queryKey: ["objects", params],
    queryFn: () => api.listObjects(params),
  });
}

export function useObject(key: string) {
  return useQuery({
    queryKey: ["object", key],
    queryFn: () => api.getObject(key),
    enabled: !!key,
  });
}

export function useObjectLinks(key: string) {
  return useQuery({
    queryKey: ["links", key],
    queryFn: () => api.getLinks(key),
    enabled: !!key,
  });
}

export function useTimeline(key: string) {
  return useQuery({
    queryKey: ["timeline", key],
    queryFn: () => api.getTimeline(key),
    enabled: !!key,
  });
}

export function useGraph(root: string, depth = 2) {
  return useQuery({
    queryKey: ["graph", root, depth],
    queryFn: () => api.getGraph(root, depth),
    enabled: !!root,
  });
}

export function useSearch(q: string, type?: string) {
  return useQuery({
    queryKey: ["search", q, type],
    queryFn: () => api.search(q, type),
    enabled: q.length > 0,
  });
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: api.getStats,
  });
}

export function useAnomalies() {
  return useQuery({
    queryKey: ["anomalies"],
    queryFn: api.getAnomalies,
  });
}

export function useTopCompanies(metric: string) {
  return useQuery({
    queryKey: ["top", metric],
    queryFn: () => api.getTop(metric),
  });
}

export function useTrending() {
  return useQuery({
    queryKey: ["trending"],
    queryFn: api.getTrending,
  });
}

export function useMovers() {
  return useQuery({
    queryKey: ["movers"],
    queryFn: api.getMovers,
  });
}

export function useSync() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (source: string) => api.triggerSync(source),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["objects"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}
