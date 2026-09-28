import { Box, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

export default function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <Box sx={{ py: 8, textAlign: "center" }}>
      <Stack spacing={1.5} alignItems="center">
        {icon && (
          <Box sx={{ color: "text.muted", opacity: 0.6, fontSize: 44 }}>{icon}</Box>
        )}
        <Typography variant="h6" sx={{ color: "text.primary" }}>
          {title}
        </Typography>
        {description && (
          <Typography variant="body2" sx={{ color: "text.secondary", maxWidth: 380 }}>
            {description}
          </Typography>
        )}
        {action}
      </Stack>
    </Box>
  );
}
