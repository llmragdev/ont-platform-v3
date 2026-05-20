"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Database, 
  Search, 
  Settings, 
  Layers, 
  FileText, 
  Cpu, 
  MessageSquare,
  Combine
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const menuItems = [
    { icon: <LayoutDashboard size={20} />, label: "Dashboard", href: "/" },
    { icon: <Database size={20} />, label: "온톨로지 설정", href: "/ontology" },
    { icon: <Settings size={20} />, label: "Q&A 설정", href: "/qa-settings" },
    { icon: <MessageSquare size={20} />, label: "RAG Q&A 질의", href: "/rag-query" },
    { icon: <Cpu size={20} />, label: "온톨로지 Q&A 질의", href: "/ontology-query" },
    { icon: <Combine size={20} />, label: "통합 질의", href: "/hybrid-query" },
  ];

  return (
    <aside className="w-72 border-r border-[var(--glass-border)] bg-[var(--glass-bg)] backdrop-blur-xl flex flex-col p-6 hidden md:flex sticky top-0 h-screen">
      <div className="flex items-center gap-3 mb-10">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.5)]">
          <Layers className="text-white w-5 h-5" />
        </div>
        <span className="font-bold text-xl tracking-tight glow-text">Antigravity</span>
      </div>

      <nav className="flex-1 space-y-2">
        {menuItems.map((item) => (
          <Link key={item.href} href={item.href}>
            <div className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all ${
              pathname === item.href 
                ? "bg-primary text-white shadow-[0_0_15px_rgba(59,130,246,0.3)]" 
                : "text-gray-400 hover:bg-white/5 hover:text-white"
            }`}>
              {item.icon}
              <span className="font-medium">{item.label}</span>
            </div>
          </Link>
        ))}
      </nav>

      <div className="mt-auto p-4 rounded-xl bg-white/5 border border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-secondary p-[1px]">
            <div className="w-full h-full rounded-full bg-[#0a0a0c] flex items-center justify-center text-xs font-bold">
              JD
            </div>
          </div>
          <div className="overflow-hidden">
            <p className="text-sm font-medium truncate">Jane Doe</p>
            <p className="text-xs text-gray-400 truncate">Enterprise Admin</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
