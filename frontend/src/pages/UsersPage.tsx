import { useEffect, useState } from "react";
import {
  Stack,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TextField,
  Button,
  Switch,
  Pagination,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
} from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import { usersApi } from "@/api/users";
import { extractErrorMessage } from "@/api/client";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import { colors, monoFont } from "@/theme/theme";
import { useAuth } from "@/context/AuthContext";
import { useNotify } from "@/context/NotificationContext";
import type { User } from "@/types";

const PAGE_SIZE = 10;
const ROLE_OPTIONS = [
  { id: 1, name: "Admin" },
  { id: 2, name: "User" },
];

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const notify = useNotify();
  const [users, setUsers] = useState<User[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const [createOpen, setCreateOpen] = useState(false);
  const [newUser, setNewUser] = useState({ first_name: "", last_name: "", email: "", password: "", role_id: 2 });
  const [creating, setCreating] = useState(false);

  const [editTarget, setEditTarget] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({ first_name: "", last_name: "", email: "" });
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = async () => {
    setError(null);
    try {
      const res = await usersApi.list({ page, page_size: PAGE_SIZE, search: search || undefined });
      setUsers(res.items);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const handleSearch = () => {
    setPage(1);
    load();
  };

  const toggleActive = async (u: User) => {
    try {
      if (u.is_active) await usersApi.deactivate(u.id);
      else await usersApi.activate(u.id);
      notify(u.is_active ? "User deactivated." : "User activated.", "success");
      load();
    } catch (err) {
      notify(extractErrorMessage(err), "error");
    }
  };

  const changeRole = async (u: User, roleId: number) => {
    try {
      await usersApi.changeRole(u.id, roleId);
      notify("Role updated.", "success");
      load();
    } catch (err) {
      notify(extractErrorMessage(err), "error");
    }
  };

  const openEdit = (u: User) => {
    setEditTarget(u);
    setEditForm({ first_name: u.first_name, last_name: u.last_name, email: u.email });
  };

  const handleSaveEdit = async () => {
    if (!editTarget) return;
    setSaving(true);
    try {
      await usersApi.update(editTarget.id, editForm);
      notify("User details updated.", "success");
      setEditTarget(null);
      load();
    } catch (err) {
      notify(extractErrorMessage(err), "error");
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await usersApi.remove(deleteTarget.id);
      notify("User deleted.", "success");
      setDeleteTarget(null);
      load();
    } catch (err) {
      notify(extractErrorMessage(err), "error");
    } finally {
      setDeleting(false);
    }
  };

  const handleCreate = async () => {
    setCreating(true);
    try {
      await usersApi.create(newUser);
      setCreateOpen(false);
      setNewUser({ first_name: "", last_name: "", email: "", password: "", role_id: 2 });
      notify("User created.", "success");
      load();
    } catch (err) {
      notify(extractErrorMessage(err), "error");
    } finally {
      setCreating(false);
    }
  };

  return (
    <Stack spacing={2.5}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <TextField
          size="small"
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          sx={{ minWidth: 280 }}
        />
        <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={() => setCreateOpen(true)}>
          New user
        </Button>
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Active</TableCell>
              <TableCell>Joined</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.id} hover>
                <TableCell>{u.first_name} {u.last_name}</TableCell>
                <TableCell sx={{ fontFamily: monoFont, fontSize: "0.82rem" }}>{u.email}</TableCell>
                <TableCell>
                  <FormControl size="small" variant="standard">
                    <Select
                      value={u.role_id}
                      onChange={(e) => changeRole(u, Number(e.target.value))}
                      disabled={u.id === currentUser?.id}
                      disableUnderline
                    >
                      {ROLE_OPTIONS.map((r) => (
                        <MenuItem key={r.id} value={r.id}>
                          {r.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </TableCell>
                <TableCell>
                  <Switch
                    size="small"
                    checked={u.is_active}
                    onChange={() => toggleActive(u)}
                    disabled={u.id === currentUser?.id}
                  />
                </TableCell>
                <TableCell sx={{ color: "text.secondary" }}>
                  {new Date(u.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Edit name / email">
                    <IconButton size="small" onClick={() => openEdit(u)}>
                      <EditRoundedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={u.id === currentUser?.id ? "Can't delete your own account" : "Delete user"}>
                    <span>
                      <IconButton
                        size="small"
                        disabled={u.id === currentUser?.id}
                        onClick={() => setDeleteTarget(u)}
                      >
                        <DeleteRoundedIcon fontSize="small" sx={{ color: colors.failed }} />
                      </IconButton>
                    </span>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <Stack direction="row" justifyContent="center" sx={{ py: 2 }}>
          <Pagination count={totalPages} page={page} onChange={(_, p) => setPage(p)} color="primary" />
        </Stack>
      </Paper>

      {/* Create user */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>New user</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Stack direction="row" spacing={2}>
              <TextField
                label="First name"
                value={newUser.first_name}
                onChange={(e) => setNewUser((f) => ({ ...f, first_name: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Last name"
                value={newUser.last_name}
                onChange={(e) => setNewUser((f) => ({ ...f, last_name: e.target.value }))}
                fullWidth
              />
            </Stack>
            <TextField
              label="Email"
              type="email"
              value={newUser.email}
              onChange={(e) => setNewUser((f) => ({ ...f, email: e.target.value }))}
              fullWidth
            />
            <TextField
              label="Password"
              type="password"
              value={newUser.password}
              onChange={(e) => setNewUser((f) => ({ ...f, password: e.target.value }))}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                label="Role"
                value={newUser.role_id}
                onChange={(e) => setNewUser((f) => ({ ...f, role_id: Number(e.target.value) }))}
              >
                {ROLE_OPTIONS.map((r) => (
                  <MenuItem key={r.id} value={r.id}>
                    {r.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={creating}>
            {creating ? "Creating…" : "Create user"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit user info (name/email only — no password here) */}
      <Dialog open={!!editTarget} onClose={() => setEditTarget(null)} fullWidth maxWidth="xs">
        <DialogTitle>Edit {editTarget?.first_name}'s details</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Stack direction="row" spacing={2}>
              <TextField
                label="First name"
                value={editForm.first_name}
                onChange={(e) => setEditForm((f) => ({ ...f, first_name: e.target.value }))}
                fullWidth
              />
              <TextField
                label="Last name"
                value={editForm.last_name}
                onChange={(e) => setEditForm((f) => ({ ...f, last_name: e.target.value }))}
                fullWidth
              />
            </Stack>
            <TextField
              label="Email"
              type="email"
              value={editForm.email}
              onChange={(e) => setEditForm((f) => ({ ...f, email: e.target.value }))}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={() => setEditTarget(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveEdit} disabled={saving}>
            {saving ? "Saving…" : "Save changes"}
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete this user?"
        message={
          deleteTarget
            ? `This will permanently delete ${deleteTarget.first_name} ${deleteTarget.last_name} (${deleteTarget.email}). This action cannot be undone.`
            : ""
        }
        confirmLabel="Delete user"
        loading={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </Stack>
  );
}
