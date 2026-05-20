"use client";
import { useState } from "react";
import { api } from "@/lib/api";

export interface ActionButtonProps {
  docId: string;
  entityId: string;
  action: string;
  onSuccess?: (result: any) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
  variant?: "ok" | "warn" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function ActionButton({
  docId,
  entityId,
  action,
  onSuccess,
  onError,
  disabled = false,
  variant = "ghost",
  size = "sm",
  showLabel = true,
}: ActionButtonProps) {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    if (disabled || loading) return;

    setLoading(true);
    try {
      const res = await api.workflowExecute(docId, entityId, action);
      onSuccess?.(res);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      onError?.(message);
    } finally {
      setLoading(false);
    }
  }

  const sizeClass = {
    sm: "text-xs py-1 px-2",
    md: "text-sm py-2 px-3",
    lg: "text-base py-2.5 px-4",
  }[size];

  const variantClass = {
    ok: "btn-ok",
    warn: "btn-warn",
    danger: "btn-danger",
    ghost: "btn-ghost",
  }[variant];

  return (
    <button
      type="button"
      className={`btn ${variantClass} ${sizeClass}`}
      disabled={disabled || loading}
      onClick={handleClick}
    >
      {loading ? "…" : showLabel ? action : ""}
    </button>
  );
}
