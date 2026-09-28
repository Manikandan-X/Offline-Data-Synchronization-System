import { apiClient } from "./client";
import type { PaginatedResponse, RecordItem } from "@/types";

export const recordsApi = {
  list: (page: number, pageSize: number) =>
    apiClient
      .get<PaginatedResponse<RecordItem>>("/records", {
        params: { page, page_size: pageSize },
      })
      .then((r) => r.data),

  get: (id: number) => apiClient.get<RecordItem>(`/records/${id}`).then((r) => r.data),

  // Direct (online) calls — used opportunistically by the sync engine equivalent
  // endpoints, but normal user mutations always go through the local queue
  // (see db/syncEngine.ts) so they work offline too.
  create: (data: Record<string, unknown>) =>
    apiClient.post<RecordItem>("/records", { data }).then((r) => r.data),

  update: (id: number, data: Record<string, unknown>) =>
    apiClient.put<RecordItem>(`/records/${id}`, { data }).then((r) => r.data),

  remove: (id: number) => apiClient.delete<RecordItem>(`/records/${id}`).then((r) => r.data),
};
