import { openDB, type DBSchema, type IDBPDatabase } from "idb";
import type { LocalQueueEntry, RecordItem } from "@/types";

const DB_NAME = "syncgrid_offline_db";
const DB_VERSION = 1;

interface SyncGridDB extends DBSchema {
  records: {
    key: number | string; // server id, or "local:<uuid>" before it is created
    value: RecordItem & { local_id?: string; pending_delete?: boolean };
    indexes: { "by-updated": string };
  };
  queue: {
    key: string; // operation_id
    value: LocalQueueEntry;
    indexes: { "by-status": string; "by-created": string };
  };
  meta: {
    key: string;
    value: { key: string; value: unknown };
  };
}

let dbPromise: Promise<IDBPDatabase<SyncGridDB>> | null = null;

export function getDb(): Promise<IDBPDatabase<SyncGridDB>> {
  if (!dbPromise) {
    dbPromise = openDB<SyncGridDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains("records")) {
          const store = db.createObjectStore("records", { keyPath: "id" });
          store.createIndex("by-updated", "updated_at");
        }
        if (!db.objectStoreNames.contains("queue")) {
          const store = db.createObjectStore("queue", { keyPath: "operation_id" });
          store.createIndex("by-status", "status");
          store.createIndex("by-created", "created_at");
        }
        if (!db.objectStoreNames.contains("meta")) {
          db.createObjectStore("meta", { keyPath: "key" });
        }
      },
    });
  }
  return dbPromise;
}

// ---------------- Records cache ----------------

export async function cacheRecords(records: RecordItem[]): Promise<void> {
  const db = await getDb();
  const tx = db.transaction("records", "readwrite");
  await Promise.all(records.map((r) => tx.store.put(r)));
  await tx.done;
}

export async function cacheRecord(record: RecordItem): Promise<void> {
  const db = await getDb();
  await db.put("records", record);
}

export async function getCachedRecords(): Promise<RecordItem[]> {
  const db = await getDb();
  const all = await db.getAll("records");
  return all.filter((r) => !r.is_deleted).sort((a, b) => b.id - a.id);
}

export async function deleteCachedRecord(id: number): Promise<void> {
  const db = await getDb();
  await db.delete("records", id);
}

// ---------------- Sync queue ----------------

export async function enqueueOperation(entry: LocalQueueEntry): Promise<void> {
  const db = await getDb();
  await db.put("queue", entry);
}

export async function updateQueueEntry(entry: LocalQueueEntry): Promise<void> {
  const db = await getDb();
  await db.put("queue", entry);
}

export async function getQueue(): Promise<LocalQueueEntry[]> {
  const db = await getDb();
  const all = await db.getAll("queue");
  return all.sort((a, b) => a.created_at.localeCompare(b.created_at));
}

export async function getPendingQueue(): Promise<LocalQueueEntry[]> {
  const all = await getQueue();
  return all.filter((e) => e.status === "PENDING" || e.status === "FAILED");
}

export async function removeQueueEntry(operationId: string): Promise<void> {
  const db = await getDb();
  await db.delete("queue", operationId);
}

// ---------------- Meta (last sync time, etc.) ----------------

export async function setMeta(key: string, value: unknown): Promise<void> {
  const db = await getDb();
  await db.put("meta", { key, value });
}

export async function getMeta<T = unknown>(key: string): Promise<T | undefined> {
  const db = await getDb();
  const row = await db.get("meta", key);
  return row?.value as T | undefined;
}

export async function clearAllOfflineData(): Promise<void> {
  const db = await getDb();
  await Promise.all([
    db.clear("records"),
    db.clear("queue"),
    db.clear("meta"),
  ]);
}

export function generateOperationId(): string {
  return `op_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

export function generateLocalRecordId(): string {
  return `local_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}
