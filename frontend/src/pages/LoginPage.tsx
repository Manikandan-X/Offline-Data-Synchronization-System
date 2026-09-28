import { useState } from "react";
import { Box, Paper, Stack, TextField, Typography, Button, Alert, Link as MuiLink } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import { useAuth } from "@/context/AuthContext";
import { extractErrorMessage } from "@/api/client";
import { colors } from "@/theme/theme";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        px: 2,
      }}
    >
      <Paper sx={{ p: 4, width: "100%", maxWidth: 420 }}>
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
          <Typography variant="h5">Welcome back</Typography>
          <Typography variant="body2" color="text.secondary">
            Sign in to your SyncGrid workspace
          </Typography>
        </Stack>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              fullWidth
            />
            <Button type="submit" variant="contained" size="large" disabled={loading} fullWidth>
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </Stack>
        </form>

        <Typography variant="body2" sx={{ mt: 3, textAlign: "center", color: "text.secondary" }}>
          Don't have an account?{" "}
          <MuiLink component={Link} to="/register" sx={{ color: colors.teal }}>
            Create one
          </MuiLink>
        </Typography>
      </Paper>
    </Box>
  );
}
