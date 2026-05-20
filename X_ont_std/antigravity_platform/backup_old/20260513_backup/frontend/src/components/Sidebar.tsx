"use client";

import React from "react";
import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  Share2, 
  Search, 
  Settings, 
  ShieldCheck, 
  UserCircle,
  Zap,
  FileText,
  Boxes
} from "lucide-react";
import { cn } from "@/lib/utils";

const roles = [
  { id: "admin", label: "ADM", icon: ShieldCheck, color: "text-rose-500", bg: "bg-rose-50" },
  { id: "approver", label: "APR", icon: Zap, color: "text-amber-500", bg: "bg-amber-50" },
  { id: "analyst", label: "ANA", icon: UserCircle, color: "text-indigo-500", bg: "bg-indigo-50" },
  { id: "viewer", label: "VW", icon: Search, color: "text-slate-500", bg: "bg-slate-50" },
];

const menuItems = [
  { id: "graph", icon: Boxes, label: "Ontology Graph" },
  { id: "documents", icon: FileText, label: "Document Store" },
  { id: "search", icon: Search, label: "Global Search" },
  { id: "settings", icon: Settings, label: "Settings" },
];

export default function Sidebar({ 
  currentRole, 
  onRoleChange,
  currentView,
  onViewChange
}: { 
  currentRole: string, 
  onRoleChange: (r: string) => void,
  currentView: string,
  onViewChange: (v: string) => void
}) {
  return (
    <aside className="w-24 border-r border-slate-200 bg-white flex flex-col items-center py-10 gap-12 z-30">
      {/* App Logo */}
      <div 
        onClick={() => onViewChange("graph")}
        className="p-3 bg-slate-900 rounded-2xl shadow-2xl shadow-slate-200 rotate-3 hover:rotate-0 transition-transform cursor-pointer"
      >
        <LayoutDashboard className="text-white" size={26} />
      </div>

      {/* Main Nav */}
      <nav className="flex-1 flex flex-col gap-8">
        {menuItems.map((item) => (
          <button 
            key={item.id} 
            onClick={() => onViewChange(item.id)}
            className={cn(
              "p-3 rounded-2xl transition-all duration-300 relative group",
              currentView === item.id ? "text-indigo-600 bg-indigo-50 shadow-sm" : "text-slate-300 hover:text-slate-500 hover:bg-slate-50"
            )}
          >
            <item.icon size={24} />
            <div className="absolute left-full ml-4 px-2 py-1 bg-slate-900 text-white text-[10px] font-bold rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
              {item.label}
            </div>
            {currentView === item.id && (
              <motion.div 
                layoutId="activeNav"
                className="absolute -right-3 top-1/2 -translate-y-1/2 w-1 h-3 bg-indigo-500 rounded-full" 
              />
            )}
          </button>
        ))}
      </nav>

      {/* Role Selector */}
      <div className="flex flex-col gap-6 items-center">
        <div className="w-8 h-[1px] bg-slate-100" />
        <div className="flex flex-col gap-3 p-2 bg-slate-50 rounded-[24px] border border-slate-100 shadow-inner">
          {roles.map((role) => (
            <button
              key={role.id}
              onClick={() => onRoleChange(role.id)}
              className={cn(
                "w-12 h-12 flex flex-col items-center justify-center rounded-[18px] transition-all duration-500 relative group",
                currentRole === role.id 
                  ? "bg-white shadow-[0_8px_20px_rgba(0,0,0,0.08)] text-indigo-600 ring-1 ring-slate-100" 
                  : "text-slate-300 hover:text-slate-500"
              )}
            >
              <role.icon size={20} className={cn(currentRole === role.id && role.color)} />
              <span className={cn(
                "text-[7px] font-black mt-1 tracking-tighter",
                currentRole === role.id ? "text-slate-900" : "text-slate-300"
              )}>
                {role.label}
              </span>
              {currentRole === role.id && (
                <motion.div 
                  layoutId="activeRole"
                  className="absolute -right-1 top-1/2 -translate-y-1/2 w-1 h-3 bg-indigo-500 rounded-full" 
                />
              )}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
