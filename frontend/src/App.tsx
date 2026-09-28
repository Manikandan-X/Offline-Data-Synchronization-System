import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { SyncProvider } from "@/context/SyncContext";
import { NotificationProvider } from "@/context/NotificationContext";
import { ProtectedRoute, AdminRoute, GuestRoute } from "@/routes/guards";
import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import DashboardPage from "@/pages/DashboardPage";
import RecordsPage from "@/pages/RecordsPage";
import SyncQueuePage from "@/pages/SyncQueuePage";
import ConflictsPage from "@/pages/ConflictsPage";
import SyncHistoryPage from "@/pages/SyncHistoryPage";
import UsersPage from "@/pages/UsersPage";
import ProfilePage from "@/pages/ProfilePage";
import AuditLogPage from "@/pages/AuditLogPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NotificationProvider>
          <SyncProvider>
            <Routes>
              <Route element={<GuestRoute />}>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
              </Route>

              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/records" element={<RecordsPage />} />
                  <Route path="/sync-queue" element={<SyncQueuePage />} />
                  <Route path="/conflicts" element={<ConflictsPage />} />
                  <Route path="/sync-history" element={<SyncHistoryPage />} />
                  <Route path="/audit-log" element={<AuditLogPage />} />
                  <Route path="/profile" element={<ProfilePage />} />

                  <Route element={<AdminRoute />}>
                    <Route path="/users" element={<UsersPage />} />
                  </Route>
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </SyncProvider>
        </NotificationProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
