import { Box, Card, Stack, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import { monoFont } from "@/theme/theme";
import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  color: string;
  hint?: string;
}

export default function StatCard({ label, value, icon, color, hint }: StatCardProps) {
  return (
    <Card sx={{ p: 2.5, height: "100%" }}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
        <Stack spacing={0.5}>
          <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 600, letterSpacing: 0.4 }}>
            {label.toUpperCase()}
          </Typography>
          <Typography variant="h4" sx={{ fontFamily: monoFont, fontWeight: 700 }}>
            {value}
          </Typography>
          {hint && (
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              {hint}
            </Typography>
          )}
        </Stack>
        <Box
          sx={{
            width: 42,
            height: 42,
            borderRadius: 2,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color,
            backgroundColor: alpha(color, 0.14),
            border: `1px solid ${alpha(color, 0.35)}`,
          }}
        >
          {icon}
        </Box>
      </Stack>
    </Card>
  );
}
