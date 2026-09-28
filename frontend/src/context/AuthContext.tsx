import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { authApi } from "@/api/auth";
import { tokenStorage } from "@/api/client";
import type { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// Role id 1 = Admin per the backend's seed order (Admin, User).
const ADMIN_ROLE_ID = 1;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    const token = tokenStorage.get();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      tokenStorage.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (email: string, password: string) => {
    const { access_token } = await authApi.login({ email, password });
    tokenStorage.set(access_token);
    const me = await authApi.me();
    setUser(me);
  };

  const register = async (payload: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }) => {
    await authApi.register(payload);
    await login(payload.email, payload.password);
  };

  const logout = () => {
    tokenStorage.clear();
    setUser(null);
  };

  const isAdmin = user?.role_id === ADMIN_ROLE_ID;

  return (
    <AuthContext.Provider value={{ user, loading, isAdmin, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
