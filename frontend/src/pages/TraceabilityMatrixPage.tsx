import React, { useEffect, useState } from 'react';
import { TableProperties, Download } from 'lucide-react';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { Button } from '../components/Button';
import { SearchBox } from '../components/SearchBox';
import { Loader } from '../components/Loader';
import { apiService } from '../services/api';
import type { TraceabilityMatrixResponse } from '../types';

export const TraceabilityMatrixPage: React.FC = () => {
  const [data, setData] = useState<TraceabilityMatrixResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState<'id' | 'count'>('id');
  const [sortAsc, setSortAsc] = useState(true);

  const pageSize = 8;

  useEffect(() => {
    fetchRtm();
  }, []);

  const fetchRtm = async () => {
    try {
      setLoading(true);
      const res = await apiService.getTraceabilityMatrix();
      setData(res);
      setError(null);
    } catch (err: any) {
      setError('Traceability Matrix not loaded yet. Please run validation pipeline.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCsv = () => {
    if (!data || !data.matrix) return;
    const headers = ['Requirement ID', 'Requirement Description', 'Mapped Test Cases', 'Count', 'Status'];
    const rows = data.matrix.map((row) => [
      row.requirement_id,
      `"${row.requirement_description.replace(/"/g, '""')}"`,
      `"${row.mapped_testcases.join(', ')}"`,
      row.testcase_count,
      row.status,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'traceability_matrix.csv';
    link.click();
  };

  if (loading) return <Loader label="Loading Requirement Traceability Matrix..." size="lg" />;

  if (error || !data) {
    return (
      <Card className="bg-amber-50 border-amber-200 text-amber-900 p-8 text-center max-w-xl mx-auto space-y-3">
        <TableProperties className="w-12 h-12 text-amber-600 mx-auto" />
        <h3 className="text-xl font-bold">No RTM Data Available</h3>
        <p className="text-sm text-amber-800">{error}</p>
      </Card>
    );
  }

  const matrix = data.matrix || [];

  const filteredMatrix = matrix.filter(
    (row) =>
      row.requirement_id.toLowerCase().includes(search.toLowerCase()) ||
      row.requirement_description.toLowerCase().includes(search.toLowerCase()) ||
      row.mapped_testcases.some((tc) => tc.toLowerCase().includes(search.toLowerCase()))
  );

  const sortedMatrix = [...filteredMatrix].sort((a, b) => {
    if (sortField === 'id') {
      return sortAsc
        ? a.requirement_id.localeCompare(b.requirement_id)
        : b.requirement_id.localeCompare(a.requirement_id);
    } else {
      return sortAsc ? a.testcase_count - b.testcase_count : b.testcase_count - a.testcase_count;
    }
  });

  const totalPages = Math.ceil(sortedMatrix.length / pageSize) || 1;
  const paginatedRows = sortedMatrix.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Banner Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card className="bg-white p-5 border-l-4 border-l-blue-600">
          <p className="text-xs uppercase text-slate-400 font-semibold">Total Requirements</p>
          <h3 className="text-2xl font-black text-slate-800 mt-1">{data.total_requirements}</h3>
        </Card>

        <Card className="bg-white p-5 border-l-4 border-l-emerald-500">
          <p className="text-xs uppercase text-slate-400 font-semibold">Covered (2+ TCs)</p>
          <h3 className="text-2xl font-black text-emerald-600 mt-1">{data.covered_count}</h3>
        </Card>

        <Card className="bg-white p-5 border-l-4 border-l-amber-500">
          <p className="text-xs uppercase text-slate-400 font-semibold">Partially Covered (1 TC)</p>
          <h3 className="text-2xl font-black text-amber-600 mt-1">{data.partially_covered_count}</h3>
        </Card>

        <Card className="bg-white p-5 border-l-4 border-l-rose-500">
          <p className="text-xs uppercase text-slate-400 font-semibold">Missing (0 TCs)</p>
          <h3 className="text-2xl font-black text-rose-600 mt-1">{data.missing_count}</h3>
        </Card>
      </div>

      {/* RTM Data Table Card */}
      <Card>
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div>
            <h3 className="font-bold text-slate-800 text-lg flex items-center space-x-2">
              <TableProperties className="w-5 h-5 text-blue-600" />
              <span>Requirement Traceability Matrix (RTM)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Showing {sortedMatrix.length} requirements mapped to test cases
            </p>
          </div>

          <div className="flex items-center space-x-3 w-full sm:w-auto">
            <SearchBox
              value={search}
              onChange={(val) => {
                setSearch(val);
                setCurrentPage(1);
              }}
              placeholder="Search RTM..."
            />
            <Button
              onClick={handleExportCsv}
              variant="outline"
              size="md"
              icon={<Download className="w-4 h-4" />}
            >
              Export CSV
            </Button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase bg-slate-50">
                <th
                  onClick={() => {
                    setSortField('id');
                    setSortAsc(!sortAsc);
                  }}
                  className="py-3 px-4 w-36 cursor-pointer hover:bg-slate-100"
                >
                  Req ID {sortField === 'id' ? (sortAsc ? '▲' : '▼') : ''}
                </th>
                <th className="py-3 px-4">Requirement Statement</th>
                <th className="py-3 px-4">Mapped Test Cases</th>
                <th
                  onClick={() => {
                    setSortField('count');
                    setSortAsc(!sortAsc);
                  }}
                  className="py-3 px-4 w-24 text-center cursor-pointer hover:bg-slate-100"
                >
                  TC Count {sortField === 'count' ? (sortAsc ? '▲' : '▼') : ''}
                </th>
                <th className="py-3 px-4 w-36 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {paginatedRows.map((row) => {
                let badgeVariant: 'pass' | 'warning' | 'fail' = 'fail';
                if (row.status === 'Covered') badgeVariant = 'pass';
                else if (row.status === 'Partially Covered') badgeVariant = 'warning';

                return (
                  <tr key={row.requirement_id} className="hover:bg-slate-50/50">
                    <td className="py-3.5 px-4 font-bold text-blue-600">
                      {row.requirement_id}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-800 max-w-md">
                      {row.requirement_description}
                    </td>
                    <td className="py-3.5 px-4 text-xs font-mono text-slate-600">
                      {row.mapped_testcases.length > 0
                        ? row.mapped_testcases.join(', ')
                        : 'None'}
                    </td>
                    <td className="py-3.5 px-4 text-center font-bold text-slate-700">
                      {row.testcase_count}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <Badge variant={badgeVariant}>{row.status}</Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="flex justify-between items-center mt-6 pt-4 border-t border-slate-200 text-xs text-slate-500">
            <span>
              Page {currentPage} of {totalPages}
            </span>
            <div className="flex space-x-2">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                className="px-3 py-1 bg-white border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={currentPage === totalPages}
                onClick={() =>
                  setCurrentPage((prev) => Math.min(totalPages, prev + 1))
                }
                className="px-3 py-1 bg-white border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
