import React, { useEffect, useState } from 'react';
import { Download, FileJson, FileText, FileCheck2 } from 'lucide-react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Loader } from '../components/Loader';
import { apiService } from '../services/api';
import type { ValidationReport } from '../types';

export const ReportsPage: React.FC = () => {
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [markdown, setMarkdown] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReportData();
  }, []);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      const jsonRes = await apiService.getJsonReport();
      const mdRes = await apiService.getMarkdownReport();
      setReport(jsonRes);
      setMarkdown(mdRes);
      setError(null);
    } catch (err: any) {
      setError('No generated reports found. Please run validation pipeline first.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadJson = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'validation_report.json';
    a.click();
  };

  const handleDownloadMarkdown = () => {
    if (!markdown) return;
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'validation_report.md';
    a.click();
  };

  const handleDownloadPdf = () => {
    const pdfUrl = apiService.getPdfReportUrl();
    window.open(pdfUrl, '_blank');
  };

  if (loading) return <Loader label="Compiling report preview..." size="lg" />;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header & Download Action Buttons */}
      <Card className="bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 text-white p-6 md:p-8 rounded-2xl shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            Enterprise Export Reports
          </h2>
          <p className="text-slate-300 text-sm mt-1 max-w-xl">
            Export automated test case validation findings in PDF, JSON, and Markdown formats.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button
            onClick={handleDownloadPdf}
            variant="danger"
            size="md"
            icon={<Download className="w-4 h-4" />}
          >
            Download PDF Report
          </Button>

          <Button
            onClick={handleDownloadJson}
            variant="primary"
            size="md"
            icon={<FileJson className="w-4 h-4" />}
          >
            Download JSON
          </Button>

          <Button
            onClick={handleDownloadMarkdown}
            variant="outline"
            size="md"
            className="bg-white/10 text-white border-white/20 hover:bg-white/20"
            icon={<FileText className="w-4 h-4" />}
          >
            Download Markdown
          </Button>
        </div>
      </Card>

      {error && (
        <Card className="bg-amber-50 border-amber-200 text-amber-900 p-6 text-center">
          <p className="text-sm font-medium">{error}</p>
        </Card>
      )}

      {/* Markdown Preview Section */}
      {markdown && (
        <Card>
          <div className="flex justify-between items-center mb-4 pb-3 border-b border-slate-200">
            <h3 className="font-bold text-slate-800 text-lg flex items-center space-x-2">
              <FileCheck2 className="w-5 h-5 text-blue-600" />
              <span>Report Preview (validation_report.md)</span>
            </h3>
            <span className="text-xs font-semibold text-slate-400">
              Live Preview
            </span>
          </div>

          <div className="bg-slate-900 text-slate-100 p-6 rounded-xl font-mono text-xs overflow-x-auto leading-relaxed max-h-[600px]">
            <pre className="whitespace-pre-wrap">{markdown}</pre>
          </div>
        </Card>
      )}
    </div>
  );
};
