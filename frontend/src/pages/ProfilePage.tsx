import { useState } from "react";
import {
  Paper,
  Stack,
  Typography,
  Avatar,
  Chip,
  Divider,
  TextField,
  Button,
  Box,
} from "@mui/material";
import LockResetRoundedIcon from "@mui/icons-material/LockResetRounded";
import { useAuth } from "@/context/AuthContext";
import { useNotify } from "@/context/NotificationContext";
import { authApi } from "@/api/auth";
import { extractErrorMessage } from "@/api/client";
import { colors, monoFont } from "@/theme/theme";

export default function ProfilePage() {
  const { user, isAdmin, refreshUser } = useAuth();
  const notify = useNotify();

  const [form, setForm] = useState({
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
    email: user?.email || "",
  });
  const [savingProfile, setSavingProfile] = useState(false);

  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm: "" });
  const [savingPassword, setSavingPassword] = useState(false);

  if (!user) return null;

  const initials = `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();

  const dirty =
    form.first_name !== user.first_name ||
    form.last_name !== user.last_name ||
    form.email !== user.email;

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    try {
      await authApi.updateProfile({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
      });
      await refreshUser();
      notify("Profile updated.", "success");
    } catch (err) {
      notify(extractErrorMessage(err), "error");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async () => {
    if (!pwForm.current_password || !pwForm.new_password) {
      notify("Fill in both password fields.", "warning");
      return;
    }
    if (pwForm.new_password.length < 8) {
      notify("New password must be at least 8 characters.", "warning");
      return;
    }
    if (pwForm.new_password !== pwForm.confirm) {
      notify("New password and confirmation don't match.", "warning");
      return;
    }
    setSavingPassword(true);
    try {
      await authApi.changePassword({
        current_password: pwForm.current_password,
        new_password: pwForm.new_password,
      });
      setPwForm({ current_password: "", new_password: "", confirm: "" });
      notify("Password changed.", "success");
    } catch (err) {
      notify(extractErrorMessage(err), "error");
    } finally {
      setSavingPassword(false);
    }
  };

  return (
    <Stack spacing={2.5} sx={{ maxWidth: 560 }}>
      <Paper sx={{ p: 3 }}>
        <Stack direction="row" spacing={2.5} alignItems="center" sx={{ mb: 3 }}>
          <Avatar sx={{ width: 64, height: 64, fontSize: "1.4rem", bgcolor: colors.tealDim, color: colors.teal }}>
            {initials}
          </Avatar>
          <Stack>
            <Typography variant="h6">
              {user.first_name} {user.last_name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {user.email}
            </Typography>
            <Chip
              label={isAdmin ? "Admin" : "User"}
              size="small"
              sx={{ mt: 0.5, width: "fit-content", color: colors.teal, backgroundColor: "rgba(45,212,191,0.12)" }}
            />
          </Stack>
        </Stack>

        <Divider sx={{ mb: 3 }} />

        <Typography variant="subtitle2" sx={{ mb: 2 }}>
          Profile details
        </Typography>
        <Stack spacing={2}>
          <Stack direction="row" spacing={2}>
            <TextField
              label="First name"
              value={form.first_name}
              onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
              fullWidth
            />
            <TextField
              label="Last name"
              value={form.last_name}
              onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
              fullWidth
            />
          </Stack>
          <TextField
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            fullWidth
          />
          <Box>
            <Button variant="contained" onClick={handleSaveProfile} disabled={!dirty || savingProfile}>
              {savingProfile ? "Saving…" : "Save changes"}
            </Button>
          </Box>
        </Stack>

        <Divider sx={{ my: 3 }} />

        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
          <LockResetRoundedIcon fontSize="small" sx={{ color: "text.secondary" }} />
          <Typography variant="subtitle2">Change password</Typography>
        </Stack>
        <Stack spacing={2}>
          <TextField
            label="Current password"
            type="password"
            value={pwForm.current_password}
            onChange={(e) => setPwForm((f) => ({ ...f, current_password: e.target.value }))}
            fullWidth
          />
          <TextField
            label="New password"
            type="password"
            value={pwForm.new_password}
            onChange={(e) => setPwForm((f) => ({ ...f, new_password: e.target.value }))}
            helperText="At least 8 characters"
            fullWidth
          />
          <TextField
            label="Confirm new password"
            type="password"
            value={pwForm.confirm}
            onChange={(e) => setPwForm((f) => ({ ...f, confirm: e.target.value }))}
            fullWidth
          />
          <Box>
            <Button variant="outlined" onClick={handleChangePassword} disabled={savingPassword}>
              {savingPassword ? "Updating…" : "Change password"}
            </Button>
          </Box>
        </Stack>

        <Divider sx={{ my: 3 }} />

        <Stack spacing={1.5}>
          <Row label="User ID" value={`#${user.id}`} />
          <Row label="Account status" value={user.is_active ? "Active" : "Inactive"} />
          <Row label="Joined" value={new Date(user.created_at).toLocaleDateString()} />
          <Row label="Last updated" value={new Date(user.updated_at).toLocaleString()} />
        </Stack>
      </Paper>
    </Stack>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <Stack direction="row" justifyContent="space-between">
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontFamily: monoFont }}>
        {value}
      </Typography>
    </Stack>
  );
}
