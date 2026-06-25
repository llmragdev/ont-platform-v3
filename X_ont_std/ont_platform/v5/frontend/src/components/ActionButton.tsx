"use client";

import { CheckCircle2, Loader2, Play, XCircle } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";

export interface WorkflowAction {
  name: string;
  display: string;
  required_params: string[];
}

export interface ActionButtonProps {
  entityId: string;
  entityType?: string;
  currentStatus?: string;
  availableActions?: WorkflowAction[];
  onActionClick?: (action: string, params: Record<string, unknown>) => void;
  loading?: boolean;
  disabled?: boolean;
  domainId?: string;
  onSuccess?: (result: any) => void;
  onError?: (error: string) => void;

  docId?: string;
  action?: string;
  variant?: "ok" | "warn" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

type ToastState = { kind: "success" | "error"; text: string } | null;

const PARAM_LABELS: Record<string, string> = {
  approver: "Approver",
  reviewer: "Reviewer",
  reason: "Reason",
  new_deadline: "New deadline",
  deadline: "Deadline",
  amount: "Amount",
};

function inputTypeFor(param: string): string {
  if (param.includes("deadline") || param.includes("date")) return "date";
  if (param.includes("amount") || param.includes("count") || param.includes("price")) return "number";
  return "text";
}

function isLongTextParam(param: string): boolean {
  return param.includes("reason") || param.includes("comment") || param.includes("note");
}

function legacyVariantClass(variant: NonNullable<ActionButtonProps["variant"]>) {
  return {
    ok: "btn-ok",
    warn: "btn-warn",
    danger: "btn-danger",
    ghost: "btn-ghost",
  }[variant];
}

function sizeClass(size: NonNullable<ActionButtonProps["size"]>) {
  return {
    sm: "text-xs py-1 px-2",
    md: "text-sm py-2 px-3",
    lg: "text-base py-2.5 px-4",
  }[size];
}

export function ActionButton(props: ActionButtonProps) {
  const {
    entityId,
    entityType = "entity",
    currentStatus,
    availableActions,
    loading = false,
    disabled = false,
    domainId = "ai-voucher-2025",
    onActionClick,
    onSuccess,
    onError,
  } = props;
  const [selectedName, setSelectedName] = useState("");
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);

  const selectedAction = useMemo(
    () => availableActions?.find((item) => item.name === selectedName) ?? null,
    [availableActions, selectedName]
  );

  async function runLegacyAction() {
    const legacyAction = props.action;
    const legacyDocId = props.docId;
    if (!legacyAction || !legacyDocId || disabled || submitting) return;

    setSubmitting(true);
    try {
      const res = await api.workflowExecute(legacyDocId, entityId, legacyAction);
      onSuccess?.(res);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      onError?.(message);
    } finally {
      setSubmitting(false);
    }
  }

  async function executeAction() {
    if (!selectedAction || disabled || loading || submitting) return;

    const missing = selectedAction.required_params.find((param) => !String(formData[param] ?? "").trim());
    if (missing) {
      setToast({ kind: "error", text: `${PARAM_LABELS[missing] ?? missing} is required.` });
      return;
    }

    setSubmitting(true);
    setToast(null);
    try {
      onActionClick?.(selectedAction.name, formData);
      const response = await fetch("/api/workflow/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          entity_id: entityId,
          entity_type: entityType,
          domain_id: domainId,
          action: selectedAction.name,
          params: formData,
        }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload?.error?.message ?? payload?.detail ?? response.statusText);
      }

      setToast({ kind: "success", text: `${selectedAction.display} completed.` });
      setFormData({});
      onSuccess?.(payload);
      window.setTimeout(() => setToast(null), 3500);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setToast({ kind: "error", text: message });
      onError?.(message);
    } finally {
      setSubmitting(false);
    }
  }

  if (!availableActions) {
    const busy = submitting || loading;
    return (
      <button
        type="button"
        data-testid="action-button"
        className={`btn ${legacyVariantClass(props.variant ?? "ghost")} ${sizeClass(props.size ?? "sm")}`}
        disabled={disabled || busy}
        onClick={runLegacyAction}
      >
        {busy && <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />}
        {busy ? "Running" : props.showLabel === false ? "" : props.action}
      </button>
    );
  }

  const busy = submitting || loading;
  const canExecute = Boolean(selectedAction) && !disabled && !busy;

  return (
    <div data-testid="action-button" className="space-y-3 rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="grid gap-2 md:grid-cols-[1fr_auto]">
        <div>
          <label className="mb-1 block text-xs font-semibold text-slate-500" htmlFor={`action-select-${entityId}`}>
            Recommended action
          </label>
          <select
            id={`action-select-${entityId}`}
            data-testid="action-select"
            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
            value={selectedName}
            disabled={disabled || busy || availableActions.length === 0}
            onChange={(event) => {
              setSelectedName(event.target.value);
              setFormData({});
              setToast(null);
            }}
          >
            <option value="">Select action</option>
            {availableActions.map((action) => (
              <option key={action.name} value={action.name}>
                {action.display}
              </option>
            ))}
          </select>
          {currentStatus && <div className="mt-1 text-xs text-slate-500">Current status: {currentStatus}</div>}
        </div>
        <button
          type="button"
          data-testid="action-execute"
          className={`btn btn-primary self-end ${disabled ? "bg-slate-300 hover:bg-slate-300" : ""}`}
          disabled={!canExecute}
          onClick={executeAction}
        >
          {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
          Execute
        </button>
      </div>

      {selectedAction && selectedAction.required_params.length > 0 && (
        <div className="grid gap-3 md:grid-cols-2">
          {selectedAction.required_params.map((param) => (
            <div key={param} className={isLongTextParam(param) ? "md:col-span-2" : ""}>
              <label className="mb-1 block text-xs font-semibold text-slate-500" htmlFor={`param-${param}`}>
                {PARAM_LABELS[param] ?? param}
              </label>
              {isLongTextParam(param) ? (
                <textarea
                  id={`param-${param}`}
                  data-testid={`param-${param}`}
                  className="min-h-20 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={formData[param] ?? ""}
                  disabled={busy}
                  onChange={(event) => setFormData((prev) => ({ ...prev, [param]: event.target.value }))}
                />
              ) : (
                <input
                  id={`param-${param}`}
                  data-testid={`param-${param}`}
                  type={inputTypeFor(param)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={formData[param] ?? ""}
                  disabled={busy}
                  onChange={(event) => setFormData((prev) => ({ ...prev, [param]: event.target.value }))}
                />
              )}
            </div>
          ))}
        </div>
      )}

      {toast && (
        <div
          data-testid={toast.kind === "success" ? "success-toast" : "error-toast"}
          className={`flex items-start gap-2 rounded-md border px-3 py-2 text-sm ${
            toast.kind === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-800"
              : "border-rose-200 bg-rose-50 text-rose-800"
          }`}
        >
          {toast.kind === "success" ? <CheckCircle2 className="mt-0.5 h-4 w-4" /> : <XCircle className="mt-0.5 h-4 w-4" />}
          <span>{toast.text}</span>
        </div>
      )}
    </div>
  );
}
