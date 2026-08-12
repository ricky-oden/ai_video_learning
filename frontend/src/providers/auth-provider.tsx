"use client";

import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  apiRequest,
  clearStoredToken,
  getStoredToken,
  storeToken,
} from "@/lib/api/client";
import type { LoginResponse, User } from "@/lib/api/types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function restore() {
      if (!getStoredToken()) {
        setLoading(false);
        return;
      }
      try {
        const currentUser = await apiRequest<User>("/auth/me");
        if (active) setUser(currentUser);
      } catch {
        if (active) setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    }
    void restore();
    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      async login(email, password) {
        const response = await apiRequest<LoginResponse>("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        storeToken(response.access_token);
        setUser(response.user);
        return response.user;
      },
      async logout() {
        try {
          await apiRequest<{ status: "revoked" }>("/auth/logout", {
            method: "POST",
          });
        } finally {
          clearStoredToken();
          setUser(null);
        }
      },
    }),
    [loading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
