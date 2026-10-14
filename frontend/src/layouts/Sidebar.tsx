import React from "react";
import { NavLink, Link } from "react-router-dom";
import {
  LayoutDashboard,
  FileCheck2,
  ShieldCheck,
  Home,
  Sparkles,
} from "lucide-react";
import { cn } from "../utils/cn";

interface SidebarProps {
  isOpen: boolean;
  onCloseMobile?: () => void;
}

const navItems = [
  { path: "/generate", label: "Test Case Generator", icon: Sparkles },
  { path: "/validate", label: "Validation Engine", icon: LayoutDashboard },
  { path: "/report", label: "PDF Report Generator", icon: FileCheck2 },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onCloseMobile }) => {
  return (
    <aside
      className={cn(
        "fixed top-0 left-0 z-40 h-screen w-64 bg-slate-950/95 backdrop-blur-xl border-r border-slate-800/80 text-white transition-transform duration-300 ease-in-out lg:translate-x-0 flex flex-col justify-between shadow-2xl",
        isOpen ? "translate-x-0" : "-translate-x-full",
      )}
    >
      <div>
        {/* Brand Header */}
        <Link
          to="/"
          className="flex items-center space-x-3 h-16 px-6 bg-slate-950 border-b border-slate-800/80 group transition-colors"
        >
          <div className="p-2 bg-gradient-to-br from-indigo-500 to-emerald-500 rounded-xl text-white shadow-[0_0_15px_rgba(99,102,241,0.4)]">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-extrabold text-sm leading-tight text-white tracking-wide group-hover:text-indigo-200 transition-colors">
              AI Validator
            </h1>
            <p className="text-[10px] text-emerald-400 font-mono tracking-wider uppercase">
              QA Engine Pro
            </p>
          </div>
        </Link>

        {/* Navigation Menu */}
        <nav className="p-4 space-y-1.5 overflow-y-auto max-h-[calc(100vh-12rem)]">
          <Link
            to="/"
            onClick={onCloseMobile}
            className="flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-all duration-150"
          >
            <Home className="w-4 h-4 flex-shrink-0 text-slate-500" />
            <span>Landing Page</span>
          </Link>

          <div className="pt-2 pb-1 px-3 text-[10px] font-mono uppercase tracking-widest text-slate-500">
            Workspaces
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  cn(
                    "flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 border",
                    isActive
                      ? "bg-indigo-600/90 text-white border-indigo-500/50 shadow-lg shadow-indigo-600/30"
                      : "border-transparent text-slate-400 hover:text-white hover:bg-slate-900/80 hover:border-slate-800",
                  )
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Branding */}
      <div className="p-4 border-t border-slate-800/80 text-xs text-slate-500 text-center bg-slate-950/50">
        <div className="flex items-center justify-center gap-2 mb-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] text-slate-400 font-mono">
            System Online
          </span>
        </div>
        <p className="text-[10px] text-slate-600">Enterprise Dark Edition</p>
      </div>
    </aside>
  );
};
