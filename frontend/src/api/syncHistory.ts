import { apiClient } from "./client";
import type { SyncHistoryItem } from "@/types";

export const syncHistoryApi = {
  list: (limit = 100) =>
    apiClient
      .get<SyncHistoryItem[]>("/sync-history", { params: { limit } })
      .then((r) => r.data),
};
