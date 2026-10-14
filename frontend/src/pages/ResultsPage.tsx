import React, { useEffect, useState } from 'react';
import { Award, AlertTriangle } from 'lucide-react';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { ProgressBar } from '../components/ProgressBar';
import { Loader } from '../components/Loader';
import { apiService } from '../services/api';
import type { ValidationReport } from '../types';

export const ResultsPage: React.FC = () => {
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const data = await apiService.getJsonReport();
      setReport(data);
      setError(null);
    } catch (err: any) {
      setError('No validation results found. Please run the validation pipeline first.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loader label="Loading validation results..." size="lg" />;

  if (error || !report) {
    return (
      <Card className="bg-amber-50 border-amber-200 text-amber-900 p-8 text-center max-w-xl mx-auto space-y-4">
        <AlertTriangle className="w-12 h-12 text-amber-600 mx-auto" />
        <h3 className="text-xl font-bold">No Results Found</h3>
        <p className="text-sm text-amber-800">{error || 'Please run validation first.'}</p>
      </Card>
    );
  }

  const summary = report.summary;
  const sb = report.score_breakdown?.score_breakdown || {};

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Overview Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <Card className="bg-gradient-to-br from-blue-600 to-blue-800 text-white p-6 shadow-md">
          <p className="text-xs uppercase text-blue-200 font-semibold tracking-wider">
            Overall Quality Score
          </p>
          <div className="flex items-baseline space-x-2 mt-2">
            <h2 className="text-4xl font-black">{report.quality_score.toFixed(1)}</h2>
            <span className="text-sm text-blue-200 font-medium">/ 100</span>
          </div>
          <p className="text-xs text-blue-200 mt-2">
            Weighted Enterprise Scoring System
          </p>
        </Card>

        <Card className="bg-white p-6">
          <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">
            Letter Grade & Rating
          </p>
          <div className="flex items-center space-x-3 mt-2">
            <Badge variant="pass" className="text-xl px-4 py-1 font-bold">
              {summary.grade}
            </Badge>
            <span className="text-lg font-bold text-slate-800">
              {summary.visual_summary}
            </span>
          </div>
        </Card>

        <Card className="bg-white p-6">
          <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">
            Requirement Coverage
          </p>
          <div className="flex items-baseline space-x-2 mt-2">
            <h2 className="text-3xl font-bold text-emerald-600">
              {report.coverage.toFixed(1)}%
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {summary.covered_requirements} of {summary.total_requirements} requirements covered
          </p>
        </Card>

        <Card className="bg-white p-6">
          <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">
            Duplicate Pair Matches
          </p>
          <div className="flex items-baseline space-x-2 mt-2">
            <h2 className="text-3xl font-bold text-slate-800">{report.duplicates}</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Cosine Similarity Threshold: 85%
          </p>
        </Card>
      </div>

      {/* Weighted Score Components Breakdown */}
      <Card>
        <h3 className="font-bold text-slate-800 text-lg mb-6 flex items-center space-x-2">
          <Award className="w-5 h-5 text-blue-600" />
          <span>Weighted Quality Score Component Breakdown</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <ProgressBar
              value={((sb.coverage || 0) / 35.0) * 100}
              label={`Requirement Coverage Component (${(sb.coverage || 0).toFixed(1)} / 35.0)`}
              color="emerald"
            />
            <p className="text-xs text-slate-500 mt-1">Weight: 35% of total score</p>
          </div>

          <div>
            <ProgressBar
              value={((sb.average_quality || 0) / 35.0) * 100}
              label={`Average Test Case Quality (${(sb.average_quality || 0).toFixed(1)} / 35.0)`}
              color="blue"
            />
            <p className="text-xs text-slate-500 mt-1">Weight: 35% of total score</p>
          </div>

          <div>
            <ProgressBar
              value={((sb.duplicate_penalty || 0) / 20.0) * 100}
              label={`Duplicate Penalty Component (${(sb.duplicate_penalty || 0).toFixed(1)} / 20.0)`}
              color="purple"
            />
            <p className="text-xs text-slate-500 mt-1">Weight: 20% of total score</p>
          </div>

          <div>
            <ProgressBar
              value={((sb.formatting || 0) / 10.0) * 100}
              label={`Formatting & Completeness (${(sb.formatting || 0).toFixed(1)} / 10.0)`}
              color="amber"
            />
            <p className="text-xs text-slate-500 mt-1">Weight: 10% of total score</p>
          </div>
        </div>
      </Card>

      {/* Rule Violations & Defective Test Cases */}
      {report.failed_testcases.length > 0 && (
        <Card>
          <h3 className="font-bold text-slate-800 text-lg mb-4 text-rose-600">
            Defective Test Cases & Compliance Rule Failures ({report.failed_testcases.length})
          </h3>

          <div className="space-y-4">
            {report.failed_testcases.map((ftc) => (
              <div
                key={ftc.id}
                className="p-4 bg-rose-50/50 border border-rose-200 rounded-xl space-y-2"
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center space-x-3">
                    <span className="font-bold text-rose-700">{ftc.id}</span>
                    <span className="font-semibold text-slate-800">{ftc.title}</span>
                  </div>
                  <Badge variant="fail">Score: {ftc.score} / 100</Badge>
                </div>

                <div className="space-y-1 pl-2 border-l-2 border-rose-300 text-xs text-rose-700">
                  {ftc.errors.map((err, i) => (
                    <p key={i}>❌ {err}</p>
                  ))}
                  {ftc.warnings.map((warn, i) => (
                    <p key={i} className="text-amber-700">
                      ⚠️ {warn}
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
