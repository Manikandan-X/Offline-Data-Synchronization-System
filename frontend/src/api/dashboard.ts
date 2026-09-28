import { apiClient } from "./client";
import type { SyncDashboard, PaginatedResponse, SyncOperation } from "@/types";

export interface SyncOperationSearchParams {
  operation_id?: string;
  status?: string;
  operation_type?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export const dashboardApi = {
  stats: () => apiClient.get<SyncDashboard>("/dashboard/sync-statistics").then((r) => r.data),

  searchOperations: (params: SyncOperationSearchParams) =>
    apiClient
      .get<PaginatedResponse<SyncOperation>>("/dashboard/sync-operations", { params })
      .then((r) => r.data),
};
