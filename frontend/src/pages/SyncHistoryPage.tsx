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
  IconButton,
  Alert,
  Box,
} from "@mui/material";
import ArrowUpwardRoundedIcon from "@mui/icons-material/ArrowUpwardRounded";
import ArrowDownwardRoundedIcon from "@mui/icons-material/ArrowDownwardRounded";
import HistoryRoundedIcon from "@mui/icons-material/HistoryRounded";
import { format } from "date-fns";
import { dashboardApi } from "@/api/dashboard";
import { extractErrorMessage } from "@/api/client";
import StatusChip from "@/components/common/StatusChip";
import EmptyState from "@/components/common/EmptyState";
import { monoFont } from "@/theme/theme";
import { useSync } from "@/context/SyncContext";
import type { SyncOperation } from "@/types";

const PAGE_SIZE = 10;

export default function SyncHistoryPage() {
  const { isOnline } = useSync();
  const [items, setItems] = useState<SyncOperation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [operationId, setOperationId] = useState("");
  const [status, setStatus] = useState("");
  const [operationType, setOperationType] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
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
      const res = await dashboardApi.searchOperations({
        operation_id: operationId || undefined,
        status: status || undefined,
        operation_type: operationType || undefined,
        from_date: fromDate ? new Date(fromDate).toISOString() : undefined,
        to_date: toDate ? new Date(toDate).toISOString() : undefined,
        page,
        page_size: PAGE_SIZE,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setItems(res.items);
      setTotal(res.total_pages);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, sortBy, sortOrder, isOnline]);

  const applyFilters = () => {
    setPage(1);
    load();
  };

  const toggleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  };

  const SortHeader = ({ field, label }: { field: string; label: string }) => (
    <TableCell
      onClick={() => toggleSort(field)}
      sx={{ cursor: "pointer", userSelect: "none", whiteSpace: "nowrap" }}
    >
      <Stack direction="row" spacing={0.4} alignItems="center">
        <span>{label}</span>
        {sortBy === field &&
          (sortOrder === "asc" ? (
            <ArrowUpwardRoundedIcon sx={{ fontSize: 13 }} />
          ) : (
            <ArrowDownwardRoundedIcon sx={{ fontSize: 13 }} />
          ))}
      </Stack>
    </TableCell>
  );

  return (
    <Stack spacing={2.5}>
      {!isOnline && (
        <Alert severity="warning">
          Sync history is stored server-side, so this page needs a connection. You're currently offline.
        </Alert>
      )}

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" spacing={1.5} flexWrap="wrap" useFlexGap alignItems="center">
          <TextField
            label="Search by operation ID"
            size="small"
            value={operationId}
            onChange={(e) => setOperationId(e.target.value)}
            sx={{ minWidth: 220 }}
          />
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Status</InputLabel>
            <Select label="Status" value={status} onChange={(e) => setStatus(e.target.value)}>
              <MenuItem value="">All</MenuItem>
              <MenuItem value="PENDING">Pending</MenuItem>
              <MenuItem value="PROCESSING">Processing</MenuItem>
              <MenuItem value="SUCCESS">Success</MenuItem>
              <MenuItem value="FAILED">Failed</MenuItem>
              <MenuItem value="CONFLICT">Conflict</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Type</InputLabel>
            <Select label="Type" value={operationType} onChange={(e) => setOperationType(e.target.value)}>
              <MenuItem value="">All</MenuItem>
              <MenuItem value="CREATE">Create</MenuItem>
              <MenuItem value="UPDATE">Update</MenuItem>
              <MenuItem value="DELETE">Delete</MenuItem>
            </Select>
          </FormControl>
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
          <EmptyState icon={<HistoryRoundedIcon fontSize="inherit" />} title="No matching sync operations" />
        ) : (
          <>
            <Table>
              <TableHead>
                <TableRow>
                  <SortHeader field="created_at" label="Created" />
                  <TableCell>Operation ID</TableCell>
                  <TableCell>Record</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Attempts</TableCell>
                  <TableCell>Error</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((op) => (
                  <TableRow key={op.id} hover>
                    <TableCell sx={{ color: "text.secondary", whiteSpace: "nowrap" }}>
                      {format(new Date(op.created_at), "MMM d, HH:mm:ss")}
                    </TableCell>
                    <TableCell sx={{ fontFamily: monoFont, fontSize: "0.78rem" }}>{op.operation_id}</TableCell>
                    <TableCell sx={{ fontFamily: monoFont }}>{op.record_id ? `#${op.record_id}` : "—"}</TableCell>
                    <TableCell>{op.operation_type}</TableCell>
                    <TableCell>
                      <StatusChip status={op.status} />
                    </TableCell>
                    <TableCell sx={{ fontFamily: monoFont }}>{op.attempt_count}</TableCell>
                    <TableCell sx={{ color: "text.secondary", maxWidth: 240 }}>
                      {op.error_message || "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Stack direction="row" justifyContent="center" sx={{ py: 2 }}>
              <Pagination count={total} page={page} onChange={(_, p) => setPage(p)} color="primary" />
            </Stack>
          </>
        )}
      </Paper>
    </Stack>
  );
}
