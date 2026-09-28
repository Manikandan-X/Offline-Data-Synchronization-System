import { useEffect, useState, useCallback } from "react";
import { apiClient } from "@/api/client";

/**
 * Tracks real connectivity to the backend, not just navigator.onLine.
 * navigator.onLine only reflects the network interface state (it can be
 * true even when the API is unreachable), so we back it up with a
 * lightweight periodic health check and browser online/offline events.
 */
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [checking, setChecking] = useState(false);

  const checkConnection = useCallback(async () => {
    setChecking(true);
    try {
      await apiClient.get("/health", { timeout: 4000 });
      setIsOnline(true);
    } catch {
      setIsOnline(false);
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    const handleOnline = () => checkConnection();
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    checkConnection();
    const interval = setInterval(checkConnection, 15000);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      clearInterval(interval);
    };
  }, [checkConnection]);

  return { isOnline, checking, checkConnection };
}
