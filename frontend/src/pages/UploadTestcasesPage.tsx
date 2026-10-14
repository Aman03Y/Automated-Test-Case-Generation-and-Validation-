import React, { useState } from 'react';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { FileUploader } from '../components/FileUploader';
import { SearchBox } from '../components/SearchBox';
import { apiService } from '../services/api';
import type { TestCase } from '../types';

export const UploadTestcasesPage: React.FC = () => {
  const [testcases, setTestcases] = useState<TestCase[]>([]);
  const [loadedCount, setLoadedCount] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const pageSize = 5;

  const handleTestcaseUpload = async (file: File) => {
    const res = await apiService.uploadTestcases(file);
    setTestcases(res.testcases);
    setLoadedCount(res.count);
  };

  const filteredTcs = testcases.filter(
    (tc) =>
      tc.id.toLowerCase().includes(search.toLowerCase()) ||
      tc.title.toLowerCase().includes(search.toLowerCase()) ||
      tc.description.toLowerCase().includes(search.toLowerCase())
  );

  const totalPages = Math.ceil(filteredTcs.length / pageSize) || 1;
  const paginatedTcs = filteredTcs.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className="space-y-8 animate-fade-in">
      <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-100 p-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-800">
              Upload Manual Software Test Cases
            </h2>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Load manually written test case JSON files into the AI validation engine. Converts inputs into validated Pydantic models with schema checks.
            </p>
          </div>
          {loadedCount !== null && (
            <Badge variant="pass" className="text-sm px-4 py-2">
              Loaded: {loadedCount} Test Cases
            </Badge>
          )}
        </div>
      </Card>

      <Card>
        <FileUploader
          accept=".json"
          onUpload={handleTestcaseUpload}
          title="Drag and Drop Test Case JSON File Here"
          subtitle="Click to browse or drop testcases.json document"
          supportedFormatsText="JSON format (.json)"
        />
      </Card>

      {/* Example Format */}
      <Card className="bg-slate-50 border-slate-200 p-6">
        <h3 className="font-bold text-slate-800 text-lg mb-4">Example Format (JSON)</h3>
        <pre className="bg-slate-800 text-slate-100 p-4 rounded-md text-sm overflow-x-auto">
{`[
  {
    "id": "TC001",
    "title": "Successful Login",
    "description": "Verify that a user can log in with valid credentials.",
    "steps": ["Enter email", "Enter password", "Click Login"],
    "expected_result": "User is redirected to the dashboard.",
    "priority": "High",
    "requirement_ids": ["REQ-001"]
  }
]`}
        </pre>
      </Card>

      {/* Test Cases Preview Table */}
      {testcases.length > 0 && (
        <Card>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
            <h3 className="font-bold text-slate-800 text-lg">
              Loaded Test Cases ({filteredTcs.length} of {testcases.length})
            </h3>
            <SearchBox
              value={search}
              onChange={(val) => {
                setSearch(val);
                setCurrentPage(1);
              }}
              placeholder="Search test cases..."
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase bg-slate-50">
                  <th className="py-3 px-4 w-28">ID</th>
                  <th className="py-3 px-4">Title</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4 w-28">Priority</th>
                  <th className="py-3 px-4 w-32">Mapped REQ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {paginatedTcs.map((tc) => {
                  const pLower = (tc.priority || 'medium').toLowerCase() as
                    | 'critical'
                    | 'high'
                    | 'medium'
                    | 'low';
                  const reqIds = tc.requirement_ids || (tc.requirement_id ? [tc.requirement_id] : []);

                  return (
                    <tr key={tc.id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-4 font-bold text-indigo-600">{tc.id}</td>
                      <td className="py-3 px-4 font-medium text-slate-800">{tc.title}</td>
                      <td className="py-3 px-4 text-xs text-slate-600 max-w-xs truncate">
                        {tc.description}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={pLower}>{tc.priority}</Badge>
                      </td>
                      <td className="py-3 px-4 text-xs font-semibold text-slate-600">
                        {reqIds.length > 0 ? reqIds.join(', ') : 'Unmapped'}
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
      )}
    </div>
  );
};
