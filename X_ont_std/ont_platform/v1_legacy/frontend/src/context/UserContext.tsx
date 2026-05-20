"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type {
  Company,
  Permissions,
  TenantProject,
  TenantUser,
  UserContextValue,
} from "@/types/tenant";
import { DEFAULT_PERMISSIONS as _DEFAULT } from "@/types/tenant";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const STORAGE_KEY = "tenant_user_id";

const Ctx = createContext<UserContextValue>({
  user: null,
  permissions: _DEFAULT,
  company: null,
  projects: [],
  currentProject: null,
  allUsers: [],
  switchUser: async () => {},
  switchProject: () => {},
});

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json() as Promise<T>;
}

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<TenantUser | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [projects, setProjects] = useState<TenantProject[]>([]);
  const [currentProject, setCurrentProject] = useState<TenantProject | null>(null);
  const [allUsers, setAllUsers] = useState<TenantUser[]>([]);

  const permissions: Permissions = user?.permissions ?? _DEFAULT;

  // 모든 사용자 목록 초기 로드 (UserSwitcher용)
  useEffect(() => {
    fetchJson<{ users: TenantUser[] }>("/api/tenant/users")
      .then((d) => setAllUsers(d.users))
      .catch(() => {});
  }, []);

  // 사용자 로드 + company/projects 연쇄 로드
  const loadUser = useCallback(async (userId: string) => {
    try {
      const u = await fetchJson<TenantUser>(`/api/tenant/users/${userId}`);
      setUser(u);
      localStorage.setItem(STORAGE_KEY, userId);

      const [compList, projRes] = await Promise.all([
        fetchJson<{ companies: Company[] }>("/api/tenant/companies").then((d) => d.companies),
        fetchJson<{ projects: TenantProject[] }>(
          `/api/tenant/projects?user_id=${userId}`
        ).then((d) => d.projects),
      ]);
      const compRes = compList.find((c) => c.id === u.company_id) ?? null;

      setCompany(compRes);
      setProjects(projRes);
      setCurrentProject(projRes[0] ?? null);
    } catch {
      // 테넌트 API 미응답 시 무시 (서버 미실행 상태 허용)
    }
  }, []);

  // 초기 로드: localStorage 복원
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY) ?? "analyst";
    loadUser(saved);
  }, [loadUser]);

  const switchUser = useCallback(
    async (id: string) => { await loadUser(id); },
    [loadUser]
  );

  const switchProject = useCallback((id: string) => {
    const found = projects.find((p) => p.id === id);
    if (found) setCurrentProject(found);
  }, [projects]);

  return (
    <Ctx.Provider
      value={{
        user, permissions, company, projects,
        currentProject, allUsers, switchUser, switchProject,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useUserContext() {
  return useContext(Ctx);
}
