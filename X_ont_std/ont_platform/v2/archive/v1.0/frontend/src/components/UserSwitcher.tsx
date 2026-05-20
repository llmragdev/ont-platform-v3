"use client";
import type { User } from "@/types/api";

export function UserSwitcher({
  users,
  current,
  onChange,
  authMode,
  onLogout,
}: {
  users: User[];
  current: string;
  onChange: (key: string) => void;
  authMode?: "demo" | "jwt";
  onLogout?: () => void;
}) {
  // JWT 모드: 현재 로그인된 사용자 표시 + 로그아웃 버튼
  if (authMode === "jwt") {
    const me = users.find((u) => (u.key ?? u.id) === current);
    return (
      <div className="flex items-center gap-2">
        <span className="badge badge-low text-xs">
          {me ? `${me.name} (${me.role})` : current}
        </span>
        <button className="btn btn-ghost text-xs py-1 px-2" onClick={onLogout}>
          로그아웃
        </button>
      </div>
    );
  }
  // 데모 모드: 셀렉트 (기존)
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-slate-500">사용자 (데모)</span>
      <select
        value={current}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
      >
        {users.map((user) => (
          <option key={user.key ?? user.id} value={user.key ?? user.id}>
            {user.name} ({user.role})
          </option>
        ))}
      </select>
    </div>
  );
}
