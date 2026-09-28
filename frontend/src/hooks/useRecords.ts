import { useCallback, useEffect, useState } from "react";
import { recordsApi } from "@/api/records";
import {
  getCachedRecords,
  cacheRecords,
  cacheRecord,
  deleteCachedRecord,
  enqueueOperation,
  generateOperationId,
  getQueue,
  removeQueueEntry,
} from "@/db/indexedDb";
import { runSync } from "@/db/syncEngine";
import type { RecordItem } from "@/types";

let tempIdCounter = 0;
function nextTempId(): number {
  tempIdCounter -= 1;
  return -(Date.now() * 1000 + Math.abs(tempIdCounter));
}

export function useRecords(isOnline: boolean) {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadFromCache = useCallback(async () => {
    const cached = await getCachedRecords();
    setRecords(cached);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (isOnline) {
        const res = await recordsApi.list(1, 100);
        await cacheRecords(res.items);
      }
      await loadFromCache();
    } catch {
      setError("Couldn't reach the server — showing your last synced copy.");
      await loadFromCache();
    } finally {
      setLoading(false);
    }
  }, [isOnline, loadFromCache]);

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOnline]);

  const createRecord = useCallback(
    async (data: Record<string, unknown>) => {
      const tempId = nextTempId();
      const nowIso = new Date().toISOString();
      const optimistic: RecordItem = {
        id: tempId,
        owner_id: 0,
        data,
        version: 1,
        is_deleted: false,
        created_at: nowIso,
        updated_at: nowIso,
      };
      await cacheRecord(optimistic);
      await enqueueOperation({
        operation_id: generateOperationId(),
        record_id: null,
        local_record_id: tempId,
        operation_type: "CREATE",
        base_version: 0,
        payload: { data },
        status: "PENDING",
        attempt_count: 0,
        error_message: null,
        created_at: nowIso,
      });
      await loadFromCache();
      if (isOnline) await runSync();
      await loadFromCache();
    },
    [isOnline, loadFromCache]
  );

  const updateRecord = useCallback(
    async (record: RecordItem, data: Record<string, unknown>) => {
      const nowIso = new Date().toISOString();
      const optimistic: RecordItem = { ...record, data, updated_at: nowIso };
      await cacheRecord(optimistic);
      await enqueueOperation({
        operation_id: generateOperationId(),
        record_id: record.id > 0 ? record.id : null,
        local_record_id: record.id < 0 ? record.id : null,
        operation_type: "UPDATE",
        base_version: record.version,
        payload: { data },
        status: "PENDING",
        attempt_count: 0,
        error_message: null,
        created_at: nowIso,
      });
      await loadFromCache();
      if (isOnline) await runSync();
      await loadFromCache();
    },
    [isOnline, loadFromCache]
  );

  const deleteRecord = useCallback(
    async (record: RecordItem) => {
      await deleteCachedRecord(record.id);

      if (record.id < 0) {
        // Never reached the server — just drop the pending CREATE operation.
        const queue = await getQueue();
        const pendingCreate = queue.find(
          (q) => q.local_record_id === record.id && q.operation_type === "CREATE"
        );
        if (pendingCreate) await removeQueueEntry(pendingCreate.operation_id);
        await loadFromCache();
        return;
      }

      const nowIso = new Date().toISOString();
      await enqueueOperation({
        operation_id: generateOperationId(),
        record_id: record.id,
        local_record_id: null,
        operation_type: "DELETE",
        base_version: record.version,
        payload: null,
        status: "PENDING",
        attempt_count: 0,
        error_message: null,
        created_at: nowIso,
      });
      await loadFromCache();
      if (isOnline) await runSync();
      await loadFromCache();
    },
    [isOnline, loadFromCache]
  );

  return { records, loading, error, refresh, createRecord, updateRecord, deleteRecord };
}
