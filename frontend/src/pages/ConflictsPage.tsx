import { useEffect, useState } from "react";
import {
  Stack,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Typography,
  Button,
  Tabs,
  Tab,
  Alert,
  Tooltip,
} from "@mui/material";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import { format } from "date-fns";
import { conflictsApi } from "@/api/conflicts";
import { extractErrorMessage } from "@/api/client";
import ConflictResolutionDialog from "@/components/conflicts/ConflictResolutionDialog";
import StatusChip from "@/components/common/StatusChip";
import EmptyState from "@/components/common/EmptyState";
import { monoFont } from "@/theme/theme";
import { useSync } from "@/context/SyncContext";
import { useNotify } from "@/context/NotificationContext";
import { getQueue, removeQueueEntry, cacheRecord } from "@/db/indexedDb";
import type { ConflictItem, ResolutionStrategy } from "@/types";

export default function ConflictsPage() {
  const { isOnline, refreshQueue } = useSync();
  const notify = useNotify();
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [tab, setTab] = useState<"pending" | "all">("pending");
  const [selected, setSelected] = useState<ConflictItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    if (!isOnline) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = tab === "pending" ? await conflictsApi.pending() : await conflictsApi.list();
      setConflicts(data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, isOnline]);

  const handleResolve = async (
    strategy: ResolutionStrategy,
    notes: string,
    manualData: Record<string, unknown> | null
  ) => {
    if (!selected) return;

    const resolved = await conflictsApi.resolve(selected.id, {
      resolution_strategy: strategy,
      resolution_notes: notes || null,
      resolution_data: strategy === "MANUAL" ? manualData : null,
    });

    // Clean up the matching local queue entry (left in CONFLICT status)
    // and refresh the local record cache to the newly resolved version.
    const queue = await getQueue();
    const stuck = queue.find(
      (q) => q.status === "CONFLICT" && q.record_id === selected.record_id
    );
    if (stuck) await removeQueueEntry(stuck.operation_id);

    const winningData =
      strategy === "MANUAL"
        ? manualData
        : strategy === "SERVER_WINS"
        ? selected.server_data
        : strategy === "CLIENT_WINS"
        ? selected.client_data
        : selected.server_version >= selected.client_version
        ? selected.server_data
        : selected.client_data;

    await cacheRecord({
      id: selected.record_id,
      owner_id: 0,
      data: winningData || {},
      version: Math.max(selected.server_version, selected.client_version) + 1,
      is_deleted: false,
      created_at: resolved.updated_at,
      updated_at: resolved.updated_at,
    });

    await refreshQueue();
    await load();
    notify(`Conflict resolved using ${strategy.replace(/_/g, " ").toLowerCase()}.`, "success");
  };

  return (
    <Stack spacing={2.5}>
      {!isOnline && (
        <Alert severity="warning">
          Conflicts are resolved on the server, so this page needs a connection. You're currently
          offline.
        </Alert>
      )}

      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab value="pending" label="Pending" />
          <Tab value="all" label="All conflicts" />
        </Tabs>
        <Button variant="outlined" onClick={load} disabled={!isOnline || loading}>
          Refresh
        </Button>
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}

      <Paper>
        {conflicts.length === 0 && !loading ? (
          <EmptyState
            icon={<WarningAmberRoundedIcon fontSize="inherit" />}
            title={tab === "pending" ? "No pending conflicts" : "No conflicts recorded"}
            description="When the same record is changed both locally and on the server, it will show up here for resolution."
          />
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Record</TableCell>
                <TableCell>Client v.</TableCell>
                <TableCell>Server v.</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Strategy used</TableCell>
                <TableCell>Notes</TableCell>
                <TableCell>Detected</TableCell>
                <TableCell align="right">Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {conflicts.map((c) => (
                <TableRow key={c.id} hover>
                  <TableCell sx={{ fontFamily: monoFont }}>#{c.record_id}</TableCell>
                  <TableCell sx={{ fontFamily: monoFont }}>v{c.client_version}</TableCell>
                  <TableCell sx={{ fontFamily: monoFont }}>v{c.server_version}</TableCell>
                  <TableCell>
                    <StatusChip status={c.resolution_status} />
                  </TableCell>
                  <TableCell sx={{ color: "text.secondary" }}>{c.resolution_strategy || "—"}</TableCell>
                  <TableCell sx={{ color: "text.secondary", maxWidth: 200 }}>
                    {c.resolution_notes ? (
                      <Tooltip title={c.resolution_notes}>
                        <span>
                          {c.resolution_notes.length > 30
                            ? c.resolution_notes.slice(0, 30) + "…"
                            : c.resolution_notes}
                        </span>
                      </Tooltip>
                    ) : (
                      "—"
                    )}
                  </TableCell>
                  <TableCell sx={{ color: "text.secondary" }}>
                    {format(new Date(c.created_at), "MMM d, HH:mm")}
                  </TableCell>
                  <TableCell align="right">
                    {c.resolution_status === "PENDING" ? (
                      <Button size="small" variant="contained" onClick={() => setSelected(c)}>
                        Resolve
                      </Button>
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        Resolved {format(new Date(c.updated_at), "MMM d, HH:mm")}
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      <ConflictResolutionDialog
        open={!!selected}
        conflict={selected}
        onClose={() => setSelected(null)}
        onResolve={handleResolve}
      />
    </Stack>
  );
}
