import { createTheme, alpha } from "@mui/material/styles";

/**
 * "SyncGrid" design system
 * A dark, data-dense console theme built for a sync/ops tool.
 * - Base: deep slate / graphite backgrounds
 * - Primary: signal teal (used for the online / synced state)
 * - Secondary: amber (used for pending / attention states)
 * - Status colors are explicit: synced=teal, pending=amber, failed=coral, conflict=violet
 * - Headings: Space Grotesk, Body: Inter, Data/IDs/timestamps: JetBrains Mono
 */

export const colors = {
  bg: "#0d1117",
  bgElevated: "#141b24",
  bgPanel: "#182130",
  border: "rgba(148, 178, 199, 0.14)",
  borderStrong: "rgba(148, 178, 199, 0.28)",
  textPrimary: "#e7edf3",
  textSecondary: "#93a4b8",
  textMuted: "#5f7086",

  teal: "#2dd4bf",
  tealDim: "#0f766e",
  amber: "#f5a524",
  amberDim: "#92400e",
  coral: "#f4685b",
  coralDim: "#7f1d1d",
  violet: "#a78bfa",
  violetDim: "#4c1d95",

  synced: "#2dd4bf",
  pending: "#f5a524",
  failed: "#f4685b",
  conflict: "#a78bfa",
  processing: "#38bdf8",
};

export const statusColor = (status: string): string => {
  const s = status.toUpperCase();
  if (s === "SUCCESS" || s === "RESOLVED" || s === "SYNCED") return colors.synced;
  if (s === "PENDING") return colors.pending;
  if (s === "FAILED") return colors.failed;
  if (s === "CONFLICT") return colors.conflict;
  if (s === "PROCESSING") return colors.processing;
  return colors.textMuted;
};

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: colors.teal, contrastText: "#04211d" },
    secondary: { main: colors.amber, contrastText: "#2a1600" },
    error: { main: colors.coral },
    warning: { main: colors.amber },
    success: { main: colors.teal },
    info: { main: colors.violet },
    background: {
      default: colors.bg,
      paper: colors.bgElevated,
    },
    text: {
      primary: colors.textPrimary,
      secondary: colors.textSecondary,
    },
    divider: colors.border,
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: '"Inter", "Segoe UI", sans-serif',
    h1: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
    h2: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
    h3: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
    h4: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
    h5: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
    h6: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
    button: { textTransform: "none", fontWeight: 600 },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundImage:
            "radial-gradient(circle at 15% 0%, rgba(45,212,191,0.06), transparent 45%), radial-gradient(circle at 85% 10%, rgba(167,139,250,0.05), transparent 40%)",
          backgroundAttachment: "fixed",
        },
        "::-webkit-scrollbar": { width: 8, height: 8 },
        "::-webkit-scrollbar-thumb": {
          backgroundColor: "rgba(148,178,199,0.25)",
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          border: `1px solid ${colors.border}`,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: colors.bgElevated,
          border: `1px solid ${colors.border}`,
          backgroundImage: "none",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 8 },
        containedPrimary: {
          boxShadow: `0 0 0 1px ${alpha(colors.teal, 0.25)}`,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, fontSize: "0.72rem" },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderColor: colors.border },
        head: {
          color: colors.textMuted,
          fontSize: "0.72rem",
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          fontWeight: 700,
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.bgPanel,
          backgroundImage: "none",
          borderRight: `1px solid ${colors.border}`,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: alpha(colors.bg, 0.85),
          backgroundImage: "none",
          backdropFilter: "blur(10px)",
          boxShadow: "none",
          borderBottom: `1px solid ${colors.border}`,
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: { borderRadius: 8 },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.bgElevated,
          backgroundImage: "none",
        },
      },
    },
  },
});

export const monoFont = '"JetBrains Mono", "Consolas", monospace';

export default theme;
