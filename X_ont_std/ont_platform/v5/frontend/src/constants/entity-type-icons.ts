import type { EntityTypeName } from "@/types/api";
import {
  Lightbulb,
  Settings,
  Package,
  Users,
  Building2,
  Cpu,
  Zap,
  FileText,
  HelpCircle,
  LucideIcon,
} from "lucide-react";

export const ENTITY_TYPE_CONFIG: Record<
  string,
  {
    icon: LucideIcon;
    label: string;
    bgColor: string;
    textColor: string;
    borderColor: string;
  }
> = {
  CONCEPT: {
    icon: Lightbulb,
    label: "개념",
    bgColor: "bg-blue-50",
    textColor: "text-blue-900",
    borderColor: "border-blue-200",
  },
  PROPERTY: {
    icon: Settings,
    label: "속성",
    bgColor: "bg-gray-50",
    textColor: "text-gray-900",
    borderColor: "border-gray-200",
  },
  INSTANCE: {
    icon: Package,
    label: "실체",
    bgColor: "bg-cyan-50",
    textColor: "text-cyan-900",
    borderColor: "border-cyan-200",
  },
  PERSON: {
    icon: Users,
    label: "인물",
    bgColor: "bg-slate-50",
    textColor: "text-slate-900",
    borderColor: "border-slate-200",
  },
  ORGANIZATION: {
    icon: Building2,
    label: "기관",
    bgColor: "bg-slate-50",
    textColor: "text-slate-900",
    borderColor: "border-slate-200",
  },
  SYSTEM: {
    icon: Cpu,
    label: "시스템",
    bgColor: "bg-purple-50",
    textColor: "text-purple-900",
    borderColor: "border-purple-200",
  },
  METHOD: {
    icon: Zap,
    label: "방법",
    bgColor: "bg-orange-50",
    textColor: "text-orange-900",
    borderColor: "border-orange-200",
  },
  DOCUMENT: {
    icon: FileText,
    label: "문서",
    bgColor: "bg-amber-50",
    textColor: "text-amber-900",
    borderColor: "border-amber-200",
  },
  UNKNOWN: {
    icon: HelpCircle,
    label: "알수없음",
    bgColor: "bg-gray-50",
    textColor: "text-gray-900",
    borderColor: "border-gray-200",
  },
};

// Fallback 설정
const FALLBACK_CONFIG = {
  icon: HelpCircle,
  label: "항목",
  bgColor: "bg-gray-50",
  textColor: "text-gray-900",
  borderColor: "border-gray-200",
};

export function getEntityTypeIcon(type: EntityTypeName | string) {
  return ENTITY_TYPE_CONFIG[type]?.icon || FALLBACK_CONFIG.icon;
}

export function getEntityTypeConfig(type: EntityTypeName | string) {
  return ENTITY_TYPE_CONFIG[type] || FALLBACK_CONFIG;
}

export function getEntityTypeLabel(type: EntityTypeName | string) {
  return ENTITY_TYPE_CONFIG[type]?.label || FALLBACK_CONFIG.label;
}
