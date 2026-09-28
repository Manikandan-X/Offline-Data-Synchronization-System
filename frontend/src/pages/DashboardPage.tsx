import { useEffect, useState } from "react";
import { Box, Grid, Paper, Stack, Typography, LinearProgress, Chip } from "@mui/material";
import StorageRoundedIcon from "@mui/icons-material/StorageRounded";
import SyncRoundedIcon from "@mui/icons-material/SyncRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import ErrorRoundedIcon from "@mui/icons-material/ErrorRounded";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import StatCard from "@/components/common/StatCard";
import { dashboardApi } from "@/api/dashboard";
import { colors, monoFont } from "@/theme/theme";
import { useSync } from "@/context/SyncContext";
import type { SyncDashboard } from "@/types";
import { format } from "date-fns";

export default function DashboardPage() {
  const [stats, setStats] = useState<SyncDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { isOnline, pendingCount, conflictCount, lastSyncAt } = useSync();

  useEffect(() => {
    if (!isOnline) return;
    dashboardApi
      .stats()
      .then(setStats)
      .catch(() => setError("Could not load live statistics."));
  }, [isOnline]);

  const total = stats?.total_operations || 0;
  const successPct = total ? Math.round(((stats?.successful_operations || 0) / total) * 100) : 0;

  return (
    <Stack spacing={3}>
      {!isOnline && (
        <Paper sx={{ p: 2, borderColor: colors.pending, backgroundColor: "rgba(245,165,36,0.08)" }}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <WarningAmberRoundedIcon sx={{ color: colors.pending }} />
            <Typography variant="body2">
              You're offline. Showing locally queued activity — server statistics will refresh once you're back online.
            </Typography>
          </Stack>
        </Paper>
      )}

      <Grid container spacing={2.5}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            label="Total Records"
            value={stats?.total_records ?? "—"}
            icon={<StorageRoundedIcon fontSize="small" />}
            color={colors.teal}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            label="Pending Sync"
            value={pendingCount}
            icon={<SyncRoundedIcon fontSize="small" />}
            color={colors.pending}
            hint="in local queue"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            label="Failed Syncs"
            value={stats?.failed_operations ?? "—"}
            icon={<ErrorRoundedIcon fontSize="small" />}
            color={colors.failed}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            label="Conflicts"
            value={conflictCount || stats?.pending_conflicts || 0}
            icon={<WarningAmberRoundedIcon fontSize="small" />}
            color={colors.conflict}
            hint="need resolution"
          />
        </Grid>
      </Grid>

      <Grid container spacing={2.5}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 3, height: "100%" }}>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 2 }}>
              Synchronization Health
            </Typography>
            <Stack spacing={2.5}>
              <Box>
                <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
                  <Typography variant="body2" color="text.secondary">
                    Success rate
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: monoFont }}>
                    {successPct}%
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={successPct}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: "rgba(148,178,199,0.12)",
                    "& .MuiLinearProgress-bar": { backgroundColor: colors.teal, borderRadius: 4 },
                  }}
                />
              </Box>

              <Grid container spacing={2}>
                <StatRow label="Successful operations" value={stats?.successful_operations} color={colors.synced} icon={<CheckCircleRoundedIcon fontSize="small" />} />
                <StatRow label="Pending operations" value={stats?.pending_operations} color={colors.pending} icon={<SyncRoundedIcon fontSize="small" />} />
                <StatRow label="Failed operations" value={stats?.failed_operations} color={colors.failed} icon={<ErrorRoundedIcon fontSize="small" />} />
                <StatRow label="Conflict operations" value={stats?.conflict_operations} color={colors.conflict} icon={<WarningAmberRoundedIcon fontSize="small" />} />
              </Grid>
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 3, height: "100%" }}>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 2 }}>
              Conflict Overview
            </Typography>
            <Stack spacing={2}>
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="text.secondary">
                  Total conflicts
                </Typography>
                <Chip label={stats?.total_conflicts ?? 0} size="small" sx={{ fontFamily: monoFont }} />
              </Stack>
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="text.secondary">
                  Pending resolution
                </Typography>
                <Chip
                  label={stats?.pending_conflicts ?? 0}
                  size="small"
                  sx={{ fontFamily: monoFont, color: colors.conflict, backgroundColor: "rgba(167,139,250,0.14)" }}
                />
              </Stack>
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="text.secondary">
                  Resolved
                </Typography>
                <Chip
                  label={stats?.resolved_conflicts ?? 0}
                  size="small"
                  sx={{ fontFamily: monoFont, color: colors.synced, backgroundColor: "rgba(45,212,191,0.14)" }}
                />
              </Stack>

              <Box sx={{ pt: 1.5, mt: 1, borderTop: `1px solid ${colors.border}` }}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <AccessTimeRoundedIcon fontSize="small" sx={{ color: "text.secondary" }} />
                  <Typography variant="body2" color="text.secondary">
                    Last sync:{" "}
                    <span style={{ fontFamily: monoFont, color: "inherit" }}>
                      {lastSyncAt || stats?.last_sync_at
                        ? format(new Date(lastSyncAt || stats!.last_sync_at!), "MMM d, HH:mm:ss")
                        : "never"}
                    </span>
                  </Typography>
                </Stack>
              </Box>
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      {error && (
        <Typography variant="body2" color="text.secondary">
          {error}
        </Typography>
      )}
    </Stack>
  );
}

function StatRow({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value?: number;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <Grid item xs={6}>
      <Stack direction="row" spacing={1} alignItems="center">
        <Box sx={{ color }}>{icon}</Box>
        <Stack>
          <Typography variant="body2" sx={{ fontFamily: monoFont, fontWeight: 700 }}>
            {value ?? "—"}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {label}
          </Typography>
        </Stack>
      </Stack>
    </Grid>
  );
}
