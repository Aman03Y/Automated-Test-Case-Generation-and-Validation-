import React, { useState } from "react";
import { Card } from "../components/Card";
import { FileUploader } from "../components/FileUploader";
import axios from "axios";
import { apiService } from "../services/api";
import type { AutoFixResponse } from "../types";
import { Loader } from "../components/Loader";

export const Page2Validation: React.FC = () => {
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
      encodeURIComponent(JSON.stringify(result.summary, null, 2));
    const dlAnchorElem = document.createElement("a");
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", "validation_report.json");
    dlAnchorElem.click();
  };

  const downloadCleanedJSON = () => {
    if (!result) return;
    const testCasesToSave =
      result.cleaned_test_cases || result.cleaned_testcases || [];
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(testCasesToSave, null, 2));
    const dlAnchorElem = document.createElement("a");
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", "cleaned_testcases.json");
    dlAnchorElem.click();
  };

  const duplicatesCount =
    result?.summary.duplicates_removed ??
    (result?.summary.exact_duplicates_removed || 0) +
      (result?.summary.semantic_duplicates_removed || 0);
  const formattingCount = result?.summary.formatting_issues_fixed ?? 0;

  return (
    <div className="space-y-8 animate-fade-in">
      <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-100 p-6">
        <h2 className="text-xl font-bold text-slate-800">
          Page 2: Test Case Validation & Auto-Fixing
        </h2>
        <p className="text-sm text-slate-600 mt-1 max-w-2xl">
          Upload existing Test Case JSON files. The system will analyze,
          validate, and perform auto-cleaning (removing duplicates and
          standardizing formatting).
        </p>
      </Card>

      <Card>
        <FileUploader
          accept=".json,.csv,.txt,.xlsx,.docx,.pdf"
          onUpload={handleUpload}
          title="Drag and Drop Any Test Case File Here"
          subtitle="Click to browse or drop document (.json, .csv, .txt, .pdf, .xlsx)"
          supportedFormatsText="All standard test case formats supported"
        />
      </Card>

      {loading && (
        <Card className="flex justify-center py-10 items-center">
          <Loader />{" "}
          <span className="ml-4 font-bold text-purple-600">
            Analyzing, Validating & Auto-Fixing...
          </span>
        </Card>
      )}

      {!loading && result && (
        <Card>
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
            <h3 className="font-bold text-slate-800 text-lg">
              Validation Summary & Report
            </h3>
            <div className="flex space-x-4">
              <button
                onClick={downloadReport}
                className="bg-white text-slate-700 border border-slate-300 px-4 py-2 rounded font-semibold text-sm hover:bg-slate-50 transition"
              >
                Download Validation Report
              </button>
              <button
                onClick={downloadCleanedJSON}
                className="bg-purple-600 text-white px-4 py-2 rounded font-semibold text-sm hover:bg-purple-700 transition"
              >
                Download Cleaned JSON
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-slate-50 p-4 rounded border border-slate-200">
              <p className="text-xs text-slate-500 uppercase font-bold">
                Total Processed
              </p>
              <p className="text-2xl font-black text-slate-800">
                {result.summary.total_processed}
              </p>
            </div>
            <div className="bg-red-50 p-4 rounded border border-red-200">
              <p className="text-xs text-red-500 uppercase font-bold">
                Duplicates Removed
              </p>
              <p className="text-2xl font-black text-red-700">
                {duplicatesCount}
              </p>
            </div>
            <div className="bg-amber-50 p-4 rounded border border-amber-200">
              <p className="text-xs text-amber-600 uppercase font-bold">
                Formatting Fixed
              </p>
              <p className="text-2xl font-black text-amber-700">
                {formattingCount}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded border border-green-200">
              <p className="text-xs text-green-600 uppercase font-bold">
                Final Clean Count
              </p>
              <p className="text-2xl font-black text-green-700">
                {result.summary.final_count}
              </p>
            </div>
          </div>

          <div className="bg-slate-800 rounded p-4 text-xs text-green-400 overflow-x-auto">
            <pre>
              {`{
  "status": "Success",
  "message": "${result.message || "The test cases have been validated and normalized."}",
  "details": "The uploaded JSON has been fully normalized to strictly follow the required schema."
}`}
            </pre>
          </div>
        </Card>
      )}
    </div>
  );
};
