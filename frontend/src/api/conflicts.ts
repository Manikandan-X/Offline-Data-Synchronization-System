import { apiClient } from "./client";
import type { ConflictItem, ResolutionStrategy } from "@/types";

export const conflictsApi = {
  list: (limit = 100) =>
    apiClient.get<ConflictItem[]>("/conflicts", { params: { limit } }).then((r) => r.data),

  pending: (limit = 100) =>
    apiClient
      .get<ConflictItem[]>("/conflicts/pending", { params: { limit } })
      .then((r) => r.data),

  get: (id: number) => apiClient.get<ConflictItem>(`/conflicts/${id}`).then((r) => r.data),

  resolve: (
    id: number,
    payload: {
      resolution_strategy: ResolutionStrategy;
      resolution_notes?: string | null;
      resolution_data?: Record<string, unknown> | null;
    }
  ) => apiClient.post<ConflictItem>(`/conflicts/${id}/resolve`, payload).then((r) => r.data),
};
