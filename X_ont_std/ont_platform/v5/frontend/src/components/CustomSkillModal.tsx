import React, { useState } from "react";
import { X } from "lucide-react";
import type { Skill } from "@/types/api";

interface CustomSkillModalProps {
  isOpen: boolean;
  skill?: Skill | null;
  onClose: () => void;
  onSave: (skill: Skill) => Promise<void>;
}

export const CustomSkillModal: React.FC<CustomSkillModalProps> = ({
  isOpen,
  skill,
  onClose,
  onSave,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<Skill>>(
    skill || {
      id: "",
      name: "",
      description: "",
      category: "custom",
      version: "1.0",
      author: "",
      tags: [],
      inputSchema: { type: "object", properties: {}, required: [] },
      outputSchema: { type: "object", properties: {} },
      implementation: { type: "http", endpoint: "" },
    }
  );

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSave = async () => {
    setError(null);
    setLoading(true);

    try {
      if (!formData.id || !formData.name) {
        throw new Error("ID와 이름은 필수입니다.");
      }

      const skillToSave: Skill = {
        id: formData.id,
        name: formData.name,
        description: formData.description || "",
        category: formData.category || "custom",
        version: formData.version || "1.0",
        author: formData.author || "",
        tags: formData.tags || [],
        inputSchema: formData.inputSchema || {},
        outputSchema: formData.outputSchema || {},
        implementation: formData.implementation || { type: "http" },
      };

      await onSave(skillToSave);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white p-4">
          <h2 className="text-lg font-bold text-slate-900">
            {skill ? "스킬 편집" : "새 커스텀 스킬"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg hover:bg-slate-100 p-2 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4 p-4">
          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm font-semibold text-rose-700">
              {error}
            </div>
          )}

          {/* Basic Info */}
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
                Skill ID *
              </span>
              <input
                type="text"
                disabled={!!skill}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                value={formData.id || ""}
                onChange={(e) => handleChange("id", e.target.value)}
                placeholder="e.g., my-skill-1"
              />
            </label>

            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
                이름 *
              </span>
              <input
                type="text"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                value={formData.name || ""}
                onChange={(e) => handleChange("name", e.target.value)}
                placeholder="스킬 이름"
              />
            </label>

            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
                카테고리
              </span>
              <input
                type="text"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                value={formData.category || ""}
                onChange={(e) => handleChange("category", e.target.value)}
                placeholder="e.g., integration, data, search"
              />
            </label>

            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
                버전
              </span>
              <input
                type="text"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                value={formData.version || ""}
                onChange={(e) => handleChange("version", e.target.value)}
                placeholder="1.0"
              />
            </label>
          </div>

          {/* Description */}
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
              설명
            </span>
            <textarea
              rows={3}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              value={formData.description || ""}
              onChange={(e) => handleChange("description", e.target.value)}
              placeholder="스킬의 목적과 사용 사례를 설명합니다"
            />
          </label>

          {/* Implementation Type */}
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
              구현 타입
            </span>
            <select
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              value={formData.implementation?.type || "http"}
              onChange={(e) =>
                handleChange("implementation", {
                  ...formData.implementation,
                  type: e.target.value,
                })
              }
            >
              <option value="http">HTTP</option>
              <option value="mcp_http">MCP HTTP</option>
              <option value="builtin">Built-in</option>
              <option value="custom" disabled>
                Custom Code (Phase 2+)
              </option>
            </select>
          </label>

          {/* Endpoint (for HTTP/MCP_HTTP) */}
          {(formData.implementation?.type === "http" ||
            formData.implementation?.type === "mcp_http") && (
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
                Endpoint
              </span>
              <input
                type="text"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                value={formData.implementation?.endpoint || ""}
                onChange={(e) =>
                  handleChange("implementation", {
                    ...formData.implementation,
                    endpoint: e.target.value,
                  })
                }
                placeholder="http://example.com/api/endpoint"
              />
            </label>
          )}

          {/* Input Schema */}
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
              Input Schema (JSON)
            </span>
            <textarea
              rows={4}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono text-xs"
              value={JSON.stringify(formData.inputSchema || {}, null, 2)}
              onChange={(e) => {
                try {
                  handleChange("inputSchema", JSON.parse(e.target.value));
                } catch {
                  // silently fail on invalid JSON
                }
              }}
              placeholder={'{\n  "type": "object",\n  "properties": {}\n}'}
            />
          </label>

          {/* Output Schema */}
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
              Output Schema (JSON)
            </span>
            <textarea
              rows={4}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono text-xs"
              value={JSON.stringify(formData.outputSchema || {}, null, 2)}
              onChange={(e) => {
                try {
                  handleChange("outputSchema", JSON.parse(e.target.value));
                } catch {
                  // silently fail on invalid JSON
                }
              }}
              placeholder={'{\n  "type": "object",\n  "properties": {}\n}'}
            />
          </label>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 flex justify-end gap-2 border-t border-slate-200 bg-slate-50 p-4">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 rounded-lg border border-slate-200 bg-white text-sm font-bold text-slate-700 hover:bg-slate-50 transition disabled:opacity-50"
          >
            취소
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-teal-700 text-sm font-bold text-white hover:bg-teal-800 transition disabled:opacity-50"
          >
            {loading ? "저장 중..." : "저장"}
          </button>
        </div>
      </div>
    </div>
  );
};
