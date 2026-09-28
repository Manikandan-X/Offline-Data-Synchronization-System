import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { Snackbar, Alert } from "@mui/material";

type Severity = "success" | "error" | "info" | "warning";

interface NotificationContextValue {
  notify: (message: string, severity?: Severity) => void;
}

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState<Severity>("success");

  const notify = useCallback((msg: string, sev: Severity = "success") => {
    setMessage(msg);
    setSeverity(sev);
    setOpen(true);
  }, []);

  return (
    <NotificationContext.Provider value={{ notify }}>
      {children}
      <Snackbar
        open={open}
        autoHideDuration={4000}
        onClose={() => setOpen(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert onClose={() => setOpen(false)} severity={severity} variant="filled" sx={{ minWidth: 280 }}>
          {message}
        </Alert>
      </Snackbar>
    </NotificationContext.Provider>
  );
}

export function useNotify(): NotificationContextValue["notify"] {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotify must be used within NotificationProvider");
  return ctx.notify;
}
