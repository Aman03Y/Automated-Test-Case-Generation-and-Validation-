import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Play, CheckCircle2, ShieldCheck, ArrowRight } from 'lucide-react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { ProgressBar } from '../components/ProgressBar';
import { apiService } from '../services/api';
import type { ValidationReport } from '../types';

export const ValidationPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.85);
  const [semanticThreshold, setSemanticThreshold] = useState(0.75);
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  const pipelineSteps = [
    'Initializing AI Validation Engine...',
    'Step 1: Parsing Requirements & NLP Preprocessing...',
    'Step 2: Loading & Validating Manual Test Cases...',
    'Step 3: AI Semantic Duplicate Detection (SentenceTransformers)...',
    'Step 4: Requirement Coverage Analysis (Explicit + Vector Similarity)...',
    'Step 5: Compliance Rule Engine (9 Rule Evaluations)...',
    'Step 6: Calculating Enterprise Weighted Quality Score (35/35/20/10)...',
    'Step 6.5: Building Requirement Traceability Matrix (RTM)...',
    'Step 7: Compiling PDF, JSON, & Markdown Enterprise Reports...',
    'Validation Completed Successfully!',
  ];

  const handleRunValidation = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    setProgress(10);
    setCurrentStep(pipelineSteps[0]);

    try {
      // Simulate progress bar increments while API runs
      const timer1 = setTimeout(() => {
        setProgress(30);
        setCurrentStep(pipelineSteps[3]);
      }, 400);

      const timer2 = setTimeout(() => {
        setProgress(65);
        setCurrentStep(pipelineSteps[5]);
      }, 900);

      const resReport = await apiService.runValidation({
        similarity_threshold: similarityThreshold,
        semantic_threshold: semanticThreshold,
      });

      clearTimeout(timer1);
      clearTimeout(timer2);

      setProgress(100);
      setCurrentStep(pipelineSteps[9]);
      setReport(resReport);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Validation execution failed. Ensure requirements and test cases are uploaded first.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl mx-auto">
      {/* Header Banner */}
      <Card className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white p-8 text-center rounded-2xl shadow-xl">
        <div className="inline-flex p-3 bg-blue-500/20 rounded-2xl mb-4 border border-blue-400/30">
          <ShieldCheck className="w-10 h-10 text-blue-400" />
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight">
          AI Validation Engine Pipeline
        </h2>
        <p className="text-slate-300 text-sm mt-2 max-w-xl mx-auto">
          Execute automated quality analysis across uploaded requirements and test cases to detect duplicate test cases, unmapped requirements, and compliance rule defects.
        </p>

        {/* Configuration Sliders */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 text-left bg-white/10 p-5 rounded-xl border border-white/15">
          <div>
            <div className="flex justify-between text-xs font-semibold text-blue-200 mb-1">
              <span>Duplicate Threshold</span>
              <span>{(similarityThreshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="0.99"
              step="0.01"
              value={similarityThreshold}
              onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
              disabled={loading}
              className="w-full h-2 bg-blue-950 rounded-lg appearance-none cursor-pointer accent-blue-400"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-blue-200 mb-1">
              <span>Semantic Coverage Threshold</span>
              <span>{(semanticThreshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="0.99"
              step="0.01"
              value={semanticThreshold}
              onChange={(e) => setSemanticThreshold(parseFloat(e.target.value))}
              disabled={loading}
              className="w-full h-2 bg-blue-950 rounded-lg appearance-none cursor-pointer accent-blue-400"
            />
          </div>
        </div>

        {/* Main Big Button */}
        <div className="mt-8 flex justify-center">
          <Button
            onClick={handleRunValidation}
            isLoading={loading}
            variant="success"
            size="lg"
            className="text-lg px-8 py-4 shadow-lg hover:scale-105 transition-transform"
            icon={<Play className="w-6 h-6 fill-current" />}
          >
            {loading ? 'Running AI Engine...' : 'Run Validation Pipeline'}
          </Button>
        </div>
      </Card>

      {/* Progress Indicator */}
      {loading && (
        <Card className="p-6 text-center space-y-4">
          <ProgressBar
            value={progress}
            label={currentStep}
            color="blue"
            height="lg"
          />
        </Card>
      )}

      {error && (
        <Card className="bg-rose-50 border-rose-200 text-rose-800 p-5">
          <h4 className="font-bold text-base">Execution Error</h4>
          <p className="text-sm mt-1">{error}</p>
        </Card>
      )}

      {/* Success Completion Result Card */}
      {report && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <Card className="bg-emerald-50/80 border-emerald-200 p-8 text-center space-y-6">
            <div className="inline-flex p-4 bg-emerald-100 text-emerald-600 rounded-full">
              <CheckCircle2 className="w-12 h-12" />
            </div>

            <div>
              <h3 className="text-2xl font-extrabold text-emerald-900">
                Validation Pipeline Completed!
              </h3>
              <p className="text-sm text-emerald-700 mt-1">
                Evaluated {report.summary.total_testcases} test cases against {report.summary.total_requirements} software requirements.
              </p>
            </div>

            <div className="flex justify-center space-x-6">
              <div className="bg-white px-6 py-3 rounded-xl shadow-xs border border-emerald-200">
                <span className="text-xs text-slate-500 uppercase font-semibold">Quality Score</span>
                <p className="text-2xl font-black text-blue-600">{report.quality_score.toFixed(1)} / 100</p>
              </div>

              <div className="bg-white px-6 py-3 rounded-xl shadow-xs border border-emerald-200">
                <span className="text-xs text-slate-500 uppercase font-semibold">Rating</span>
                <p className="text-2xl font-black text-emerald-600">{report.summary.grade}</p>
              </div>
            </div>

            <div className="pt-2 flex justify-center space-x-4">
              <Button
                onClick={() => navigate('/results')}
                variant="primary"
                size="lg"
                icon={<ArrowRight className="w-5 h-5" />}
              >
                View Detailed Results
              </Button>
              <Button
                onClick={() => navigate('/reports')}
                variant="outline"
                size="lg"
              >
                Download Export Reports
              </Button>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  );
};
