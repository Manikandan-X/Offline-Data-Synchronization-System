import { useEffect, useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Stack,
  Alert,
  Typography,
} from "@mui/material";
import { monoFont } from "@/theme/theme";
import type { RecordItem } from "@/types";

interface RecordFormDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  record?: RecordItem | null;
}

export default function RecordFormDialog({ open, onClose, onSubmit, record }: RecordFormDialogProps) {
  const [text, setText] = useState("{\n  \"title\": \"\",\n  \"notes\": \"\"\n}");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setText(record ? JSON.stringify(record.data, null, 2) : "{\n  \"title\": \"\",\n  \"notes\": \"\"\n}");
      setError(null);
    }
  }, [open, record]);

  const handleSubmit = async () => {
    setError(null);
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(text);
    } catch {
      setError("That's not valid JSON — check for a missing comma or bracket.");
      return;
    }
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      setError("Record data must be a JSON object.");
      return;
    }
    setSaving(true);
    try {
      await onSubmit(parsed);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{record ? `Edit record #${record.id}` : "New record"}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Record data is a free-form JSON object — add whatever fields fit your use case.
          </Typography>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            multiline
            minRows={10}
            maxRows={16}
            value={text}
            onChange={(e) => setText(e.target.value)}
            InputProps={{ sx: { fontFamily: monoFont, fontSize: "0.85rem" } }}
            fullWidth
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2.5 }}>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button variant="contained" onClick={handleSubmit} disabled={saving}>
          {saving ? "Saving…" : record ? "Save changes" : "Create record"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
