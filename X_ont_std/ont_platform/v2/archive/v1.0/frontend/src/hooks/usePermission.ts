import { useUserContext } from "@/context/UserContext";
import type { Permissions } from "@/types/tenant";

/**
 * 현재 테넌트 사용자의 권한 플래그 하나를 반환.
 *
 * @example
 * const canEdit = usePermission("can_edit_diagram");
 * <button disabled={!canEdit}>편집</button>
 */
export function usePermission(flag: keyof Permissions): boolean {
  const { permissions } = useUserContext();
  return permissions[flag] ?? false;
}
