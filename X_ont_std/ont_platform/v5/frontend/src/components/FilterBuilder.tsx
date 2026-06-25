"use client";

import { Plus, Wand2 } from "lucide-react";
import { useState } from "react";

type Operator = "=" | "!=" | ">" | "<" | ">=" | "<=" | "LIKE";
type Joiner = "AND" | "OR";

interface FilterRule {
  id: string;
  property: string;
  operator: Operator;
  value: string;
  joiner: Joiner;
}

const OPERATORS: Operator[] = ["=", "!=", ">", "<", ">=", "<=", "LIKE"];
const DEFAULT_PROPERTIES = ["name", "status", "type", "cost", "owner", "updated_at"];

function toVariable(property: string): string {
  return `?${property.replace(/[^a-zA-Z0-9_]/g, "_")}`;
}

function formatValue(value: string): string {
  if (/^-?\d+(\.\d+)?$/.test(value)) return value;
  return `"${value.replace(/"/g, '\\"')}"`;
}

function ruleToSparql(rule: FilterRule): string {
  const variable = toVariable(rule.property);
  if (rule.operator === "LIKE") {
    return `REGEX(STR(${variable}), "${rule.value.replace(/"/g, '\\"')}", "i")`;
  }
  return `${variable} ${rule.operator} ${formatValue(rule.value)}`;
}

export function FilterBuilder({
  onApply,
}: {
  onApply: (snippet: string) => void;
}) {
  const [rules, setRules] = useState<FilterRule[]>([
    { id: "rule-1", property: "status", operator: "=", value: "active", joiner: "AND" },
  ]);

  const snippet = rules
    .filter((rule) => rule.property && rule.value)
    .map((rule, index) => `${index === 0 ? "" : ` ${rule.joiner} `}${ruleToSparql(rule)}`)
    .join("");

  function updateRule(id: string, patch: Partial<FilterRule>) {
    setRules((prev) => prev.map((rule) => (rule.id === id ? { ...rule, ...patch } : rule)));
  }

  function addRule(joiner: Joiner) {
    setRules((prev) => [
      ...prev,
      {
        id: `rule-${Date.now()}`,
        property: "name",
        operator: "LIKE",
        value: "",
        joiner,
      },
    ]);
  }

  function removeRule(id: string) {
    setRules((prev) => prev.filter((rule) => rule.id !== id));
  }

  return (
    <section data-testid="filter-builder" className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Wand2 className="h-4 w-4 text-slate-500" />
          <h3 className="text-sm font-semibold">필터 빌더</h3>
        </div>
        <button type="button" data-testid="filter-apply-button" className="btn btn-primary py-1 text-xs gap-1" onClick={() => onApply(`FILTER (${snippet})`)}>
          <Plus className="h-3.5 w-3.5" />
          Apply
        </button>
      </div>
      <div className="panel-body space-y-3">
        {rules.map((rule, index) => (
          <div key={rule.id} className="grid grid-cols-[64px_1fr_76px_1fr_28px] gap-2">
            <select
              className="rounded-md border border-slate-200 px-2 py-1.5 text-xs"
              value={rule.joiner}
              onChange={(event) => updateRule(rule.id, { joiner: event.target.value as Joiner })}
              disabled={index === 0}
              aria-label="joiner"
            >
              <option>AND</option>
              <option>OR</option>
            </select>
            <input
              list="sparql-filter-properties"
              data-testid="filter-property-input"
              className="rounded-md border border-slate-200 px-2 py-1.5 text-xs"
              value={rule.property}
              onChange={(event) => updateRule(rule.id, { property: event.target.value })}
              aria-label="property"
            />
            <select
              data-testid="filter-operator-select"
              className="rounded-md border border-slate-200 px-2 py-1.5 text-xs"
              value={rule.operator}
              onChange={(event) => updateRule(rule.id, { operator: event.target.value as Operator })}
              aria-label="operator"
            >
              {OPERATORS.map((operator) => (
                <option key={operator}>{operator}</option>
              ))}
            </select>
            <input
              data-testid="filter-value-input"
              className="rounded-md border border-slate-200 px-2 py-1.5 text-xs"
              value={rule.value}
              onChange={(event) => updateRule(rule.id, { value: event.target.value })}
              placeholder="value"
              aria-label="value"
            />
            <button
              type="button"
              className="rounded-md border border-slate-200 text-xs text-slate-400 hover:text-rose-600"
              onClick={() => removeRule(rule.id)}
              aria-label="remove filter"
            >
              x
            </button>
          </div>
        ))}

        <datalist id="sparql-filter-properties">
          {DEFAULT_PROPERTIES.map((property) => (
            <option key={property} value={property} />
          ))}
        </datalist>

        <div className="flex gap-2">
          <button type="button" className="btn btn-ghost py-1 text-xs" onClick={() => addRule("AND")}>
            + AND
          </button>
          <button type="button" className="btn btn-ghost py-1 text-xs" onClick={() => addRule("OR")}>
            + OR
          </button>
        </div>

        <pre data-testid="filter-preview" className="overflow-auto rounded-md bg-slate-100 p-3 text-xs text-slate-700">
          {snippet ? `FILTER (${snippet})` : "FILTER (...)"}
        </pre>
      </div>
    </section>
  );
}
