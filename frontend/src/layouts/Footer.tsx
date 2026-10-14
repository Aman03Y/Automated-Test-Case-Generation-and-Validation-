import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="py-6 px-8 border-t border-slate-800/80 bg-slate-950/80 text-xs text-slate-500 flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
      <div>
        <span className="font-semibold text-slate-400">
          AI Automated QA Engine
        </span>{' '}
        &copy; {new Date().getFullYear()} Enterprise Edition
      </div>
      <div className="flex space-x-4 text-slate-500 font-mono text-[11px]">
        <span>FastAPI</span>
        <span>&bull;</span>
        <span>SentenceTransformers NLP</span>
        <span>&bull;</span>
        <span>Auto-Fix Engine</span>
      </div>
    </footer>
  );
};
