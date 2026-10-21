import React, { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileUp,
  Download,
  AlertTriangle,
  Code2,
  ChevronRight,
  Activity,
  FileCheck2,
  FileText,
} from "lucide-react";
import axios from "axios";
import { apiService } from "../services/api";
import type { AutoFixResponse } from "../types";
import { generatePdfReport } from "../utils/generatePdfReport";

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
          className="text-slate-800"
        />
        <motion.circle
          cx="40"
          cy="40"
          r={radius}
          stroke="currentColor"
          strokeWidth="6"
          fill="transparent"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          strokeLinecap="round"
          className={
            score >= 80
              ? "text-emerald-500"
              : score >= 50
                ? "text-amber-500"
                : "text-rose-500"
          }
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-lg font-black text-white">{score}</span>
        <span className="text-[9px] font-bold text-slate-500 uppercase tracking-tighter">
          Score
        </span>
      </div>
    </div>
  );
};

// Log Line formatter
const TerminalLine = ({ log }: { log: string }) => {
  let color = "text-slate-400";
  let tagColor = "text-slate-500";

  if (log.includes("[EXACT_DUPLICATE]")) {
    color = "text-rose-300";
    tagColor = "text-rose-500";
  } else if (log.includes("[SEMANTIC_MERGE]")) {
    color = "text-amber-300";
    tagColor = "text-amber-500";
  } else if (log.includes("[ORPHAN_FLAG]")) {
    color = "text-orange-300";
    tagColor = "text-orange-500";
  } else if (log.includes("[CLEANED]")) {
    color = "text-emerald-300";
    tagColor = "text-emerald-500";
  }

  const match = log.match(/^(\[[^\]]+\])(.*)/);
  if (match) {
    return (
      <div className="font-mono text-xs mb-1.5 flex items-start leading-relaxed">
        <span className={`${tagColor} font-bold mr-2 whitespace-nowrap`}>
          {match[1]}
        </span>
        <span className={`${color}`}>{match[2]}</span>
      </div>
    );
  }
  return <div className="font-mono text-xs text-slate-400 mb-1">{log}</div>;
};

export const ValidatePage: React.FC = () => {
  const [result, setResult] = useState<AutoFixResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 100;

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      const res = await apiService.validateAndFixTestcases(file);
      setResult(res);
      setCurrentPage(1);
      localStorage.setItem("latest_validation_report", JSON.stringify(res));
    } catch (error) {
      console.error(error);
      if (axios.isAxiosError(error) && !error.response) {
        alert(
          "Backend is not reachable (ERR_CONNECTION_REFUSED).\n\n" +
            "Fix: start the backend in a separate terminal:\n" +
            "  cd E:\\Abhau && uv run uvicorn backend.app:app --reload --port 8000\n\n" +
            "Then refresh this page and try again.\n" +
            "Check http://localhost:8000/docs opens.",
        );
      } else if (axios.isAxiosError(error) && error.response) {
        const detail =
          (error.response.data as any)?.detail || error.response.data;
        alert(
          `Validation failed: ${typeof detail === "string" ? detail : JSON.stringify(detail)}`,
        );
      } else {
        alert("Error validating file: " + String(error));
      }
    } finally {
      setLoading(false);
      // allow re-uploading same file
      e.target.value = "";
    }
  };

  const toggleRow = (id: string) => {
    const next = new Set(expandedRows);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedRows(next);
  };

  const downloadReport = () => {
    if (!result) return;
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(result.validation_report, null, 2));
    const a = document.createElement("a");
    a.href = dataStr;
    a.download = "validation_report.json";
    a.click();
  };

  const downloadJSON = () => {
    if (!result) return;
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(result.cleaned_test_cases, null, 2));
    const a = document.createElement("a");
    a.href = dataStr;
    a.download = "cleaned_testcases.json";
    a.click();
  };

  const handleDownloadPdf = () => {
    if (!result) return;
    try {
      generatePdfReport(result, "AI_Validation_Full_Report.pdf");
    } catch (e: any) {
      alert("Failed to generate PDF: " + (e.message || String(e)));
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "critical":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      case "high":
        return "bg-orange-500/10 text-orange-400 border-orange-500/20";
      case "medium":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
      case "low":
        return "bg-slate-500/10 text-slate-400 border-slate-500/20";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  const qualityScore = result
    ? Math.max(
        0,
        Math.round(
          100 -
            (result.summary.orphans_flagged /
              Math.max(result.summary.final_count, 1)) *
              100,
        ),
      )
    : 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-indigo-500/30">
      <div className="max-w-[1400px] mx-auto p-6 md:p-8 space-y-8">
        {/* Header & Export Bar */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row justify-between items-start md:items-center bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl"
        >
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
                <Activity className="w-6 h-6" />
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white">
                Validation & Auto-Fix Engine
              </h1>
            </div>
            <p className="text-slate-400 text-sm max-w-xl">
              Semantic deduplication and architectural sanitization pipeline.
              Upload a JSON test suite to begin.
            </p>
          </div>

          <div className="mt-6 md:mt-0 flex flex-wrap gap-3">
            {result && (
              <>
                <button
                  onClick={handleDownloadPdf}
                  className="flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white px-5 py-2.5 rounded-xl text-sm font-bold transition shadow-lg shadow-indigo-600/30 cursor-pointer"
                >
                  <Download className="w-4 h-4" />{" "}
                  <span>Download PDF Report</span>
                </button>

                <Link
                  to="/report"
                  className="flex items-center space-x-2 bg-slate-800/90 hover:bg-slate-700 text-slate-200 px-4 py-2.5 rounded-xl text-sm font-semibold transition border border-slate-700"
                >
                  <FileCheck2 className="w-4 h-4 text-emerald-400" />{" "}
                  <span>View PDF Page</span>
                </Link>

                <button
                  onClick={downloadJSON}
                  className="flex items-center space-x-2 bg-slate-800/90 hover:bg-slate-700 text-slate-200 px-4 py-2.5 rounded-xl text-sm font-semibold transition border border-slate-700 cursor-pointer"
                >
                  <Code2 className="w-4 h-4 text-indigo-400" />{" "}
                  <span>Cleaned JSON</span>
                </button>

                <button
                  onClick={downloadReport}
                  className="flex items-center space-x-2 bg-slate-800/90 hover:bg-slate-700 text-slate-200 px-4 py-2.5 rounded-xl text-sm font-semibold transition border border-slate-700 cursor-pointer"
                >
                  <FileText className="w-4 h-4 text-amber-400" />{" "}
                  <span>Report JSON</span>
                </button>
              </>
            )}
          </div>
        </motion.div>

        {/* Upload State */}
        {!result && !loading && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-12 relative group"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all opacity-50"></div>
            <label className="relative flex flex-col items-center justify-center w-full h-64 bg-slate-900/80 border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-3xl cursor-pointer backdrop-blur-sm transition-colors">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <FileUp className="w-12 h-12 mb-4 text-indigo-400 group-hover:text-indigo-300 group-hover:-translate-y-1 transition-all" />
                <p className="mb-2 text-lg font-bold text-slate-200">
                  Drop your JSON test cases here
                </p>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
                  Or click to browse
                </p>
              </div>
              <input
                type="file"
                className="hidden"
                accept=".json"
                onChange={handleUpload}
              />
            </label>
          </motion.div>
        )}

        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-64 space-y-6"
          >
            <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            <p className="text-indigo-400 font-bold tracking-widest text-sm animate-pulse">
              EXECUTING NEURAL DEDUPLICATION PIPELINE...
            </p>
          </motion.div>
        )}

        {/* Results State */}
        {result && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Metrics Row */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              <div className="col-span-2 md:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex items-center justify-between">
                <div>
                  <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">
                    Quality Score
                  </h3>
                  <p className="text-slate-500 text-xs">
                    Based on unmapped orphans
                  </p>
                </div>
                <QualityRing score={qualityScore} />
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-center">
                <span className="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-2">
                  Processed
                </span>
                <span className="text-3xl font-black text-slate-200">
                  {result.summary.total_processed}
                </span>
              </div>
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-center">
                <span className="text-rose-500/80 text-[10px] font-bold uppercase tracking-widest mb-2">
                  Exact Dups
                </span>
                <span className="text-3xl font-black text-rose-400">
                  {result.summary.exact_duplicates_removed}
                </span>
              </div>
              <div className="bg-amber-500/5 border border-amber-500/10 rounded-2xl p-5 flex flex-col justify-center">
                <span className="text-amber-500/80 text-[10px] font-bold uppercase tracking-widest mb-2">
                  Semantic Merged
                </span>
                <span className="text-3xl font-black text-amber-400">
                  {result.summary.semantic_duplicates_removed}
                </span>
              </div>
              <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-2xl p-5 flex flex-col justify-center">
                <span className="text-indigo-400 text-[10px] font-bold uppercase tracking-widest mb-2">
                  Final Cleaned
                </span>
                <span className="text-3xl font-black text-indigo-400">
                  {result.summary.final_count}
                </span>
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
              {/* Activity Log Terminal */}
              <div className="col-span-1 bg-[#0a0a0c] border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-2xl">
                <div className="bg-slate-900 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
                  <div className="flex space-x-2">
                    <div className="w-3 h-3 rounded-full bg-rose-500/80"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
                    <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
                  </div>
                  <span className="text-xs font-mono font-bold text-slate-500">
                    validation_pipeline.log
                  </span>
                </div>
                <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                  {result.validation_report.map((log, i) => (
                    <TerminalLine key={i} log={log} />
                  ))}
                  {result.validation_report.length === 0 && (
                    <div className="text-slate-600 font-mono text-xs">
                      No fixes applied. Dataset is perfectly formatted.
                    </div>
                  )}
                </div>
              </div>

              {/* Data Matrix */}
              <div className="col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-2xl">
                <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                  <h3 className="font-bold text-slate-200">
                    Sanitized Data Matrix
                  </h3>
                  <span className="text-xs font-semibold bg-slate-800 text-slate-400 px-2 py-1 rounded-md">
                    Showing {(currentPage - 1) * itemsPerPage + 1}-
                    {Math.min(
                      currentPage * itemsPerPage,
                      result.cleaned_test_cases.length,
                    )}{" "}
                    of {result.cleaned_test_cases.length} records
                  </span>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar">
                  <table className="w-full text-left border-collapse">
                    <thead className="sticky top-0 bg-slate-900/95 backdrop-blur z-10 border-b border-slate-800">
                      <tr className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                        <th className="py-4 px-6 w-12"></th>
                        <th className="py-4 px-2 w-24">TC ID</th>
                        <th className="py-4 px-4">Title</th>
                        <th className="py-4 px-4 w-28">Priority</th>
                        <th className="py-4 px-6 w-32 text-right">
                          SRS Mapping
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                      {result.cleaned_test_cases
                        .slice(
                          (currentPage - 1) * itemsPerPage,
                          currentPage * itemsPerPage,
                        )
                        .map((tc) => (
                          <React.Fragment key={tc.id}>
                            <tr
                              onClick={() => toggleRow(tc.id)}
                              className="hover:bg-slate-800/30 transition-colors cursor-pointer group"
                            >
                              <td className="py-4 px-6">
                                <motion.div
                                  animate={{
                                    rotate: expandedRows.has(tc.id) ? 90 : 0,
                                  }}
                                >
                                  <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-indigo-400 transition-colors" />
                                </motion.div>
                              </td>
                              <td className="py-4 px-2 font-mono text-xs font-bold text-slate-300">
                                {tc.id}
                              </td>
                              <td className="py-4 px-4 text-sm font-medium text-slate-200">
                                {tc.title}
                              </td>
                              <td className="py-4 px-4">
                                <span
                                  className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getPriorityColor(tc.priority)}`}
                                >
                                  {tc.priority}
                                </span>
                              </td>
                              <td className="py-4 px-6 text-right">
                                <div className="flex flex-wrap justify-end gap-1.5">
                                  {tc.requirement_ids?.map((req: string) => (
                                    <span
                                      key={req}
                                      className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono border ${
                                        req === "ORPHAN-UNMAPPED"
                                          ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                                          : "bg-slate-800 text-slate-400 border-slate-700"
                                      }`}
                                    >
                                      {req === "ORPHAN-UNMAPPED" && (
                                        <AlertTriangle className="w-3 h-3 inline mr-1 -mt-0.5" />
                                      )}
                                      {req}
                                    </span>
                                  ))}
                                </div>
                              </td>
                            </tr>

                            {/* Expanded Drawer */}
                            <AnimatePresence>
                              {expandedRows.has(tc.id) && (
                                <motion.tr
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: "auto" }}
                                  exit={{ opacity: 0, height: 0 }}
                                  className="bg-slate-950/50 border-b border-slate-800/50"
                                >
                                  <td colSpan={5} className="py-6 px-12">
                                    <div className="grid grid-cols-2 gap-8">
                                      <div>
                                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
                                          Execution Steps
                                        </h4>
                                        <ol className="list-decimal list-inside space-y-2 text-sm text-slate-300 font-medium">
                                          {tc.steps?.map(
                                            (step: string, i: number) => (
                                              <li key={i} className="pl-2">
                                                {step}
                                              </li>
                                            ),
                                          )}
                                        </ol>
                                      </div>
                                      <div>
                                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
                                          Expected Result
                                        </h4>
                                        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-sm text-emerald-400 font-medium">
                                          {tc.expected_result}
                                        </div>
                                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-6 mb-3">
                                          Description
                                        </h4>
                                        <p className="text-sm text-slate-400 leading-relaxed">
                                          {tc.description}
                                        </p>
                                      </div>
                                    </div>
                                  </td>
                                </motion.tr>
                              )}
                            </AnimatePresence>
                          </React.Fragment>
                        ))}
                    </tbody>
                  </table>
                </div>
                {result.cleaned_test_cases.length > itemsPerPage && (
                  <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/50 flex justify-between items-center">
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 text-xs font-bold rounded"
                    >
                      Previous
                    </button>
                    <span className="text-xs font-semibold text-slate-500">
                      Page {currentPage} of{" "}
                      {Math.ceil(
                        result.cleaned_test_cases.length / itemsPerPage,
                      )}
                    </span>
                    <button
                      onClick={() =>
                        setCurrentPage((p) =>
                          Math.min(
                            Math.ceil(
                              result.cleaned_test_cases.length / itemsPerPage,
                            ),
                            p + 1,
                          ),
                        )
                      }
                      disabled={
                        currentPage ===
                        Math.ceil(
                          result.cleaned_test_cases.length / itemsPerPage,
                        )
                      }
                      className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 text-xs font-bold rounded"
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};
