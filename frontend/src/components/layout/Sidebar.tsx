import { Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Stack, Typography, Badge } from "@mui/material";
import { NavLink, useLocation } from "react-router-dom";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import StorageRoundedIcon from "@mui/icons-material/StorageRounded";
import SyncRoundedIcon from "@mui/icons-material/SyncRounded";
import HistoryRoundedIcon from "@mui/icons-material/HistoryRounded";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import GroupRoundedIcon from "@mui/icons-material/GroupRounded";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import HistoryEduRoundedIcon from "@mui/icons-material/HistoryEduRounded";
import { useAuth } from "@/context/AuthContext";
import { useSync } from "@/context/SyncContext";
import { colors } from "@/theme/theme";

export const SIDEBAR_WIDTH = 240;

export default function Sidebar() {
  const location = useLocation();
  const { isAdmin } = useAuth();
  const { pendingCount, conflictCount } = useSync();

  const navItems = [
    { to: "/", label: "Dashboard", icon: <DashboardRoundedIcon fontSize="small" /> },
    { to: "/records", label: "Records", icon: <StorageRoundedIcon fontSize="small" /> },
    {
      to: "/sync-queue",
      label: "Sync Queue",
      icon: <SyncRoundedIcon fontSize="small" />,
      badge: pendingCount,
    },
    {
      to: "/conflicts",
      label: "Conflicts",
      icon: <WarningAmberRoundedIcon fontSize="small" />,
      badge: conflictCount,
      badgeColor: colors.conflict,
    },
    { to: "/sync-history", label: "Sync History", icon: <HistoryRoundedIcon fontSize="small" /> },
    { to: "/audit-log", label: "Audit Log", icon: <HistoryEduRoundedIcon fontSize="small" /> },
    { to: "/profile", label: "Profile", icon: <PersonRoundedIcon fontSize="small" /> },
  ];

  if (isAdmin) {
    navItems.splice(6, 0, { to: "/users", label: "Users", icon: <GroupRoundedIcon fontSize="small" /> });
  }

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: SIDEBAR_WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: SIDEBAR_WIDTH, boxSizing: "border-box" },
      }}
    >
      <Stack sx={{ px: 2.5, py: 2.5 }} direction="row" spacing={1.2} alignItems="center">
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: 1.5,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: `linear-gradient(135deg, ${colors.teal}, ${colors.violet})`,
            color: "#04211d",
          }}
        >
          <HubRoundedIcon fontSize="small" />
        </Box>
        <Typography variant="h6" sx={{ fontSize: "1.05rem", letterSpacing: 0.2 }}>
          SyncGrid
        </Typography>
      </Stack>

      <List sx={{ px: 1.5, flex: 1 }}>
        {navItems.map((item) => {
          const active = location.pathname === item.to;
          return (
            <ListItemButton
              key={item.to}
              component={NavLink}
              to={item.to}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                color: active ? colors.teal : "text.secondary",
                backgroundColor: active ? "rgba(45,212,191,0.08)" : "transparent",
                "&:hover": { backgroundColor: "rgba(148,178,199,0.08)" },
              }}
            >
              <ListItemIcon sx={{ minWidth: 34, color: "inherit" }}>{item.icon}</ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{ fontSize: "0.88rem", fontWeight: active ? 600 : 500 }}
              />
              {!!item.badge && (
                <Badge
                  badgeContent={item.badge}
                  sx={{
                    "& .MuiBadge-badge": {
                      backgroundColor: item.badgeColor || colors.amber,
                      color: "#1a1200",
                      fontWeight: 700,
                    },
                  }}
                />
              )}
            </ListItemButton>
          );
        })}
      </List>

      <Box sx={{ px: 2.5, py: 2, borderTop: `1px solid ${colors.border}` }}>
        <Typography variant="caption" sx={{ color: "text.muted" }}>
          Offline-First Sync Console
        </Typography>
      </Box>
    </Drawer>
  );
}
