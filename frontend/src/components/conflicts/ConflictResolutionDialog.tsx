import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stack,
  Typography,
  Paper,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  Alert,
  Box,
} from "@mui/material";
import { monoFont, colors } from "@/theme/theme";
import { extractErrorMessage } from "@/api/client";
import type { ConflictItem, ResolutionStrategy } from "@/types";

interface Props {
  open: boolean;
  onClose: () => void;
  conflict: ConflictItem | null;
  onResolve: (
    strategy: ResolutionStrategy,
    notes: string,
    manualData: Record<string, unknown> | null
  ) => Promise<void>;
}

export default function ConflictResolutionDialog({ open, onClose, conflict, onResolve }: Props) {
  const [strategy, setStrategy] = useState<ResolutionStrategy>("LAST_WRITE_WINS");
  const [notes, setNotes] = useState("");
  const [manualText, setManualText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  if (!conflict) return null;

  const handleResolve = async () => {
    setError(null);
    let manualData: Record<string, unknown> | null = null;

    if (strategy === "MANUAL") {
      try {
        manualData = JSON.parse(manualText || "{}");
      } catch {
        setError("Manual data must be valid JSON.");
        return;
      }
    }

    setSaving(true);
    try {
      await onResolve(strategy, notes, manualData);
      onClose();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>Resolve conflict on record #{conflict.record_id}</DialogTitle>
      <DialogContent>
        <Stack spacing={2.5} sx={{ mt: 1 }}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <Paper sx={{ p: 2, flex: 1, borderColor: colors.pending }}>
              <Typography variant="caption" sx={{ color: colors.pending, fontWeight: 700 }}>
                YOUR VERSION (v{conflict.client_version})
              </Typography>
              <Box
                component="pre"
                sx={{ fontFamily: monoFont, fontSize: "0.78rem", mt: 1, whiteSpace: "pre-wrap", color: "text.primary" }}
              >
                {JSON.stringify(conflict.client_data, null, 2)}
              </Box>
            </Paper>
            <Paper sx={{ p: 2, flex: 1, borderColor: colors.teal }}>
              <Typography variant="caption" sx={{ color: colors.teal, fontWeight: 700 }}>
                SERVER VERSION (v{conflict.server_version})
              </Typography>
              <Box
                component="pre"
                sx={{ fontFamily: monoFont, fontSize: "0.78rem", mt: 1, whiteSpace: "pre-wrap", color: "text.primary" }}
              >
                {JSON.stringify(conflict.server_data, null, 2)}
              </Box>
            </Paper>
          </Stack>

          {error && <Alert severity="error">{error}</Alert>}

          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Resolution strategy
            </Typography>
            <RadioGroup value={strategy} onChange={(e) => setStrategy(e.target.value as ResolutionStrategy)}>
              <FormControlLabel
                value="LAST_WRITE_WINS"
                control={<Radio size="small" />}
                label="Last-write-wins — keep whichever version has the higher version number"
              />
              <FormControlLabel
                value="SERVER_WINS"
                control={<Radio size="small" />}
                label="Server wins — discard your local change"
              />
              <FormControlLabel
                value="CLIENT_WINS"
                control={<Radio size="small" />}
                label="Client wins — overwrite the server with your local change"
              />
              <FormControlLabel value="MANUAL" control={<Radio size="small" />} label="Manual — write the merged result yourself" />
            </RadioGroup>
          </Box>

          {strategy === "MANUAL" && (
            <TextField
              label="Merged data (JSON)"
              multiline
              minRows={6}
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
              placeholder='{"field": "merged value"}'
              InputProps={{ sx: { fontFamily: monoFont, fontSize: "0.82rem" } }}
              fullWidth
            />
          )}

          <TextField
            label="Notes (optional)"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            fullWidth
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2.5 }}>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button variant="contained" onClick={handleResolve} disabled={saving}>
          {saving ? "Resolving…" : "Resolve conflict"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
