import { syncApi } from "@/api/sync";
import { extractErrorMessage } from "@/api/client";
import {
  getPendingQueue,
  updateQueueEntry,
  removeQueueEntry,
  cacheRecord,
  deleteCachedRecord,
  setMeta,
} from "./indexedDb";
import type { LocalQueueEntry, RecordItem, SyncOperation } from "@/types";

export type SyncListener = (summary: SyncRunSummary) => void;

export interface SyncRunSummary {
  processed: number;
  succeeded: number;
  failed: number;
  conflicts: number;
  ranAt: string;
}

const listeners = new Set<SyncListener>();
let isRunning = false;

export function onSyncRun(listener: SyncListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function notify(summary: SyncRunSummary) {
  listeners.forEach((l) => l(summary));
}

/**
 * Processes every PENDING/FAILED entry in the local queue, in FIFO order,
 * against the backend. On success the local record cache is reconciled with
 * the server's copy. On conflict, the operation is left in CONFLICT state
 * (a Conflict record now exists server-side) so the Conflicts page can
 * surface it for resolution — the queue entry is not silently dropped.
 */
export async function runSync(): Promise<SyncRunSummary> {
  if (isRunning) {
    return { processed: 0, succeeded: 0, failed: 0, conflicts: 0, ranAt: new Date().toISOString() };
  }

  isRunning = true;
  let succeeded = 0;
  let failed = 0;
  let conflicts = 0;

  try {
    const pending = await getPendingQueue();

    for (const entry of pending) {
      const result = await processSingleEntry(entry);
      if (result === "SUCCESS") succeeded += 1;
      else if (result === "CONFLICT") conflicts += 1;
      else failed += 1;
    }

    const summary: SyncRunSummary = {
      processed: pending.length,
      succeeded,
      failed,
      conflicts,
      ranAt: new Date().toISOString(),
    };

    if (pending.length > 0) {
      await setMeta("last_sync_at", summary.ranAt);
    }

    notify(summary);
    return summary;
  } finally {
    isRunning = false;
  }
}

async function processSingleEntry(
  entry: LocalQueueEntry
): Promise<"SUCCESS" | "FAILED" | "CONFLICT"> {
  try {
    // Step 1: ensure the operation exists server-side (idempotent — the
    // backend rejects a duplicate operation_id, which we treat as "already
    // registered" rather than an error).
    let remoteOp: SyncOperation | null = null;

    try {
      remoteOp = await syncApi.createOperation({
        operation_id: entry.operation_id,
        record_id: entry.record_id,
        operation_type: entry.operation_type,
        base_version: entry.base_version,
        payload: entry.payload,
      });
    } catch (err: any) {
      const status = err?.response?.status;
      if (status !== 409) throw err; // 409 = ConflictException "already exists" -> safe to continue
    }

    // Step 2: ask the server to apply it.
    const processed = await syncApi.process(entry.operation_id);

    if (processed.status === "SUCCESS") {
      await reconcileLocalRecord(entry, processed);
      await removeQueueEntry(entry.operation_id);
      return "SUCCESS";
    }

    if (processed.status === "CONFLICT") {
      await updateQueueEntry({
        ...entry,
        status: "CONFLICT",
        error_message: "Version conflict — resolve on the Conflicts page.",
      });
      return "CONFLICT";
    }

    // FAILED or PROCESSING (shouldn't linger) — bump attempt count.
    await updateQueueEntry({
      ...entry,
      status: "FAILED",
      attempt_count: entry.attempt_count + 1,
      error_message: processed.error_message || "Sync attempt failed.",
    });
    return "FAILED";
  } catch (err: any) {
    const status = err?.response?.status;

    if (status === 409) {
      // Conflict raised directly from /process
      await updateQueueEntry({
        ...entry,
        status: "CONFLICT",
        error_message: "Version conflict — resolve on the Conflicts page.",
      });
      return "CONFLICT";
    }

    await updateQueueEntry({
      ...entry,
      status: "FAILED",
      attempt_count: entry.attempt_count + 1,
      error_message: extractErrorMessage(err),
    });
    return "FAILED";
  }
}

async function reconcileLocalRecord(entry: LocalQueueEntry, op: SyncOperation): Promise<void> {
  if (entry.operation_type === "DELETE") {
    if (op.record_id) await deleteCachedRecord(op.record_id);
    return;
  }

  if (!op.record_id) return;

  const data = (entry.payload?.data as Record<string, unknown>) || {};
  const nowIso = new Date().toISOString();

  const reconciled: RecordItem = {
    id: op.record_id,
    owner_id: 0, // filled in properly on next full refetch; not needed for local display logic
    data,
    version: entry.base_version + 1,
    is_deleted: false,
    created_at: nowIso,
    updated_at: nowIso,
  };

  // If this was a CREATE that had a temporary local id, drop the temp entry.
  if (entry.local_record_id !== null && entry.local_record_id !== undefined) {
    await deleteCachedRecord(entry.local_record_id);
  }

  await cacheRecord(reconciled);
}
