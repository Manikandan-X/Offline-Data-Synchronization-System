import { apiClient } from "./client";
import type { SyncOperation, OperationType } from "@/types";

export interface CreateSyncOperationPayload {
  operation_id: string;
  record_id: number | null;
  operation_type: OperationType;
  base_version: number;
  payload: Record<string, unknown> | null;
}

export const syncApi = {
  createOperation: (data: CreateSyncOperationPayload) =>
    apiClient.post<SyncOperation>("/sync/operations", data).then((r) => r.data),

  getPending: (limit = 100) =>
    apiClient
      .get<SyncOperation[]>("/sync/operations/pending", { params: { limit } })
      .then((r) => r.data),

  process: (operationId: string) =>
    apiClient
      .post<SyncOperation>(`/sync/operations/${operationId}/process`)
      .then((r) => r.data),
};
