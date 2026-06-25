import React, { useState, useCallback } from "react";
import { Skill } from "@/types/api";

interface InputMappingEditorProps {
  skillId: string;
  skill: Skill | null;
  inputMapping: Record<string, any>;
  onUpdateMapping: (mapping: Record<string, any>) => void;
  previousNodeOutputs: Record<string, Record<string, any>>;
}

export const InputMappingEditor: React.FC<InputMappingEditorProps> = ({
  skillId,
  skill,
  inputMapping,
  onUpdateMapping,
  previousNodeOutputs,
}) => {
  const [validationResults, setValidationResults] = useState<Record<string, boolean>>({});
  const [expandedField, setExpandedField] = useState<string | null>(null);

  if (!skill || !skill.inputSchema) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500">
        스킬 정보를 로드할 수 없습니다.
      </div>
    );
  }

  const inputSchema = skill.inputSchema as any;
  const properties = inputSchema.properties || {};
  const requiredFields = inputSchema.required || [];

  const handleFieldChange = (fieldName: string, value: any) => {
    const newMapping = { ...inputMapping };
    newMapping[fieldName] = value;
    onUpdateMapping(newMapping);
    validateExpression(fieldName, value);
  };

  const validateExpression = async (fieldName: string, value: string) => {
    if (!value.includes("{{")) {
      setValidationResults((prev) => ({ ...prev, [fieldName]: true }));
      return;
    }

    try {
      const response = await fetch("/api/skills/validate-expression", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          expression: value,
          executionContext: { nodes: previousNodeOutputs },
        }),
      });

      const data = await response.json();
      setValidationResults((prev) => ({ ...prev, [fieldName]: data.valid }));
    } catch (error) {
      console.error("Expression validation error:", error);
      setValidationResults((prev) => ({ ...prev, [fieldName]: false }));
    }
  };

  const getAvailableOutputs = (): Array<{ path: string; type: string }> => {
    const outputs: Array<{ path: string; type: string }> = [];
    Object.entries(previousNodeOutputs).forEach(([nodeId, nodeOutput]) => {
      if (nodeOutput && typeof nodeOutput === "object") {
        Object.entries(nodeOutput).forEach(([key, value]) => {
          outputs.push({
            path: `{{nodes.${nodeId}.output.${key}}}`,
            type: typeof value,
          });
        });
      }
    });
    return outputs;
  };

  const availableOutputs = getAvailableOutputs();

  return (
    <div className="space-y-4">
      <div>
        <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 mb-3">
          Input Binding ({skill.id})
        </div>
      </div>

      <div className="space-y-3 border-t border-slate-200 pt-3">
        {Object.entries(properties).map(([fieldName, fieldSchema]: [string, any]) => {
          const isRequired = requiredFields.includes(fieldName);
          const currentValue = inputMapping[fieldName] ?? "";
          const isValid = validationResults[fieldName] !== false;
          const isExpression = String(currentValue).includes("{{");

          return (
            <div key={fieldName} className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-700">
                  {fieldName}
                  {isRequired && <span className="text-red-500 ml-1">*</span>}
                </label>
                {isExpression && (
                  <span
                    className={`text-[8px] font-mono px-1.5 py-0.5 rounded ${
                      isValid
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {isValid ? "✓" : "✗"}
                  </span>
                )}
              </div>

              <textarea
                rows={currentValue.includes("\n") ? 3 : 1}
                className={`w-full font-mono text-xs p-2 rounded-lg border ${
                  isExpression && !isValid
                    ? "border-red-300 bg-red-50"
                    : "border-slate-200 bg-white"
                } focus:outline-none focus:ring-2 focus:ring-teal-500`}
                value={currentValue}
                onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                placeholder={fieldSchema.description || `입력 또는 {{nodes.xxx.output.yyy}}`}
              />

              {fieldSchema.enum && (
                <div className="flex gap-1 flex-wrap">
                  {fieldSchema.enum.map((opt: string) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleFieldChange(fieldName, opt)}
                      className="text-[10px] px-2 py-1 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 hover:border-slate-300 transition"
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              )}

              {availableOutputs.length > 0 && (
                <button
                  type="button"
                  onClick={() =>
                    setExpandedField(expandedField === fieldName ? null : fieldName)
                  }
                  className="text-[9px] text-teal-600 hover:text-teal-700 font-semibold"
                >
                  {expandedField === fieldName
                    ? "▼ 이전 노드 출력 숨기기"
                    : "▶ 이전 노드 출력 보기"}
                </button>
              )}

              {expandedField === fieldName && availableOutputs.length > 0 && (
                <div className="bg-slate-50 rounded-lg p-2 space-y-1 max-h-32 overflow-y-auto">
                  {availableOutputs.map((output) => (
                    <button
                      key={output.path}
                      type="button"
                      onClick={() => handleFieldChange(fieldName, output.path)}
                      className="block w-full text-left text-[9px] font-mono p-1.5 rounded hover:bg-teal-100 hover:text-teal-800 transition"
                    >
                      <div className="truncate">{output.path}</div>
                      <div className="text-[8px] text-slate-500">({output.type})</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-[10px] leading-4 text-slate-600">
        <div className="font-bold mb-1">사용 방법:</div>
        <ul className="space-y-1 ml-4 list-disc">
          <li>
            <strong>리터럴 값:</strong> 직접 텍스트 입력
          </li>
          <li>
            <strong>표현식:</strong> <code>{"{{nodes.node-id.output.field}}"}</code> 형식
          </li>
          <li>
            <strong>혼합:</strong> <code>{"Equipment: {{nodes.asset.output.name}}"}</code>
          </li>
        </ul>
      </div>
    </div>
  );
};
