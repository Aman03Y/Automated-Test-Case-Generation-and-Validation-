import React from 'react';
import { Menu, Activity, Sparkles } from 'lucide-react';

interface NavbarProps {
  onToggleSidebar: () => void;
  pageTitle: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  onToggleSidebar,
  pageTitle,
}) => {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 shadow-lg">
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 text-slate-400 hover:text-white lg:hidden rounded-lg hover:bg-slate-900 border border-slate-800"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h2 className="text-xl font-black text-white tracking-tight">
          {pageTitle}
        </h2>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden md:flex items-center space-x-2 bg-emerald-950/50 px-3 py-1.5 rounded-full border border-emerald-500/30">
          <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span className="text-xs font-semibold text-emerald-300">
            Backend API Connected
          </span>
        </div>

        <div className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-950/50 text-indigo-300 border border-indigo-500/30">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>AI Engine Ready</span>
        </div>
      </div>
    </header>
  );
};
