"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";

const DEMO_ACCOUNTS = [
  { email: "kim.ops@example.com", password: "analyst", label: "Kim Ops (AccountManager)" },
  { email: "finance.lead@example.com", password: "finance", label: "Finance Lead (FinanceManager)" },
  { email: "viewer@example.com", password: "viewer", label: "Read Only (Viewer)" },
  { email: "admin@example.com", password: "admin", label: "System Admin (Admin)" },
];

export function LoginPanel({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState("kim.ops@example.com");
  const [password, setPassword] = useState("analyst");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e?: React.FormEvent) {
    e?.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await api.login(email, password);
      setToken(res.access_token, res.user as any);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function chooseDemo(account: (typeof DEMO_ACCOUNTS)[number]) {
    setEmail(account.email);
    setPassword(account.password);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md panel">
        <div className="panel-header">
          <h2 className="text-base font-semibold">Ontology Console — 로그인</h2>
        </div>
        <form className="panel-body space-y-3" onSubmit={submit}>
          <label className="block">
            <span className="text-xs text-slate-500">이메일</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              required
            />
          </label>
          <label className="block">
            <span className="text-xs text-slate-500">비밀번호</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              required
            />
          </label>
          {error && <div className="text-xs text-rose-600">{error}</div>}
          <button type="submit" className="btn btn-primary w-full" disabled={busy}>
            {busy ? "로그인 중…" : "로그인"}
          </button>
          <div className="pt-3 border-t border-slate-100">
            <div className="text-xs text-slate-500 mb-2">교육용 데모 계정:</div>
            <div className="grid grid-cols-2 gap-2">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  onClick={() => chooseDemo(acc)}
                  className="btn btn-ghost text-xs py-1 px-2 text-left"
                >
                  {acc.label}
                </button>
              ))}
            </div>
            <div className="mt-3 text-[10px] text-slate-400">
              비밀번호는 계정 라벨과 동일 (analyst / finance / viewer / admin)
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
