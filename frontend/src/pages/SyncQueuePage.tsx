import { Stack, Paper, Table, TableHead, TableRow, TableCell, TableBody, Typography, Button, Box } from "@mui/material";
import SyncRoundedIcon from "@mui/icons-material/SyncRounded";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";
import { format } from "date-fns";
import { useSync } from "@/context/SyncContext";
import StatusChip from "@/components/common/StatusChip";
import EmptyState from "@/components/common/EmptyState";
import { monoFont } from "@/theme/theme";

export default function SyncQueuePage() {
  const { queue, isOnline, syncing, triggerSync } = useSync();

  return (
    <Stack spacing={2.5}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="body2" color="text.secondary">
          Local operations captured while working — including offline. They're applied to the
          server in the order they were created, and re-queued automatically on failure.
        </Typography>
        <Button
          variant="contained"
          startIcon={<SyncRoundedIcon />}
          onClick={() => triggerSync()}
          disabled={!isOnline || syncing}
        >
          {syncing ? "Syncing…" : "Sync now"}
        </Button>
      </Stack>

      <Paper>
        {queue.length === 0 ? (
          <EmptyState
            icon={<CheckCircleOutlineRoundedIcon fontSize="inherit" />}
            title="Queue is empty"
            description="Every local change has been synchronized with the server."
          />
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Operation ID</TableCell>
                <TableCell>Record</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Base version</TableCell>
                <TableCell>Attempts</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Details</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {queue.map((entry) => (
                <TableRow key={entry.operation_id} hover>
                  <TableCell sx={{ fontFamily: monoFont, fontSize: "0.78rem" }}>
                    {entry.operation_id}
                  </TableCell>
                  <TableCell sx={{ fontFamily: monoFont }}>
                    {entry.record_id ? `#${entry.record_id}` : entry.local_record_id ? "new" : "—"}
                  </TableCell>
                  <TableCell>{entry.operation_type}</TableCell>
                  <TableCell sx={{ fontFamily: monoFont }}>{entry.base_version}</TableCell>
                  <TableCell sx={{ fontFamily: monoFont }}>{entry.attempt_count}</TableCell>
                  <TableCell sx={{ color: "text.secondary" }}>
                    {format(new Date(entry.created_at), "MMM d, HH:mm:ss")}
                  </TableCell>
                  <TableCell>
                    <StatusChip status={entry.status} />
                  </TableCell>
                  <TableCell sx={{ color: "text.secondary", maxWidth: 220 }}>
                    {entry.error_message || "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      {!isOnline && (
        <Box>
          <Typography variant="caption" color="text.secondary">
            You're offline — queued operations will sync automatically the moment your connection is restored.
          </Typography>
        </Box>
      )}
    </Stack>
  );
}
