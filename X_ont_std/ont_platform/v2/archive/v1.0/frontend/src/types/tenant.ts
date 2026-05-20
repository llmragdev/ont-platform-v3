export type TenantRole = "admin" | "editor" | "viewer";

export interface Permissions {
  can_edit_diagram: boolean;
  can_edit_ontology: boolean;
  can_upload_doc: boolean;
  can_delete_doc: boolean;
  can_manage_users: boolean;
  can_view_audit_log: boolean;
}

export interface TenantUser {
  id: string;
  name: string;
  company_id: string;
  role: TenantRole;
  project_ids: string[];
  permission_override?: Partial<Permissions>;
  permissions: Permissions; // 서버가 resolve해서 반환
}

export interface Company {
  id: string;
  name: string;
  description: string;
}

export interface TenantProject {
  id: string;
  company_id: string;
  name: string;
  description: string;
  created_by: string;
  created_at: string;
}

export interface UserContextValue {
  user: TenantUser | null;
  permissions: Permissions;
  company: Company | null;
  projects: TenantProject[];
  currentProject: TenantProject | null;
  allUsers: TenantUser[];          // UserSwitcher 드롭다운용
  switchUser: (id: string) => Promise<void>;
  switchProject: (id: string) => void;
}

export const DEFAULT_PERMISSIONS: Permissions = {
  can_edit_diagram: false,
  can_edit_ontology: false,
  can_upload_doc: false,
  can_delete_doc: false,
  can_manage_users: false,
  can_view_audit_log: false,
};
