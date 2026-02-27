import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl, type AnalyzeRequest } from "@shared/routes";
import { z } from "zod";

function parseWithLogging<T>(schema: z.ZodSchema<T>, data: unknown, label: string): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    console.error(`[Zod] ${label} validation failed:`, result.error.format());
    throw new Error(`Data validation failed for ${label}`);
  }
  return result.data;
}

export function useAnalyses() {
  return useQuery({
    queryKey: [api.analyses.list.path],
    queryFn: async () => {
      const res = await fetch(api.analyses.list.path, { credentials: "include" });
      if (!res.ok) throw new Error('Failed to fetch analyses');
      const data = await res.json();
      return parseWithLogging(api.analyses.list.responses[200], data, "analyses.list");
    },
  });
}

export function useAnalysis(id: number | null) {
  return useQuery({
    queryKey: [api.analyses.get.path, id],
    queryFn: async () => {
      if (id === null) return null;
      const url = buildUrl(api.analyses.get.path, { id });
      const res = await fetch(url, { credentials: "include" });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error('Failed to fetch analysis');
      const data = await res.json();
      return parseWithLogging(api.analyses.get.responses[200], data, "analyses.get");
    },
    enabled: id !== null,
  });
}

export function useCreateAnalysis() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: AnalyzeRequest) => {
      const validated = api.analyses.create.input.parse(data);
      const res = await fetch(api.analyses.create.path, {
        method: api.analyses.create.method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(validated),
        credentials: "include",
      });
      
      if (!res.ok) {
        if (res.status === 400) {
          const error = parseWithLogging(api.analyses.create.responses[400], await res.json(), "analyses.create.400");
          throw new Error(error.message || 'Validation failed');
        }
        if (res.status === 500) {
          const error = parseWithLogging(api.analyses.create.responses[500], await res.json(), "analyses.create.500");
          throw new Error(error.message || 'Internal server error');
        }
        throw new Error('Failed to create analysis');
      }
      
      const responseData = await res.json();
      return parseWithLogging(api.analyses.create.responses[201], responseData, "analyses.create.201");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.analyses.list.path] });
    },
  });
}
