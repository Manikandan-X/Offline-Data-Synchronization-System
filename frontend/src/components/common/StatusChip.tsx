import { Chip } from "@mui/material";
import { alpha } from "@mui/material/styles";
import { statusColor } from "@/theme/theme";

export default function StatusChip({ status }: { status: string }) {
  const color = statusColor(status);
  return (
    <Chip
      label={status}
      size="small"
      sx={{
        color,
        backgroundColor: alpha(color, 0.14),
        border: `1px solid ${alpha(color, 0.4)}`,
      }}
    />
  );
}
