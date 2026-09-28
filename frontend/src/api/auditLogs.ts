import { apiClient } from "./client";
import type { PaginatedAuditLogResponse } from "@/types";

export interface AuditLogSearchParams {
  action?: string;
  entity_type?: string;
  entity_id?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
  sort_order?: "asc" | "desc";
}

export const auditLogApi = {
  // Own activity — any authenticated user
  mine: (params: AuditLogSearchParams) =>
    apiClient
      .get<PaginatedAuditLogResponse>("/audit-logs", { params })
      .then((r) => r.data),

  // Every user's activity — admin only
  all: (params: AuditLogSearchParams) =>
    apiClient
      .get<PaginatedAuditLogResponse>("/audit-logs/all", { params })
      .then((r) => r.data),
};
