import React, { useState } from 'react';
import { Settings, Server, Info, CheckCircle2 } from 'lucide-react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';

export const SettingsPage: React.FC = () => {
  const [apiUrl, setApiUrl] = useState(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  );
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl mx-auto">
      {/* Top Card */}
      <Card className="bg-gradient-to-r from-slate-900 to-blue-950 text-white p-6 md:p-8 rounded-2xl shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-400/30">
            <Settings className="w-8 h-8 text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-extrabold tracking-tight">
              System Settings & Configuration
            </h2>
            <p className="text-slate-300 text-sm mt-0.5">
              Configure backend REST API endpoint URLs, application theme, and AI engine parameters.
            </p>
          </div>
        </div>
      </Card>

      {/* Backend API URL Config */}
      <Card>
        <h3 className="font-bold text-slate-800 text-base mb-4 flex items-center space-x-2">
          <Server className="w-5 h-5 text-blue-600" />
          <span>FastAPI Backend Server URL</span>
        </h3>

        <div className="space-y-4 max-w-lg">
          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
              API Base Endpoint URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg text-sm font-mono text-slate-800 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center space-x-3">
            <Button onClick={handleSave} variant="primary" size="md">
              Save Settings
            </Button>
            {saved && (
              <span className="inline-flex items-center text-xs font-semibold text-emerald-600 space-x-1">
                <CheckCircle2 className="w-4 h-4" />
                <span>Saved successfully!</span>
              </span>
            )}
          </div>
        </div>
      </Card>

      {/* About Project Specs Card */}
      <Card>
        <h3 className="font-bold text-slate-800 text-base mb-4 flex items-center space-x-2">
          <Info className="w-5 h-5 text-blue-600" />
          <span>About AI Test Case Validation System</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-slate-600">
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1">
            <p className="font-bold text-slate-800">Frontend Framework</p>
            <p className="text-xs text-slate-500">React 19, TypeScript, Vite, Tailwind CSS</p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1">
            <p className="font-bold text-slate-800">Backend Server</p>
            <p className="text-xs text-slate-500">FastAPI, Python 3.12, ReportLab, Pydantic v2</p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1">
            <p className="font-bold text-slate-800">NLP & Embedding Engine</p>
            <p className="text-xs text-slate-500">SentenceTransformers (all-MiniLM-L6-v2)</p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1">
            <p className="font-bold text-slate-800">Vector Math & Distance</p>
            <p className="text-xs text-slate-500">Scikit-Learn Cosine Similarity, RapidFuzz</p>
          </div>
        </div>
      </Card>
    </div>
  );
};
