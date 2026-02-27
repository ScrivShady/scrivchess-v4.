import { z } from 'zod';
import { insertAnalysisSchema, analyses, analyzeRequestSchema } from './schema';

export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  notFound: z.object({
    message: z.string(),
  }),
  internal: z.object({
    message: z.string(),
  }),
};

export const api = {
  analyses: {
    list: {
      method: 'GET' as const,
      path: '/api/analyses' as const,
      responses: {
        200: z.array(z.custom<typeof analyses.$inferSelect>()),
      },
    },
    get: {
      method: 'GET' as const,
      path: '/api/analyses/:id' as const,
      responses: {
        200: z.custom<typeof analyses.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/analyses' as const,
      input: analyzeRequestSchema,
      responses: {
        201: z.custom<typeof analyses.$inferSelect>(),
        400: errorSchemas.validation,
        500: errorSchemas.internal,
      },
    },
  },
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}

export type AnalyzeRequest = z.infer<typeof api.analyses.create.input>;
export type AnalysisResponse = z.infer<typeof api.analyses.create.responses[201]>;
export type AnalysesListResponse = z.infer<typeof api.analyses.list.responses[200]>;
