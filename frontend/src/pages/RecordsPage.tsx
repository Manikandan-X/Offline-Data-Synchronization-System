import { useState } from "react";
import {
  Stack,
  Button,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  IconButton,
  Typography,
  Tooltip,
  Chip,
  Box,
} from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import CloudOffRoundedIcon from "@mui/icons-material/CloudOffRounded";
import CloudDoneRoundedIcon from "@mui/icons-material/CloudDoneRounded";
import StorageRoundedIcon from "@mui/icons-material/StorageRounded";
import { format } from "date-fns";
import { useSync } from "@/context/SyncContext";
import { useNotify } from "@/context/NotificationContext";
import { useRecords } from "@/hooks/useRecords";
import RecordFormDialog from "@/components/records/RecordFormDialog";
import EmptyState from "@/components/common/EmptyState";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import { colors, monoFont } from "@/theme/theme";
import type { RecordItem } from "@/types";

export default function RecordsPage() {
  const { isOnline } = useSync();
  const { records, loading, error, createRecord, updateRecord, deleteRecord } = useRecords(isOnline);
  const notify = useNotify();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<RecordItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<RecordItem | null>(null);
  const [deleting, setDeleting] = useState(false);

  const openCreate = () => {
    setEditing(null);
    setDialogOpen(true);
  };
  const openEdit = (record: RecordItem) => {
    setEditing(record);
    setDialogOpen(true);
  };

  const handleSubmit = async (data: Record<string, unknown>) => {
    if (editing) await updateRecord(editing, data);
    else await createRecord(data);
    notify(editing ? "Record updated." : "Record created.", "success");
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteRecord(deleteTarget);
      notify("Record deleted.", "success");
      setDeleteTarget(null);
    } catch {
      notify("Couldn't delete the record. Please try again.", "error");
    } finally {
      setDeleting(false);
    }
  };

  const previewOf = (data: Record<string, unknown>) => {
    const str = JSON.stringify(data);
    return str.length > 60 ? str.slice(0, 60) + "…" : str;
  };

  return (
    <Stack spacing={2.5}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="body2" color="text.secondary">
          {isOnline
            ? "Connected — changes sync immediately."
            : "Offline — changes are queued locally and will sync automatically once you're reconnected."}
        </Typography>
        <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={openCreate}>
          New record
        </Button>
      </Stack>

      <Paper>
        {records.length === 0 && !loading ? (
          <EmptyState
            icon={<StorageRoundedIcon fontSize="inherit" />}
            title="No records yet"
            description="Create your first record — it works the same whether you're online or offline."
            action={
              <Button variant="outlined" onClick={openCreate} startIcon={<AddRoundedIcon />}>
                New record
              </Button>
            }
          />
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Data preview</TableCell>
                <TableCell>Version</TableCell>
                <TableCell>Updated</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {records.map((record) => {
                const isPendingCreate = record.id < 0;
                return (
                  <TableRow key={record.id} hover>
                    <TableCell sx={{ fontFamily: monoFont }}>
                      {isPendingCreate ? "—" : `#${record.id}`}
                    </TableCell>
                    <TableCell sx={{ fontFamily: monoFont, color: "text.secondary" }}>
                      {previewOf(record.data)}
                    </TableCell>
                    <TableCell sx={{ fontFamily: monoFont }}>v{record.version}</TableCell>
                    <TableCell sx={{ color: "text.secondary" }}>
                      {format(new Date(record.updated_at), "MMM d, HH:mm")}
                    </TableCell>
                    <TableCell>
                      {isPendingCreate ? (
                        <Chip
                          icon={<CloudOffRoundedIcon sx={{ fontSize: 14 }} />}
                          label="Queued"
                          size="small"
                          sx={{ color: colors.pending, backgroundColor: "rgba(245,165,36,0.12)" }}
                        />
                      ) : (
                        <Chip
                          icon={<CloudDoneRoundedIcon sx={{ fontSize: 14 }} />}
                          label="Synced"
                          size="small"
                          sx={{ color: colors.synced, backgroundColor: "rgba(45,212,191,0.12)" }}
                        />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => openEdit(record)}>
                          <EditRoundedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton size="small" onClick={() => setDeleteTarget(record)}>
                          <DeleteRoundedIcon fontSize="small" sx={{ color: colors.failed }} />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Paper>

      {error && (
        <Box>
          <Typography variant="caption" color="text.secondary">
            {error}
          </Typography>
        </Box>
      )}

      <RecordFormDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleSubmit}
        record={editing}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete this record?"
        message={
          deleteTarget
            ? `This will permanently delete record ${
                deleteTarget.id > 0 ? `#${deleteTarget.id}` : "(not yet synced)"
              }. This action cannot be undone.`
            : ""
        }
        confirmLabel="Delete record"
        loading={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </Stack>
  );
}
