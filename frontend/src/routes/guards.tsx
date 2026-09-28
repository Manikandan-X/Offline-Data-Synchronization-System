import { Navigate, Outlet } from "react-router-dom";
import { Box, CircularProgress } from "@mui/material";
import { useAuth } from "@/context/AuthContext";
import { colors } from "@/theme/theme";

export function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <CircularProgress sx={{ color: colors.teal }} />
      </Box>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  return <Outlet />;
}

export function AdminRoute() {
  const { isAdmin, loading } = useAuth();

  if (loading) return null;
  if (!isAdmin) return <Navigate to="/" replace />;

  return <Outlet />;
}

export function GuestRoute() {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (user) return <Navigate to="/" replace />;

  return <Outlet />;
}
