"use client";

import React from "react";
import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  Database, 
  Search, 
  Settings, 
  ChevronRight, 
  Activity, 
  ShieldCheck, 
  Layers 
} from "lucide-react";

export default function DashboardPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 },
  };

  return (
    <div className="p-8">
      <header className="flex justify-between items-center mb-10">
          <div>
            <h1 className="mb-1">Project Dashboard</h1>
            <p className="text-gray-400 text-sm">Welcome back. Here is what's happening with your ontology today.</p>
          </div>
          <div className="flex gap-4">
            <div className="glass-card px-4 py-2 flex items-center gap-2 cursor-pointer">
              <ShieldCheck className="text-accent w-4 h-4" />
              <span className="text-sm font-medium">Tenant: Global_Finance</span>
            </div>
          </div>
        </header>

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
        >
          {/* Stats Cards */}
          <StatCard 
            variants={itemVariants}
            title="Active Entities" 
            value="12,482" 
            change="+12% from last week"
            icon={<Database className="text-primary" />}
          />
          <StatCard 
            variants={itemVariants}
            title="Relationships" 
            value="84,291" 
            change="+5.2% from last week"
            icon={<Layers className="text-secondary" />}
          />
          <StatCard 
            variants={itemVariants}
            title="Query Latency" 
            value="142ms" 
            change="-18ms improvement"
            icon={<Activity className="text-accent" />}
          />
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Hybrid Query Console Placeholder */}
          <motion.div 
            variants={itemVariants}
            initial="hidden"
            animate="visible"
            className="glass-card p-6 flex flex-col"
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Search size={18} className="text-primary" />
                Hybrid Query Console
              </h3>
              <span className="text-xs bg-primary/20 text-primary px-2 py-1 rounded-full font-bold">LIVE</span>
            </div>
            
            <div className="flex-1 bg-black/40 rounded-xl border border-white/5 p-4 font-mono text-sm text-gray-300 min-h-[200px]">
              <p className="text-primary opacity-50 mb-2">// Enter your natural language query...</p>
              <div className="flex items-center gap-2">
                <span className="text-secondary">{">"}</span>
                <span className="animate-pulse w-2 h-5 bg-primary/50" />
              </div>
            </div>
            
            <div className="mt-4 flex gap-3">
              <button className="flex-1 bg-primary hover:bg-primary/80 text-white font-bold py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)]">
                Execute Hybrid Search
              </button>
            </div>
          </motion.div>

          {/* Ontology Preview Placeholder */}
          <motion.div 
            variants={itemVariants}
            initial="hidden"
            animate="visible"
            className="glass-card p-6"
          >
            <h3 className="text-lg font-semibold mb-6">Recent Ontology Updates</h3>
            <div className="space-y-4">
              <UpdateItem label="Person -> worksAt -> Company" time="2 mins ago" type="relationship" />
              <UpdateItem label="Asset_Portfolio" time="15 mins ago" type="entity" />
              <UpdateItem label="Transaction_Flow" time="1 hour ago" type="entity" />
              <UpdateItem label="Risk_Factor -> influences -> Market" time="3 hours ago" type="relationship" />
            </div>
            <button className="w-full mt-6 text-sm text-gray-400 hover:text-white flex items-center justify-center gap-1 transition-colors">
              View all updates <ChevronRight size={14} />
            </button>
          </motion.div>
        </div>
      </section>
    </div>
  );
}

function NavItem({ icon, label, active = false }: { icon: React.ReactNode, label: string, active?: boolean }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all ${
      active ? "bg-primary text-white shadow-[0_0_15px_rgba(59,130,246,0.3)]" : "text-gray-400 hover:bg-white/5 hover:text-white"
    }`}>
      {icon}
      <span className="font-medium">{label}</span>
    </div>
  );
}

function StatCard({ title, value, change, icon, variants }: any) {
  return (
    <motion.div variants={variants} className="glass-card p-6">
      <div className="flex justify-between items-start mb-4">
        <div className="p-2 bg-white/5 rounded-lg border border-white/10">
          {icon}
        </div>
        <span className="text-xs text-accent font-medium">{change}</span>
      </div>
      <p className="text-gray-400 text-sm font-medium mb-1">{title}</p>
      <p className="text-3xl font-bold">{value}</p>
    </motion.div>
  );
}

function UpdateItem({ label, time, type }: { label: string, time: string, type: 'entity' | 'relationship' }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors border border-transparent hover:border-white/5">
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${type === 'entity' ? 'bg-primary' : 'bg-secondary'}`} />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <span className="text-xs text-gray-500">{time}</span>
    </div>
  );
}
