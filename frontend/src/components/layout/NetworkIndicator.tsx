import { Stack, Typography, CircularProgress, Tooltip, IconButton } from "@mui/material";
import WifiRoundedIcon from "@mui/icons-material/WifiRounded";
import WifiOffRoundedIcon from "@mui/icons-material/WifiOffRounded";
import SyncRoundedIcon from "@mui/icons-material/SyncRounded";
import { alpha } from "@mui/material/styles";
import { colors } from "@/theme/theme";
import { useSync } from "@/context/SyncContext";

export default function NetworkIndicator() {
  const { isOnline, syncing, triggerSync, pendingCount } = useSync();
  const color = isOnline ? colors.synced : colors.failed;

  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Stack
        direction="row"
        spacing={0.75}
        alignItems="center"
        sx={{
          px: 1.25,
          py: 0.5,
          borderRadius: 5,
          backgroundColor: alpha(color, 0.12),
          border: `1px solid ${alpha(color, 0.35)}`,
        }}
      >
        {isOnline ? (
          <WifiRoundedIcon sx={{ fontSize: 16, color }} />
        ) : (
          <WifiOffRoundedIcon sx={{ fontSize: 16, color }} />
        )}
        <Typography variant="caption" sx={{ color, fontWeight: 700 }}>
          {isOnline ? "Online" : "Offline"}
        </Typography>
      </Stack>

      {pendingCount > 0 && (
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          {pendingCount} pending
        </Typography>
      )}

      <Tooltip title={isOnline ? "Sync now" : "Will sync automatically when back online"}>
        <span>
          <IconButton size="small" onClick={() => triggerSync()} disabled={!isOnline || syncing}>
            {syncing ? (
              <CircularProgress size={16} sx={{ color: colors.teal }} />
            ) : (
              <SyncRoundedIcon fontSize="small" />
            )}
          </IconButton>
        </span>
      </Tooltip>
    </Stack>
  );
}
