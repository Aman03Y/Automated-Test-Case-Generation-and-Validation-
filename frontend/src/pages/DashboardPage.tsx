import React, { useState } from "react";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { FileUploader } from "../components/FileUploader";
import axios from "axios";
import { apiService } from "../services/api";
import type { AutoFixResponse } from "../types";
import { Loader } from "../components/Loader";

export const DashboardPage: React.FC = () => {
  const [result, setResult] = useState<AutoFixResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (file: File) => {
    setLoading(true);
    try {
      const res = await apiService.validateAndFixTestcases(file);
      setResult(res);
    } catch (e) {
      console.error(e);
      if (axios.isAxiosError(e) && !e.response) {
        alert(
          "Backend is not reachable. Run: uv run uvicorn backend.app:app --reload --port 8000 and refresh.",
        );
      } else if (axios.isAxiosError(e) && e.response) {
        const d = (e.response.data as any)?.detail || e.response.data;
        alert(
          `Validation failed: ${typeof d === "string" ? d : JSON.stringify(d)}`,
        );
      } else {
        alert("Error validating file: " + String(e));
      }
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!result) return;
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(result.validation_report, null, 2));
    const dlAnchorElem = document.createElement("a");
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", "validation_report.json");
    dlAnchorElem.click();
  };

  const downloadCleanedJSON = () => {
    if (!result) return;
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(result.cleaned_test_cases, null, 2));
    const dlAnchorElem = document.createElement("a");
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", "cleaned_testcases.json");
    dlAnchorElem.click();
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <Card className="bg-gradient-to-r from-slate-900 to-indigo-900 border-indigo-900 p-8 shadow-xl">
        <h2 className="text-2xl font-black text-white tracking-wide">
          Test Case Validation & Cleaning Engine
        </h2>
        <p className="text-sm text-indigo-200 mt-2 max-w-3xl leading-relaxed">
          Upload JSON test case files to automatically detect duplicates,
          correct malformed structures, and flag unmapped orphans using hybrid
          NLP Semantic Deduplication (SentenceTransformers).
        </p>
      </Card>

      {!result && !loading && (
        <Card className="shadow-lg border-slate-200 p-8">
          <FileUploader
            accept=".json"
            onUpload={handleUpload}
            title="Drop JSON Test Cases Here"
            subtitle="Click to browse your file system (.json)"
            supportedFormatsText="Strictly JSON format containing 'testcases' array."
          />
        </Card>
      )}

      {loading && (
        <Card className="flex flex-col items-center justify-center py-16 shadow-lg border-slate-200">
          <Loader />
          <span className="mt-6 font-bold text-indigo-700 tracking-wide">
            Analyzing, Semantic Deduplicating & Auto-Fixing...
          </span>
        </Card>
      )}

      {!loading && result && (
        <div className="space-y-6">
          <Card className="shadow-lg border-slate-200 p-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 border-b border-slate-100 pb-4">
              <h3 className="font-extrabold text-slate-800 text-xl">
                Processing Summary
              </h3>
              <div className="flex space-x-3">
                <button
                  onClick={downloadReport}
                  className="bg-white text-slate-700 border border-slate-300 px-4 py-2 rounded-md font-semibold text-sm hover:bg-slate-50 transition shadow-sm"
                >
                  Download Validation Report
                </button>
                <button
                  onClick={downloadCleanedJSON}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md font-semibold text-sm hover:bg-indigo-700 transition shadow-sm"
                >
                  Download Cleaned JSON
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-2">
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center">
                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1">
                  Total Processed
                </p>
                <p className="text-3xl font-black text-slate-800">
                  {result.summary.total_processed}
                </p>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 shadow-sm flex flex-col items-center justify-center text-center">
                <p className="text-[10px] text-blue-600 uppercase font-bold tracking-wider mb-1">
                  Exact Dups Removed
                </p>
                <p className="text-3xl font-black text-blue-700">
                  {result.summary.exact_duplicates_removed}
                </p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200 shadow-sm flex flex-col items-center justify-center text-center">
                <p className="text-[10px] text-purple-600 uppercase font-bold tracking-wider mb-1">
                  Semantic Dups Removed
                </p>
                <p className="text-3xl font-black text-purple-700">
                  {result.summary.semantic_duplicates_removed}
                </p>
              </div>
              <div className="bg-amber-50 p-4 rounded-lg border border-amber-200 shadow-sm flex flex-col items-center justify-center text-center">
                <p className="text-[10px] text-amber-600 uppercase font-bold tracking-wider mb-1">
                  Orphans Flagged
                </p>
                <p className="text-3xl font-black text-amber-700">
                  {result.summary.orphans_flagged}
                </p>
              </div>
              <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-200 shadow-sm flex flex-col items-center justify-center text-center">
                <p className="text-[10px] text-emerald-600 uppercase font-bold tracking-wider mb-1">
                  Final Clean Count
                </p>
                <p className="text-3xl font-black text-emerald-700">
                  {result.summary.final_count}
                </p>
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="col-span-1 shadow-lg border-slate-200 p-0 overflow-hidden flex flex-col">
              <div className="bg-slate-900 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
                <h4 className="font-mono text-sm font-bold text-green-400">
                  Activity_Log.sh
                </h4>
                <span className="flex space-x-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                </span>
              </div>
              <div className="bg-slate-950 p-4 text-xs font-mono text-slate-300 overflow-y-auto max-h-[500px] flex-1">
                {result.validation_report.length === 0 ? (
                  <p className="text-slate-500 italic">
                    No automated fixes were required. Dataset is pristine.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {result.validation_report.map((log, idx) => (
                      <li key={idx} className="flex space-x-2">
                        <span className="text-blue-400 select-none">~</span>
                        <span>{log}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </Card>

            <Card className="col-span-2 shadow-lg border-slate-200 p-0 overflow-hidden flex flex-col">
              <div className="px-5 py-4 border-b border-slate-200 bg-white">
                <h4 className="font-bold text-slate-800">
                  Sanitized Test Case Preview
                </h4>
              </div>
              <div className="overflow-x-auto max-h-[500px] flex-1 bg-slate-50">
                <table className="w-full text-left border-collapse bg-white">
                  <thead className="sticky top-0 bg-white shadow-sm z-10">
                    <tr className="border-b border-slate-200 text-xs font-bold text-slate-500 uppercase">
                      <th className="py-3 px-4 w-28 whitespace-nowrap">
                        TC ID
                      </th>
                      <th className="py-3 px-4">Title</th>
                      <th className="py-3 px-4 w-32 whitespace-nowrap">
                        Req ID
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {result.cleaned_test_cases.slice(0, 100).map((tc, i) => (
                      <tr
                        key={i}
                        className="hover:bg-indigo-50/30 transition-colors"
                      >
                        <td className="py-3 px-4 font-mono font-bold text-indigo-600 text-xs">
                          {tc.id}
                        </td>
                        <td className="py-3 px-4 font-medium text-slate-800">
                          {tc.title}
                        </td>
                        <td className="py-3 px-4">
                          {tc.requirement_ids?.map((req: string) => (
                            <Badge
                              key={req}
                              variant={
                                req === "ORPHAN-UNMAPPED" ? "danger" : "neutral"
                              }
                              className="mr-1 mb-1"
                            >
                              {req}
                            </Badge>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {result.cleaned_test_cases.length > 100 && (
                <div className="px-4 py-2 bg-slate-50 text-center text-xs text-slate-500 border-t border-slate-200">
                  Showing first 100 results. Download JSON for full dataset.
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
