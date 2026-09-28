import { useState } from "react";
import { Box, Paper, Stack, TextField, Typography, Button, Alert, Link as MuiLink } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import { useAuth } from "@/context/AuthContext";
import { extractErrorMessage } from "@/api/client";
import { colors } from "@/theme/theme";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const update = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(form);
      navigate("/");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", px: 2 }}>
      <Paper sx={{ p: 4, width: "100%", maxWidth: 440 }}>
        <Stack spacing={0.5} alignItems="center" sx={{ mb: 3 }}>
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: 2,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: `linear-gradient(135deg, ${colors.teal}, ${colors.violet})`,
              color: "#04211d",
              mb: 1,
            }}
          >
            <HubRoundedIcon />
          </Box>
          <Typography variant="h5">Create your account</Typography>
          <Typography variant="body2" color="text.secondary">
            Start working — even offline
          </Typography>
        </Stack>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <Stack direction="row" spacing={2}>
              <TextField label="First name" value={form.first_name} onChange={update("first_name")} required fullWidth />
              <TextField label="Last name" value={form.last_name} onChange={update("last_name")} required fullWidth />
            </Stack>
            <TextField label="Email" type="email" value={form.email} onChange={update("email")} required fullWidth />
            <TextField
              label="Password"
              type="password"
              value={form.password}
              onChange={update("password")}
              required
              fullWidth
              helperText="At least 8 characters"
            />
            <Button type="submit" variant="contained" size="large" disabled={loading} fullWidth>
              {loading ? "Creating account…" : "Create account"}
            </Button>
          </Stack>
        </form>

        <Typography variant="body2" sx={{ mt: 3, textAlign: "center", color: "text.secondary" }}>
          Already have an account?{" "}
          <MuiLink component={Link} to="/login" sx={{ color: colors.teal }}>
            Sign in
          </MuiLink>
        </Typography>
      </Paper>
    </Box>
  );
}
