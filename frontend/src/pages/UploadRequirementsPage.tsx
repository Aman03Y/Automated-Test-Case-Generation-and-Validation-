import React, { useState } from 'react';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { FileUploader } from '../components/FileUploader';
import { apiService } from '../services/api';
import type { Requirement } from '../types';

export const UploadRequirementsPage: React.FC = () => {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [parsedCount, setParsedCount] = useState<number | null>(null);

  const handleRequirementUpload = async (file: File) => {
    const res = await apiService.uploadRequirements(file);
    setRequirements(res.requirements);
    setParsedCount(res.count);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-100 p-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-800">
              Upload Software Requirement Specifications
            </h2>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Extract functional software requirements automatically from PDF, Word (.docx), Plain Text (.txt), or JSON documents using the Requirement Parser module.
            </p>
          </div>
          {parsedCount !== null && (
            <Badge variant="pass" className="text-sm px-4 py-2">
              Parsed: {parsedCount} Requirements Loaded
            </Badge>
          )}
        </div>
      </Card>

      <Card>
        <FileUploader
          accept=".pdf,.docx,.txt,.json"
          onUpload={handleRequirementUpload}
          title="Drag and Drop Requirement File Here"
          subtitle="Click to browse or drop your SRS / Requirement document"
          supportedFormatsText="PDF (.pdf), Microsoft Word (.docx), Text (.txt), JSON (.json)"
        />
      </Card>

      {/* Example Format */}
      <Card className="bg-slate-50 border-slate-200 p-6">
        <h3 className="font-bold text-slate-800 text-lg mb-4">Example Format (JSON)</h3>
        <pre className="bg-slate-800 text-slate-100 p-4 rounded-md text-sm overflow-x-auto">
{`[
  {
    "id": "REQ-001",
    "requirement": "The system shall allow users to log in using their email and password.",
    "category": "Authentication"
  }
]`}
        </pre>
      </Card>

      {/* Parsed Requirements Preview Table */}
      {requirements.length > 0 && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-slate-800 text-lg">
              Extracted Requirements ({requirements.length})
            </h3>
            <Badge variant="neutral">Parsed Data Preview</Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase bg-slate-50">
                  <th className="py-3 px-4 w-32">Requirement ID</th>
                  <th className="py-3 px-4">Requirement Statement</th>
                  <th className="py-3 px-4 w-32">Category</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {requirements.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-4 font-bold text-blue-600">{req.id}</td>
                    <td className="py-3 px-4 font-medium text-slate-700">
                      {req.requirement}
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant="neutral">{req.category || 'Functional'}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
