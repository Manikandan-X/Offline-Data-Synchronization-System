import { useEffect, useState } from "react";
import {
  Stack,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TextField,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  Pagination,
  Typography,
  Alert,
  ToggleButtonGroup,
  ToggleButton,
  Box,
  Chip,
} from "@mui/material";
import HistoryEduRoundedIcon from "@mui/icons-material/HistoryEduRounded";
import { format } from "date-fns";
import { auditLogApi } from "@/api/auditLogs";
import { extractErrorMessage } from "@/api/client";
import EmptyState from "@/components/common/EmptyState";
import { monoFont, colors } from "@/theme/theme";
import { useAuth } from "@/context/AuthContext";
import type { AuditLogItem } from "@/types";

const PAGE_SIZE = 15;

const ACTION_OPTIONS = [
  "USER_CREATED",
  "USER_UPDATED",
  "USER_ROLE_CHANGED",
  "USER_ACTIVATED",
  "USER_DEACTIVATED",
  "USER_DELETED",
  "USER_PASSWORD_CHANGED",
  "RECORD_CREATED",
  "RECORD_UPDATED",
  "RECORD_DELETED",
  "SYNC_OPERATION_CREATED",
  "SYNC_OPERATION_PROCESSED",
  "SYNC_OPERATION_FAILED",
  "SYNC_OPERATION_CONFLICT",
  "CONFLICT_CREATED",
  "CONFLICT_RESOLVED",
];

const ENTITY_OPTIONS = ["USER", "RECORD", "SYNC_OPERATION", "CONFLICT"];

function actionColor(action: string): string {
  if (action.includes("DELETED") || action.includes("FAILED")) return colors.failed;
  if (action.includes("CONFLICT")) return colors.conflict;
  if (action.includes("CREATED")) return colors.synced;
  if (action.includes("DEACTIVATED")) return colors.pending;
  return colors.processing;
}

function formatDetails(details: string | null): string {
  if (!details) return "—";
  try {
    const parsed = JSON.parse(details);
    return Object.entries(parsed)
      .map(([k, v]) => `${k}: ${v}`)
      .join(", ");
  } catch {
    return details;
  }
}

export default function AuditLogPage() {
  const { isAdmin } = useAuth();
  const [scope, setScope] = useState<"mine" | "all">("mine");
  const [items, setItems] = useState<AuditLogItem[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [entityId, setEntityId] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        action: action || undefined,
        entity_type: entityType || undefined,
        entity_id: entityId || undefined,
        from_date: fromDate ? new Date(fromDate).toISOString() : undefined,
        to_date: toDate ? new Date(toDate).toISOString() : undefined,
        page,
        page_size: PAGE_SIZE,
        sort_order: "desc" as const,
      };
      const res = scope === "all" ? await auditLogApi.all(params) : await auditLogApi.mine(params);
      setItems(res.items);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, scope]);

  const applyFilters = () => {
    setPage(1);
    load();
  };

  return (
    <Stack spacing={2.5}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="body2" color="text.secondary">
          {scope === "mine"
            ? "Every action taken on your account — profile edits, password changes, records, and syncs."
            : "Every action across every account in the workspace."}
        </Typography>
        {isAdmin && (
          <ToggleButtonGroup
            size="small"
            exclusive
            value={scope}
            onChange={(_, v) => {
              if (v) {
                setPage(1);
                setScope(v);
              }
            }}
          >
            <ToggleButton value="mine">My activity</ToggleButton>
            <ToggleButton value="all">All activity</ToggleButton>
          </ToggleButtonGroup>
        )}
      </Stack>

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" spacing={1.5} flexWrap="wrap" useFlexGap alignItems="center">
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Action</InputLabel>
            <Select label="Action" value={action} onChange={(e) => setAction(e.target.value)}>
              <MenuItem value="">All</MenuItem>
              {ACTION_OPTIONS.map((a) => (
                <MenuItem key={a} value={a}>
                  {a}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Entity type</InputLabel>
            <Select label="Entity type" value={entityType} onChange={(e) => setEntityType(e.target.value)}>
              <MenuItem value="">All</MenuItem>
              {ENTITY_OPTIONS.map((e) => (
                <MenuItem key={e} value={e}>
                  {e}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="Entity ID"
            size="small"
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            sx={{ width: 120 }}
          />
          <TextField
            label="From"
            type="date"
            size="small"
            InputLabelProps={{ shrink: true }}
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
          />
          <TextField
            label="To"
            type="date"
            size="small"
            InputLabelProps={{ shrink: true }}
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
          />
          <Box sx={{ ml: "auto" }}>
            <Typography
              variant="body2"
              sx={{ color: "primary.main", fontWeight: 600, cursor: "pointer" }}
              onClick={applyFilters}
            >
              Apply filters
            </Typography>
          </Box>
        </Stack>
      </Paper>

      {error && <Alert severity="error">{error}</Alert>}

      <Paper>
        {items.length === 0 && !loading ? (
          <EmptyState
            icon={<HistoryEduRoundedIcon fontSize="inherit" />}
            title="No matching activity"
            description="Actions like profile edits, record changes, and sync events will show up here."
          />
        ) : (
          <>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>When</TableCell>
                  {scope === "all" && <TableCell>User ID</TableCell>}
                  <TableCell>Action</TableCell>
                  <TableCell>Entity</TableCell>
                  <TableCell>Details</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((log) => (
                  <TableRow key={log.id} hover>
                    <TableCell sx={{ color: "text.secondary", whiteSpace: "nowrap" }}>
                      {format(new Date(log.created_at), "MMM d, HH:mm:ss")}
                    </TableCell>
                    {scope === "all" && (
                      <TableCell sx={{ fontFamily: monoFont }}>
                        {log.user_id ? `#${log.user_id}` : "—"}
                      </TableCell>
                    )}
                    <TableCell>
                      <Chip
                        label={log.action}
                        size="small"
                        sx={{
                          color: actionColor(log.action),
                          backgroundColor: "rgba(148,178,199,0.10)",
                          fontFamily: monoFont,
                          fontSize: "0.68rem",
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ fontFamily: monoFont, fontSize: "0.8rem" }}>
                      {log.entity_type}
                      {log.entity_id ? ` #${log.entity_id}` : ""}
                    </TableCell>
                    <TableCell sx={{ color: "text.secondary", maxWidth: 320 }}>
                      {formatDetails(log.details)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Stack direction="row" justifyContent="center" sx={{ py: 2 }}>
              <Pagination count={totalPages} page={page} onChange={(_, p) => setPage(p)} color="primary" />
            </Stack>
          </>
        )}
      </Paper>
    </Stack>
  );
}
