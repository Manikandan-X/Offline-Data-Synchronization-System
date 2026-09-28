import { Box } from "@mui/material";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar, { SIDEBAR_WIDTH } from "./Sidebar";
import Topbar from "./Topbar";

const TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/records": "Records",
  "/sync-queue": "Sync Queue",
  "/conflicts": "Conflicts",
  "/sync-history": "Sync History",
  "/audit-log": "Audit Log",
  "/users": "User Management",
  "/profile": "Profile",
};

function resolveTitle(pathname: string): string {
  if (TITLES[pathname]) return TITLES[pathname];
  const base = "/" + pathname.split("/")[1];
  return TITLES[base] || "SyncGrid";
}

export default function AppLayout() {
  const location = useLocation();

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />
      <Box sx={{ flex: 1, width: `calc(100% - ${SIDEBAR_WIDTH}px)`, display: "flex", flexDirection: "column" }}>
        <Topbar title={resolveTitle(location.pathname)} />
        <Box sx={{ p: 3, flex: 1 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
