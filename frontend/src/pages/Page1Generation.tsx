import React, { useState } from 'react';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { FileUploader } from '../components/FileUploader';
import { apiService } from '../services/api';
import type { TestCase } from '../types';
import { Loader } from '../components/Loader';

export const Page1Generation: React.FC = () => {
  const [testcases, setTestcases] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (file: File) => {
    setLoading(true);
    try {
      await apiService.uploadRequirements(file);
      const res = await apiService.generateTestCases();
      setTestcases(res.testcases);
    } catch (e) {
      console.error(e);
      alert('Error processing file');
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(testcases, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", "generated_testcases.json");
    dlAnchorElem.click();
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-100 p-6">
        <h2 className="text-xl font-bold text-slate-800">Page 1: Requirements Processing & Test Case Generation</h2>
        <p className="text-sm text-slate-600 mt-1 max-w-2xl">
          Upload unstructured requirements (PDF, DOCX, TXT). The system will parse them and automatically generate structured test cases using NLP.
        </p>
      </Card>

      <Card>
        <FileUploader
          accept=".pdf,.docx,.txt,.json"
          onUpload={handleUpload}
          title="Drag and Drop Requirement File Here"
          subtitle="Click to browse or drop your SRS document"
          supportedFormatsText="PDF (.pdf), Microsoft Word (.docx), Text (.txt), JSON (.json)"
        />
      </Card>
      
      {loading && (
        <Card className="flex justify-center py-10 items-center">
           <Loader /> <span className="ml-4 font-bold text-indigo-600">Processing Requirements & Generating Test Cases...</span>
        </Card>
      )}

      {!loading && testcases.length > 0 && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-slate-800 text-lg">Generated Test Cases ({testcases.length})</h3>
            <button 
              onClick={downloadJSON} 
              className="bg-indigo-600 text-white px-4 py-2 rounded font-semibold text-sm hover:bg-indigo-700 transition"
            >
              Download Test Cases (JSON)
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase bg-slate-50">
                  <th className="py-3 px-4 w-28">ID</th>
                  <th className="py-3 px-4">Title</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">Priority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {testcases.map((tc) => (
                  <tr key={tc.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-4 font-bold text-indigo-600">{tc.id}</td>
                    <td className="py-3 px-4 font-medium text-slate-800">{tc.title}</td>
                    <td className="py-3 px-4 text-xs text-slate-600 max-w-xs truncate">{tc.description}</td>
                    <td className="py-3 px-4"><Badge variant="neutral">{tc.priority as string}</Badge></td>
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
