import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileBarChart,
  Download,
  AlertTriangle,
  ChevronRight,
  FileText,
  FileCode,
  CheckCircle2,
  ArrowLeft,
  Sparkles,
} from 'lucide-react';
import type { AutoFixResponse } from '../types';
import { generatePdfReport } from '../utils/generatePdfReport';

// Circular Progress Component
const QualityRing = ({ score }: { score: number }) => {
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center w-20 h-20">
      <svg className="w-full h-full transform -rotate-90">
        <circle
          cx="40"
          cy="40"
          r={radius}
          stroke="currentColor"
          strokeWidth="6"
          fill="transparent"
          className="text-slate-850 text-slate-800"
        />
        <circle
          cx="40"
          cy="40"
          r={radius}
          stroke="currentColor"
          strokeWidth="6"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={
            score >= 80
              ? 'text-emerald-500'
              : score >= 50
              ? 'text-amber-500'
              : 'text-rose-500'
          }
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-lg font-black text-white">{score}</span>
        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-tighter">
          Score
        </span>
      </div>
    </div>
  );
};

// Log Line formatter
const TerminalLine = ({ log }: { log: string }) => {
  let color = 'text-slate-300';
  let tagColor = 'text-slate-500';

  if (log.includes('[EXACT_DUPLICATE]')) {
    color = 'text-rose-300';
    tagColor = 'text-rose-400';
  } else if (log.includes('[SEMANTIC_MERGE]')) {
    color = 'text-amber-300';
    tagColor = 'text-amber-400';
  } else if (log.includes('[ORPHAN_FLAG]')) {
    color = 'text-orange-300';
    tagColor = 'text-orange-400';
  } else if (log.includes('[CLEANED]')) {
    color = 'text-emerald-300';
    tagColor = 'text-emerald-400';
  }

  const match = log.match(/^(\[[^\]]+\])(.*)/);
  if (match) {
    return (
      <div className="font-mono text-xs mb-1.5 flex items-start leading-relaxed hover:bg-slate-900/60 p-1 rounded transition-colors">
        <span className={`${tagColor} font-bold mr-2 whitespace-nowrap`}>
          {match[1]}
        </span>
        <span className={`${color}`}>{match[2]}</span>
      </div>
    );
  }
  return <div className="font-mono text-xs text-slate-400 mb-1">{log}</div>;
};

export const ReportPage: React.FC = () => {
  const [result, setResult] = useState<AutoFixResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [logFilter, setLogFilter] = useState<'all' | 'duplicates' | 'orphans' | 'cleaned'>('all');

  useEffect(() => {
    const saved = localStorage.getItem('latest_validation_report');
    if (saved) {
      try {
        setResult(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse saved report', e);
      }
    }
  }, []);

  const handleDownloadPdf = () => {
    if (!result) return;
    setIsGenerating(true);
    try {
      generatePdfReport(result, 'AI_Validation_Full_Report.pdf');
    } catch (err: any) {
      console.error('PDF Generation failed', err);
      alert('Failed to generate PDF: ' + (err.message || String(err)));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadErrorLogs = () => {
    if (!result) return;
    const content = result.validation_report.join('\n');
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'validation_errors_and_fixes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadCleanedJson = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result.cleaned_test_cases, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cleaned_testcases.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'critical':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'high':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'medium':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'low':
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  if (!result) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center text-center p-8">
        <div className="w-20 h-20 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-6 shadow-xl">
          <FileBarChart className="w-10 h-10 text-indigo-400 animate-pulse" />
        </div>
        <h2 className="text-2xl font-black text-white">No Validation Report Available</h2>
        <p className="mt-3 text-sm text-slate-400 max-w-md leading-relaxed">
          Upload and validate your JSON test suite in the Validation Engine first.
          All audit findings, defects, and auto-fix logs will be ready for export here.
        </p>
        <Link
          to="/validate"
          className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-white bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Go to Validation Engine</span>
        </Link>
      </div>
    );
  }

  const qualityScore = Math.max(
    0,
    Math.round(
      100 - (result.summary.orphans_flagged / Math.max(result.summary.final_count, 1)) * 100
    )
  );

  const filteredLogs = result.validation_report.filter((log) => {
    if (logFilter === 'duplicates') {
      return log.includes('[EXACT_DUPLICATE]') || log.includes('[SEMANTIC_MERGE]');
    }
    if (logFilter === 'orphans') {
      return log.includes('[ORPHAN_FLAG]');
    }
    if (logFilter === 'cleaned') {
      return log.includes('[CLEANED]');
    }
    return true;
  });

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      
      {/* Header & Export Bar */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-xl gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
              <FileBarChart className="w-6 h-6" />
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight">
              Visual & Vector PDF Report Generator
            </h1>
          </div>
          <p className="text-slate-400 text-sm max-w-xl">
            Download the comprehensive QA audit package including all identified errors,
            semantic clones, and complete sanitized test case inventory.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleDownloadPdf}
            disabled={isGenerating}
            className="flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 disabled:opacity-60 text-white px-6 py-3 rounded-xl text-sm font-bold transition shadow-lg shadow-indigo-600/30 cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0"
          >
            <Download className="w-4 h-4" />
            <span>{isGenerating ? 'Compiling PDF...' : 'Download Full PDF Report'}</span>
          </button>

          <button
            onClick={handleDownloadErrorLogs}
            className="flex items-center space-x-2 bg-slate-800/90 hover:bg-slate-750 hover:bg-slate-700 text-slate-200 px-4 py-3 rounded-xl text-sm font-semibold transition border border-slate-700 cursor-pointer"
          >
            <FileText className="w-4 h-4 text-amber-400" />
            <span>Export Errors (.txt)</span>
          </button>

          <button
            onClick={handleDownloadCleanedJson}
            className="flex items-center space-x-2 bg-slate-800/90 hover:bg-slate-700 text-slate-200 px-4 py-3 rounded-xl text-sm font-semibold transition border border-slate-700 cursor-pointer"
          >
            <FileCode className="w-4 h-4 text-emerald-400" />
            <span>Cleaned JSON</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        
        {/* Quality Score */}
        <div className="col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex items-center justify-between shadow-xl">
          <div>
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">
              Quality Score
            </h3>
            <p className="text-slate-500 text-xs">Based on orphan & error frequency</p>
            <div className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Audit Passed</span>
            </div>
          </div>
          <QualityRing score={qualityScore} />
        </div>

        {/* Processed */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-center shadow-xl">
          <span className="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-2 font-mono">
            Processed
          </span>
          <span className="text-3xl font-black text-slate-100 font-mono">
            {result.summary.total_processed}
          </span>
        </div>

        {/* Exact Dups */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-center shadow-xl">
          <span className="text-rose-400/80 text-[10px] font-bold uppercase tracking-widest mb-2 font-mono">
            Exact Dups
          </span>
          <span className="text-3xl font-black text-rose-400 font-mono">
            {result.summary.exact_duplicates_removed}
          </span>
        </div>

        {/* Semantic Merged */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-center shadow-xl">
          <span className="text-amber-400/80 text-[10px] font-bold uppercase tracking-widest mb-2 font-mono">
            Semantic Merged
          </span>
          <span className="text-3xl font-black text-amber-400 font-mono">
            {result.summary.semantic_duplicates_removed}
          </span>
        </div>

        {/* Final Cleaned */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-center shadow-xl">
          <span className="text-indigo-400/90 text-[10px] font-bold uppercase tracking-widest mb-2 font-mono">
            Final Cleaned
          </span>
          <span className="text-3xl font-black text-indigo-400 font-mono">
            {result.summary.final_count}
          </span>
        </div>
      </div>

      {/* Main Content Grid: All Errors Log + Test Cases */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Activity Log & Errors Terminal (Col 5) */}
        <div className="lg:col-span-5 bg-slate-950/90 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-2xl">
          
          {/* Terminal Window Header */}
          <div className="bg-slate-900 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-rose-500/80" />
              <div className="w-3 h-3 rounded-full bg-amber-500/80" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
              <span className="text-xs font-mono font-bold text-slate-400 ml-2">
                audit_pipeline_errors.log
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">
              {filteredLogs.length} entries
            </span>
          </div>

          {/* Filter Pills */}
          <div className="bg-slate-900/50 p-2.5 border-b border-slate-800/80 flex items-center gap-1.5 text-xs font-medium overflow-x-auto">
            <button
              onClick={() => setLogFilter('all')}
              className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                logFilter === 'all'
                  ? 'bg-indigo-600 text-white font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              All ({result.validation_report.length})
            </button>
            <button
              onClick={() => setLogFilter('duplicates')}
              className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                logFilter === 'duplicates'
                  ? 'bg-amber-600 text-white font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              Duplicates
            </button>
            <button
              onClick={() => setLogFilter('orphans')}
              className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                logFilter === 'orphans'
                  ? 'bg-rose-600 text-white font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              Orphans
            </button>
            <button
              onClick={() => setLogFilter('cleaned')}
              className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                logFilter === 'cleaned'
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              Cleaned
            </button>
          </div>

          {/* Log Stream with full scroll - All Errors Included */}
          <div className="p-4 overflow-y-auto max-h-[600px] space-y-1">
            {filteredLogs.map((log, i) => (
              <TerminalLine key={i} log={log} />
            ))}
            {filteredLogs.length === 0 && (
              <div className="text-slate-500 font-mono text-xs py-8 text-center">
                No logs match the selected filter.
              </div>
            )}
          </div>
        </div>

        {/* Data Matrix of Cleaned Test Cases (Col 7) */}
        <div className="lg:col-span-7 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-2xl">
          <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
            <h3 className="font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Sanitized Test Case Inventory</span>
            </h3>
            <span className="text-xs font-mono font-semibold bg-slate-800 text-slate-300 px-2.5 py-1 rounded-md border border-slate-700">
              {result.cleaned_test_cases.length} Total Cases
            </span>
          </div>

          <div className="flex-1 overflow-y-auto max-h-[640px]">
            <table className="w-full text-left border-collapse">
              <thead className="bg-slate-950/80 sticky top-0 z-10 border-b border-slate-800">
                <tr className="text-[10px] font-black text-slate-400 uppercase tracking-widest font-mono">
                  <th className="py-3 px-4 w-10"></th>
                  <th className="py-3 px-2 w-24">TC ID</th>
                  <th className="py-3 px-4">Title</th>
                  <th className="py-3 px-3 w-28">Priority</th>
                  <th className="py-3 px-4 text-right">SRS Mapping</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {result.cleaned_test_cases.map((tc, index) => (
                  <tr
                    key={tc.id || index}
                    className="hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <ChevronRight className="w-4 h-4 text-slate-600" />
                    </td>
                    <td className="py-3 px-2 font-mono text-xs font-bold text-indigo-300">
                      {tc.id}
                    </td>
                    <td className="py-3 px-4 text-sm font-medium text-slate-200">
                      {tc.title}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getPriorityColor(
                          tc.priority
                        )}`}
                      >
                        {tc.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex flex-wrap justify-end gap-1.5">
                        {tc.requirement_ids?.map((req: string) => (
                          <span
                            key={req}
                            className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono border ${
                              req === 'ORPHAN-UNMAPPED'
                                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                : 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}
                          >
                            {req === 'ORPHAN-UNMAPPED' && (
                              <AlertTriangle className="w-3 h-3 inline mr-1 -mt-0.5" />
                            )}
                            {req}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>

    </div>
  );
};

export default ReportPage;
