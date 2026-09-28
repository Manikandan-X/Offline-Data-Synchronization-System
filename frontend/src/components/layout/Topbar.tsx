import { AppBar, Toolbar, Typography, Stack, Avatar, Menu, MenuItem, IconButton, Divider } from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import { useAuth } from "@/context/AuthContext";
import NetworkIndicator from "./NetworkIndicator";
import { colors } from "@/theme/theme";

export default function Topbar({ title }: { title: string }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const initials = user ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase() : "?";

  return (
    <AppBar position="sticky" elevation={0}>
      <Toolbar sx={{ justifyContent: "space-between", gap: 2 }}>
        <Typography variant="h6" sx={{ fontSize: "1.05rem" }}>
          {title}
        </Typography>

        <Stack direction="row" spacing={2} alignItems="center">
          <NetworkIndicator />
          <Divider orientation="vertical" flexItem sx={{ borderColor: colors.border }} />
          <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} size="small">
            <Avatar sx={{ width: 32, height: 32, fontSize: "0.8rem", bgcolor: colors.tealDim, color: colors.teal }}>
              {initials}
            </Avatar>
          </IconButton>
          <Menu anchorEl={anchorEl} open={!!anchorEl} onClose={() => setAnchorEl(null)}>
            <MenuItem disabled sx={{ opacity: "1 !important" }}>
              <Stack>
                <Typography variant="body2" fontWeight={600}>
                  {user?.first_name} {user?.last_name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {user?.email}
                </Typography>
              </Stack>
            </MenuItem>
            <Divider />
            <MenuItem
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              <LogoutRoundedIcon fontSize="small" sx={{ mr: 1 }} />
              Log out
            </MenuItem>
          </Menu>
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
