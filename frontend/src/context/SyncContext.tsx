import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { useNetworkStatus } from "@/hooks/useNetworkStatus";
import { runSync, onSyncRun, type SyncRunSummary } from "@/db/syncEngine";
import { getQueue, getMeta } from "@/db/indexedDb";
import type { LocalQueueEntry } from "@/types";

interface SyncContextValue {
  isOnline: boolean;
  syncing: boolean;
  queue: LocalQueueEntry[];
  pendingCount: number;
  conflictCount: number;
  failedCount: number;
  lastSyncAt: string | null;
  lastSummary: SyncRunSummary | null;
  refreshQueue: () => Promise<void>;
  triggerSync: () => Promise<void>;
}

const SyncContext = createContext<SyncContextValue | undefined>(undefined);

const AUTO_SYNC_INTERVAL_MS = 20000;

export function SyncProvider({ children }: { children: ReactNode }) {
  const { isOnline } = useNetworkStatus();
  const [queue, setQueue] = useState<LocalQueueEntry[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [lastSyncAt, setLastSyncAt] = useState<string | null>(null);
  const [lastSummary, setLastSummary] = useState<SyncRunSummary | null>(null);
  const wasOffline = useRef(false);

  const refreshQueue = useCallback(async () => {
    const q = await getQueue();
    setQueue(q);
    const last = await getMeta<string>("last_sync_at");
    if (last) setLastSyncAt(last);
  }, []);

  const triggerSync = useCallback(async () => {
    setSyncing(true);
    try {
      await runSync();
    } finally {
      setSyncing(false);
      await refreshQueue();
    }
  }, [refreshQueue]);

  // Load queue on mount
  useEffect(() => {
    refreshQueue();
  }, [refreshQueue]);

  // Listen for sync engine completions from anywhere in the app
  useEffect(() => {
    return onSyncRun((summary) => {
      setLastSummary(summary);
      setLastSyncAt(summary.ranAt);
      refreshQueue();
    });
  }, [refreshQueue]);

  // Auto-trigger a sync the moment connectivity is restored
  useEffect(() => {
    if (isOnline && wasOffline.current) {
      triggerSync();
    }
    wasOffline.current = !isOnline;
  }, [isOnline, triggerSync]);

  // Background polling sync loop while online
  useEffect(() => {
    if (!isOnline) return;
    const interval = setInterval(() => {
      triggerSync();
    }, AUTO_SYNC_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [isOnline, triggerSync]);

  const pendingCount = queue.filter((q) => q.status === "PENDING" || q.status === "FAILED").length;
  const conflictCount = queue.filter((q) => q.status === "CONFLICT").length;
  const failedCount = queue.filter((q) => q.status === "FAILED").length;

  return (
    <SyncContext.Provider
      value={{
        isOnline,
        syncing,
        queue,
        pendingCount,
        conflictCount,
        failedCount,
        lastSyncAt,
        lastSummary,
        refreshQueue,
        triggerSync,
      }}
    >
      {children}
    </SyncContext.Provider>
  );
}

export function useSync(): SyncContextValue {
  const ctx = useContext(SyncContext);
  if (!ctx) throw new Error("useSync must be used within SyncProvider");
  return ctx;
}
