"use client";
import { createContext, useContext, useState, ReactNode } from "react";
import type { TenantConfig, UserRole } from "@/types/api";
import { setCurrentTenant } from "@/lib/api";

interface UserContextValue {
  user: TenantConfig;
  setUser: (cfg: TenantConfig) => void;
  presets: TenantConfig[];
}

const PRESETS: TenantConfig[] = [
  { userId: "alice", companyId: "demo-co", projectId: "proj-01", role: "Admin" },
  { userId: "bob", companyId: "demo-co", projectId: "proj-01", role: "FinanceManager" },
  { userId: "carol", companyId: "demo-co", projectId: "proj-01", role: "AccountManager" },
  { userId: "dave", companyId: "demo-co", projectId: "proj-01", role: "Viewer" },
];

const UserContext = createContext<UserContextValue>({
  user: PRESETS[1],
  setUser: () => {},
  presets: PRESETS,
});

export function UserContextProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<TenantConfig>(PRESETS[1]);

  function setUser(cfg: TenantConfig) {
    setUserState(cfg);
    setCurrentTenant(cfg);
  }

  return (
    <UserContext.Provider value={{ user, setUser, presets: PRESETS }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUserContext() {
  return useContext(UserContext);
}
