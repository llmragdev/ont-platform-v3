"use client";
import { useUserContext } from "@/context/UserContext";

const ROLE_LABEL: Record<string, string> = {
  admin: "관리자",
  editor: "편집자",
  viewer: "뷰어",
};

const ROLE_COLOR: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700",
  editor: "bg-blue-100 text-blue-700",
  viewer: "bg-slate-100 text-slate-600",
};

/**
 * 테넌트 사용자 전환 드롭다운.
 * 회사별로 그룹핑하고, 현재 사용자에 체크 표시.
 * 기존 워크플로우 UserSwitcher와 독립적으로 동작.
 */
export function TenantUserSwitcher() {
  const { user, allUsers, switchUser, company } = useUserContext();

  if (!allUsers.length) return null;

  // 회사별 그룹핑
  const grouped = allUsers.reduce<Record<string, typeof allUsers>>((acc, u) => {
    const cid = u.company_id;
    if (!acc[cid]) acc[cid] = [];
    acc[cid].push(u);
    return acc;
  }, {});

  const companyNames: Record<string, string> = {
    default: "Default",
    acme: "ACME Corp",
    globex: "Globex Corp",
  };

  return (
    <div className="relative group">
      {/* 트리거 버튼 */}
      <button className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm hover:bg-slate-50 transition-colors">
        <span className="font-medium text-slate-700">
          {user?.name ?? "사용자 선택"}
        </span>
        {user && (
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              ROLE_COLOR[user.role] ?? "bg-slate-100 text-slate-600"
            }`}
          >
            {ROLE_LABEL[user.role] ?? user.role}
          </span>
        )}
        <svg className="h-4 w-4 text-slate-400" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.17l3.71-3.94a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
        </svg>
      </button>

      {/* 드롭다운 */}
      <div className="absolute right-0 top-full z-50 mt-1 hidden w-56 rounded-xl border border-slate-200 bg-white py-1 shadow-lg group-hover:block group-focus-within:block">
        {/* 현재 회사 표시 */}
        {company && (
          <div className="border-b border-slate-100 px-3 py-2">
            <p className="text-xs text-slate-500">현재 테넌트</p>
            <p className="text-sm font-semibold text-slate-700">{company.name}</p>
          </div>
        )}

        {/* 회사별 그룹 */}
        {Object.entries(grouped).map(([companyId, users]) => (
          <div key={companyId}>
            <p className="px-3 pt-2 pb-1 text-xs font-medium text-slate-400 uppercase tracking-wide">
              {companyNames[companyId] ?? companyId}
            </p>
            {users.map((u) => {
              const isActive = u.id === user?.id;
              return (
                <button
                  key={u.id}
                  onClick={() => switchUser(u.id)}
                  className={`flex w-full items-center justify-between px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    {isActive && (
                      <svg className="h-3.5 w-3.5 text-indigo-500" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                      </svg>
                    )}
                    {!isActive && <span className="w-3.5" />}
                    {u.name}
                  </span>
                  <span
                    className={`rounded-full px-1.5 py-0.5 text-xs ${
                      ROLE_COLOR[u.role] ?? "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {ROLE_LABEL[u.role] ?? u.role}
                  </span>
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
