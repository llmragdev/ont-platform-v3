"use client";
import { usePermission } from "@/hooks/usePermission";
import type { Permissions } from "@/types/tenant";

/**
 * 권한이 없으면 children을 렌더링하지 않는 게이트 컴포넌트.
 *
 * 삭제·관리 버튼처럼 권한 없는 사용자에게 아예 보여주지 않을 때 사용.
 * 버튼을 disabled 처리만 할 때는 usePermission 훅을 직접 사용.
 *
 * @example
 * <PermissionGate required="can_delete_doc">
 *   <DeleteButton />
 * </PermissionGate>
 */
export function PermissionGate({
  required,
  children,
  fallback = null,
}: {
  required: keyof Permissions;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const allowed = usePermission(required);
  return allowed ? <>{children}</> : <>{fallback}</>;
}
