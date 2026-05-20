"use client";
import { useUserContext } from "@/context/UserContext";

const PERMISSIONS: Record<string, string[]> = {
  can_edit_ontology: ["Admin", "FinanceManager"],
  can_edit_diagram: ["Admin", "FinanceManager", "AccountManager"],
  can_run_workflow: ["Admin", "FinanceManager", "AccountManager"],
  can_delete: ["Admin"],
  can_view_audit: ["Admin", "FinanceManager"],
};

export function usePermission(permission: string): boolean {
  const { user } = useUserContext();
  const allowed = PERMISSIONS[permission] ?? [];
  return allowed.includes(user.role);
}
