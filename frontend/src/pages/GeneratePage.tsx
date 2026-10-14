import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  UploadCloud,
  Settings2,
  Download,
  Brain,
  ChevronDown,
  ChevronUp,
  FileText,
  Copy,
  Check,
} from "lucide-react";
import { apiService } from "../services/api";
import type { GeneratorResponse } from "../types";

type Strategy = "comprehensive" | "minimal";

export const GeneratePage: React.FC = () => {
  const [result, setResult] = useState<GeneratorResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generation options
  const [casesPerReq, setCasesPerReq] = useState<number>(3);
  const [strategy, setStrategy] = useState<Strategy>("comprehensive");
  const [includeNegative, setIncludeNegative] = useState(true);
  const [includeBoundary, setIncludeBoundary] = useState(true);
  const [includeEdge, setIncludeEdge] = useState(true);
  const [includeSecurity, setIncludeSecurity] = useState(false);
  const [showOptions, setShowOptions] = useState(true);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [copied, setCopied] = useState(false);

  // Upload branch: file -> upload-and-generate in one shot
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.generatorUploadAndGenerate(file, {
        cases_per_requirement: casesPerReq,
        include_negative: includeNegative,
        include_boundary: includeBoundary,
        include_edge: includeEdge,
        include_security: includeSecurity,
        strategy,
      });
      setResult(res);
      // If upload-and-generate also returns requirements dict, try to capture
      // (fallback: we have requirements via separate fetch if needed)
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || err?.message || "Generation failed";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
      // reset file input
      e.target.value = "";
    }
  };

  // Requirements already in session: generate from them
  const handleGenerateFromSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.generatorGenerate({
        cases_per_requirement: casesPerReq,
        include_negative: includeNegative,
        include_boundary: includeBoundary,
        include_edge: includeEdge,
        include_security: includeSecurity,
        strategy,
        save_to_session: true,
      });
      setResult(res);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || err?.message || "Generation failed";
      const detail = typeof msg === "string" ? msg : JSON.stringify(msg);
      setError(detail);
      // Hint if no requirements have been uploaded
      if (detail.toLowerCase().includes("no requirements")) {
        setError(
          detail +
            " — please upload a requirement document first using the file picker above.",
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleRow = (id: string) => {
    const next = new Set(expandedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedIds(next);
  };

  const downloadJson = () => {
    if (!result) return;
    const payload = result.testcases_dict || result.testcases;
    const url =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(payload, null, 2));
    const a = document.createElement("a");
    a.href = url;
    a.download = "generated_testcases.json";
    a.click();
  };

  const copyJson = async () => {
    if (!result) return;
    const payload = result.testcases_dict || result.testcases;
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const getPriorityChip = (p: string) => {
    const key = p.toLowerCase();
    if (key === "critical")
      return "bg-rose-500/15 text-rose-300 border-rose-500/30";
    if (key === "high")
      return "bg-orange-500/15 text-orange-300 border-orange-500/30";
    if (key === "medium")
      return "bg-indigo-500/15 text-indigo-300 border-indigo-500/30";
    return "bg-slate-500/15 text-slate-300 border-slate-500/30";
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-indigo-500/30">
      <div className="max-w-[1400px] mx-auto p-6 md:p-8 space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl"
        >
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-violet-500/15 text-violet-300 rounded-xl border border-violet-500/20">
                <Sparkles className="w-6 h-6" />
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white">
                AI Test Case Generator
              </h1>
              <span className="ml-2 px-2.5 py-1 rounded-full text-[10px] font-mono uppercase tracking-widest bg-emerald-500/15 text-emerald-300 border border-emerald-500/20">
                New
              </span>
            </div>
            <p className="text-slate-400 text-sm max-w-2xl">
              Turn requirement specifications into comprehensive,
              well-structured test suites. Generates{" "}
              <span className="text-slate-200 font-semibold">
                Positive, Negative, Boundary, Edge &amp; Security
              </span>{" "}
              variants per requirement — ready to validate in one click.
            </p>
          </div>
          {result && (
            <div className="flex items-center gap-2">
              <button
                onClick={copyJson}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-semibold hover:bg-slate-700 transition"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
                {copied ? "Copied" : "Copy JSON"}
              </button>
              <button
                onClick={downloadJson}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-500 transition shadow-lg shadow-indigo-600/20"
              >
                <Download className="w-4 h-4" /> Download JSON
              </button>
            </div>
          )}
        </motion.div>

        {/* Stats row when result exists */}
        {result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-3"
          >
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
              <div className="text-[11px] font-mono uppercase tracking-widest text-slate-500">
                Requirements Covered
              </div>
              <div className="text-2xl font-black text-white mt-1">
                {result.requirements_covered}
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
              <div className="text-[11px] font-mono uppercase tracking-widest text-slate-500">
                Test Cases Generated
              </div>
              <div className="text-2xl font-black text-violet-400 mt-1">
                {result.count}
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
              <div className="text-[11px] font-mono uppercase tracking-widest text-slate-500">
                Per Requirement
              </div>
              <div className="text-2xl font-black text-white mt-1">
                {result.cases_per_requirement}×
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
              <div className="text-[11px] font-mono uppercase tracking-widest text-slate-500">
                Strategy
              </div>
              <div className="text-sm font-bold text-emerald-300 mt-1 capitalize">
                {result.strategy}
              </div>
              <div className="text-xs text-slate-500">{result.message}</div>
            </div>
          </motion.div>
        )}

        {/* Generation Options */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <button
            onClick={() => setShowOptions(!showOptions)}
            className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-slate-800/50 transition"
          >
            <div className="flex items-center gap-3">
              <div className="p-1.5 bg-slate-800 border border-slate-700 rounded-lg">
                <Settings2 className="w-4 h-4 text-slate-300" />
              </div>
              <div>
                <div className="text-sm font-bold text-white">
                  Generation Options
                </div>
                <div className="text-xs text-slate-500">
                  {casesPerReq} per requirement · {strategy} ·{" "}
                  {[
                    includeNegative && "Negative",
                    includeBoundary && "Boundary",
                    includeEdge && "Edge",
                    includeSecurity && "Security",
                  ]
                    .filter(Boolean)
                    .join(", ") || "Positive only"}
                </div>
              </div>
            </div>
            {showOptions ? (
              <ChevronUp className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            )}
          </button>
          <AnimatePresence>
            {showOptions && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="border-t border-slate-800 px-6 py-5 grid grid-cols-1 md:grid-cols-2 gap-6"
              >
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-mono uppercase tracking-widest text-slate-500">
                      Cases per Requirement
                    </label>
                    <div className="flex items-center gap-2 mt-2">
                      {[1, 2, 3, 4, 5].map((n) => (
                        <button
                          key={n}
                          onClick={() => setCasesPerReq(n)}
                          className={`w-10 h-10 rounded-xl font-black text-sm border transition ${casesPerReq === n ? "bg-violet-600 border-violet-500 text-white shadow-lg shadow-violet-600/20" : "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"}`}
                        >
                          {n}
                        </button>
                      ))}
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1.5">
                      How many variants (Positive → Negative → Boundary →
                      Security → Edge) per requirement.
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-mono uppercase tracking-widest text-slate-500">
                      Strategy
                    </label>
                    <div className="flex gap-2 mt-2">
                      {(["comprehensive", "minimal"] as Strategy[]).map((s) => (
                        <button
                          key={s}
                          onClick={() => setStrategy(s)}
                          className={`flex-1 py-2.5 rounded-xl text-sm font-semibold border capitalize transition ${strategy === s ? "bg-slate-800 border-violet-500/50 text-white" : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"}`}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1.5">
                      <span className="text-slate-300 font-semibold">
                        Comprehensive:
                      </span>{" "}
                      Negative + Boundary + Edge coverage. &nbsp;
                      <span className="text-slate-300 font-semibold">
                        Minimal:
                      </span>{" "}
                      Happy-path only.
                    </p>
                  </div>
                </div>
                <div className="space-y-3">
                  <label className="text-xs font-mono uppercase tracking-widest text-slate-500">
                    Include Variants
                  </label>
                  {[
                    {
                      key: "negative",
                      label: "Negative / Invalid Input",
                      desc: "Bad formats, wrong values, error paths",
                      value: includeNegative,
                      setter: setIncludeNegative,
                    },
                    {
                      key: "boundary",
                      label: "Boundary & Limits",
                      desc: "Min / max / out-of-range checks",
                      value: includeBoundary,
                      setter: setIncludeBoundary,
                    },
                    {
                      key: "edge",
                      label: "Edge Cases & Empty States",
                      desc: "No data, first-time, concurrent",
                      value: includeEdge,
                      setter: setIncludeEdge,
                    },
                    {
                      key: "security",
                      label: "Security / Authorization",
                      desc: "Unauth, tampering, access control",
                      value: includeSecurity,
                      setter: setIncludeSecurity,
                    },
                  ].map((item) => (
                    <label
                      key={item.key}
                      className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition ${item.value ? "bg-violet-500/10 border-violet-500/30" : "bg-slate-950 border-slate-800 hover:border-slate-700"}`}
                    >
                      <input
                        type="checkbox"
                        checked={item.value}
                        onChange={(e) => item.setter(e.target.checked)}
                        className="mt-0.5 accent-violet-600 w-4 h-4"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-semibold text-white">
                          {item.label}
                        </div>
                        <div className="text-xs text-slate-500">
                          {item.desc}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Upload / Generate controls */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* One-shot file upload */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-3">
              <UploadCloud className="w-5 h-5 text-violet-400" />
              <h3 className="font-bold text-white text-sm">
                Upload &amp; Generate (One-Shot)
              </h3>
              <span className="ml-auto text-[11px] font-mono px-2 py-1 rounded-full bg-violet-500/15 text-violet-300 border border-violet-500/20">
                Recommended
              </span>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Drop a requirement file (.pdf, .docx, .txt, .json) — it will be
              parsed and test cases generated in one request.
            </p>
            <label className="flex flex-col items-center justify-center gap-2 p-6 rounded-xl border-2 border-dashed border-slate-700 bg-slate-950 hover:border-violet-500/40 hover:bg-slate-900 cursor-pointer transition">
              <FileText className="w-7 h-7 text-slate-500" />
              <span className="text-sm font-semibold text-slate-200">
                Choose or drop requirement file
              </span>
              <span className="text-xs text-slate-500">
                PDF, DOCX, TXT, JSON
              </span>
              <input
                type="file"
                accept=".pdf,.docx,.txt,.json"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>

          {/* Generate from session (requirements already uploaded via /api/requirements/upload or Landing) */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-emerald-400" />
              <h3 className="font-bold text-white text-sm">
                Generate from Uploaded Requirements
              </h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Use requirements already uploaded in this session (via Landing /
              Generate / Upload). Adjust options on the left, then generate.
            </p>
            <div className="mt-auto flex gap-2">
              <button
                onClick={handleGenerateFromSession}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-sm transition shadow-lg shadow-emerald-600/20"
              >
                <Sparkles className="w-4 h-4" />{" "}
                {loading ? "Generating…" : "Generate Test Cases"}
              </button>
              {result && (
                <button
                  onClick={handleGenerateFromSession}
                  className="px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-semibold hover:bg-slate-700 transition"
                >
                  Regenerate
                </button>
              )}
            </div>
            <p className="text-[11px] text-slate-500 mt-2 text-center">
              After generation, go to{" "}
              <span className="text-violet-300 font-semibold">
                Validation Engine
              </span>{" "}
              to validate instantly — generated cases are auto-saved to your
              session.
            </p>
          </div>
        </div>

        {loading && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
            <div className="text-sm font-bold text-violet-300">
              Generating test cases…
            </div>
            <div className="text-xs text-slate-500">
              Parsing requirements, synthesizing variants, inferring priorities
              &amp; modules.
            </div>
          </div>
        )}

        {error && (
          <div className="bg-rose-950/50 border border-rose-500/30 rounded-2xl p-4">
            <div className="text-sm font-bold text-rose-300">
              Generation failed
            </div>
            <div className="text-xs text-rose-200/80 mt-1 whitespace-pre-wrap break-words">
              {error}
            </div>
          </div>
        )}

        {/* Results table */}
        {result && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 px-6 py-4 border-b border-slate-800 bg-slate-900/50">
              <div>
                <h3 className="font-black text-white">
                  Generated Test Cases — {result.count}
                </h3>
                <p className="text-xs text-slate-500">
                  Each row maps to one requirement variant. Click to expand
                  steps &amp; expected results.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-500">
                  Showing {result.testcases.length} cases
                </span>
                <button
                  onClick={downloadJson}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold hover:bg-slate-700 transition flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" /> JSON
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-[11px] font-mono uppercase tracking-widest text-slate-500 bg-slate-950/50">
                    <th className="py-3 px-4 w-28">ID</th>
                    <th className="py-3 px-4">Title</th>
                    <th className="py-3 px-4 w-28">Priority</th>
                    <th className="py-3 px-4 w-32">Requirement</th>
                    <th className="py-3 px-4 w-28">Module</th>
                    <th className="py-3 px-4 w-16"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-sm">
                  {result.testcases.map((tc: any) => {
                    const expanded = expandedIds.has(tc.id);
                    const reqId =
                      (tc.requirement_ids && tc.requirement_ids[0]) ||
                      tc.requirement_id ||
                      "—";
                    const moduleName = tc.module || "—";
                    return (
                      <React.Fragment key={tc.id}>
                        <tr className="hover:bg-slate-800/40 transition">
                          <td className="py-3 px-4 font-mono font-bold text-violet-300">
                            {tc.id}
                          </td>
                          <td className="py-3 px-4 font-medium text-slate-100 max-w-md">
                            <div className="line-clamp-2">{tc.title}</div>
                            <div className="text-xs text-slate-500 line-clamp-1 mt-0.5">
                              {tc.description}
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`inline-flex px-2.5 py-1 rounded-full text-xs font-bold border ${getPriorityChip(tc.priority)}`}
                            >
                              {tc.priority}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-mono text-xs text-emerald-300">
                            {reqId}
                          </td>
                          <td className="py-3 px-4 text-xs text-slate-400">
                            {moduleName}
                          </td>
                          <td className="py-3 px-4">
                            <button
                              onClick={() => toggleRow(tc.id)}
                              className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 transition"
                            >
                              {expanded ? (
                                <ChevronUp className="w-4 h-4 text-slate-300" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-slate-300" />
                              )}
                            </button>
                          </td>
                        </tr>
                        {expanded && (
                          <tr className="bg-slate-950/60">
                            <td colSpan={6} className="px-6 py-4">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                  <div className="text-[11px] font-mono uppercase tracking-widest text-slate-500 mb-1">
                                    Description
                                  </div>
                                  <p className="text-sm text-slate-200 leading-relaxed">
                                    {tc.description}
                                  </p>
                                  <div className="text-[11px] font-mono uppercase tracking-widest text-slate-500 mt-3 mb-1">
                                    Expected Result
                                  </div>
                                  <p className="text-sm text-emerald-200/90 leading-relaxed bg-emerald-500/5 border border-emerald-500/10 rounded-xl p-3">
                                    {tc.expected_result}
                                  </p>
                                </div>
                                <div>
                                  <div className="text-[11px] font-mono uppercase tracking-widest text-slate-500 mb-1">
                                    Steps ({(tc.steps || []).length})
                                  </div>
                                  <ol className="space-y-1.5">
                                    {(tc.steps || []).map(
                                      (s: string, idx: number) => (
                                        <li
                                          key={idx}
                                          className="flex gap-2 text-sm text-slate-300"
                                        >
                                          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-mono text-slate-400">
                                            {idx + 1}
                                          </span>
                                          <span className="leading-relaxed">
                                            {s}
                                          </span>
                                        </li>
                                      ),
                                    )}
                                  </ol>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}

        {!result && !loading && !error && (
          <div className="bg-slate-900/50 border border-dashed border-slate-800 rounded-2xl p-8 text-center">
            <div className="inline-flex p-3 rounded-2xl bg-slate-800 border border-slate-700 mb-3">
              <Sparkles className="w-6 h-6 text-slate-500" />
            </div>
            <div className="text-sm font-bold text-white">
              No test cases generated yet
            </div>
            <div className="text-xs text-slate-500 mt-1 max-w-lg mx-auto">
              Upload a requirement file above or use the session generator. Tip:
              try{" "}
              <span className="text-slate-300 font-mono">
                3 per requirement
              </span>{" "}
              with <span className="text-slate-300">Comprehensive</span> for
              best coverage.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
