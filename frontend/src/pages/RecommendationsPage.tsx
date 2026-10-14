import React, { useEffect, useState } from 'react';
import { Lightbulb, ShieldAlert, Target, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { SearchBox } from '../components/SearchBox';
import { Loader } from '../components/Loader';
import { apiService } from '../services/api';
import type { RecommendationsResponse } from '../types';

export const RecommendationsPage: React.FC = () => {
  const [data, setData] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchRecs();
  }, []);

  const fetchRecs = async () => {
    try {
      setLoading(true);
      const res = await apiService.getRecommendations();
      setData(res);
      setError(null);
    } catch (err: any) {
      setError('No recommendations found. Please run the validation pipeline first.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loader label="Generating AI recommendations..." size="lg" />;

  if (error || !data) {
    return (
      <Card className="bg-amber-50 border-amber-200 text-amber-900 p-8 text-center max-w-xl mx-auto space-y-3">
        <Lightbulb className="w-12 h-12 text-amber-600 mx-auto" />
        <h3 className="text-xl font-bold">No Recommendations Loaded</h3>
        <p className="text-sm text-amber-800">{error}</p>
      </Card>
    );
  }

  const projRecs = data.project_recommendations || [];
  const uncoveredRecs = data.uncovered_requirement_recommendations || [];
  const tcRecs = data.testcase_recommendations || [];

  const filteredTcRecs = tcRecs.filter(
    (item) =>
      item.testcase_id.toLowerCase().includes(search.toLowerCase()) ||
      item.recommendations.some((r) => r.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Banner */}
      <Card className="bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 text-white p-6 md:p-8 rounded-2xl shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-purple-500/20 rounded-xl border border-purple-400/30">
            <Lightbulb className="w-8 h-8 text-purple-300" />
          </div>
          <div>
            <h2 className="text-2xl font-extrabold tracking-tight">
              Actionable AI Recommendations
            </h2>
            <p className="text-purple-200 text-sm mt-0.5">
              Intelligent rule-based guidance to fix compliance defects, cover missing requirements, and eliminate duplicate test cases.
            </p>
          </div>
        </div>
      </Card>

      {/* Project Guidelines & Missing Requirement Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {projRecs.length > 0 && (
          <Card className="border-blue-200 bg-blue-50/40">
            <h3 className="font-bold text-blue-900 text-base mb-3 flex items-center space-x-2">
              <ShieldAlert className="w-5 h-5 text-blue-600" />
              <span>Project-Level Quality Guidelines</span>
            </h3>
            <ul className="space-y-2 text-sm text-blue-800 font-medium">
              {projRecs.map((pr, i) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-blue-500 font-bold">&bull;</span>
                  <span>{pr}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {uncoveredRecs.length > 0 && (
          <Card className="border-rose-200 bg-rose-50/40">
            <h3 className="font-bold text-rose-900 text-base mb-3 flex items-center space-x-2">
              <Target className="w-5 h-5 text-rose-600" />
              <span>Missing Requirement Actions</span>
            </h3>
            <ul className="space-y-2 text-sm text-rose-800 font-medium">
              {uncoveredRecs.map((ur, i) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-rose-500 font-bold">&bull;</span>
                  <span>{ur}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      {/* Specific Test Case Recommendations */}
      <Card>
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <h3 className="font-bold text-slate-800 text-lg">
            Specific Test Case Action Items ({filteredTcRecs.length})
          </h3>
          <SearchBox
            value={search}
            onChange={setSearch}
            placeholder="Filter recommendations..."
          />
        </div>

        {filteredTcRecs.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            No test case recommendations found matching your search.
          </div>
        ) : (
          <div className="space-y-4">
            {filteredTcRecs.map((item) => {
              const isExpanded = expandedId === item.testcase_id;
              const pLower = (item.priority || 'medium').toLowerCase() as
                | 'critical'
                | 'high'
                | 'medium'
                | 'low';

              return (
                <div
                  key={item.testcase_id}
                  className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-xs transition-all"
                >
                  <div
                    onClick={() =>
                      setExpandedId(isExpanded ? null : item.testcase_id)
                    }
                    className="flex justify-between items-center p-4 bg-slate-50/60 hover:bg-slate-100/60 cursor-pointer"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="font-extrabold text-blue-600 text-base">
                        {item.testcase_id}
                      </span>
                      <Badge variant={pLower}>Priority: {item.priority}</Badge>
                      <span className="text-xs text-slate-500">
                        ({item.recommendations.length} action items)
                      </span>
                    </div>

                    <button className="text-slate-400 hover:text-slate-600">
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5" />
                      ) : (
                        <ChevronDown className="w-5 h-5" />
                      )}
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="p-4 border-t border-slate-200 bg-white space-y-2 text-sm text-slate-700">
                      {item.recommendations.map((rec, idx) => (
                        <div
                          key={idx}
                          className="flex items-start space-x-2.5 p-2 bg-slate-50 rounded-lg border border-slate-100"
                        >
                          <span className="text-amber-500 font-bold">💡</span>
                          <span className="font-medium text-slate-800">{rec}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
};
