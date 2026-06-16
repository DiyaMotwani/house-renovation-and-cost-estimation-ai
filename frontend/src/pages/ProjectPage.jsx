import { useState } from 'react';
import UploadStep from '../components/upload/UploadStep';
import ZoneStep from '../components/zones/ZoneStep';
import GenerationStep from '../components/generation/GenerationStep';
import EstimationStep from '../components/estimation/EstimationStep';
import ReportStep from '../components/report/ReportStep';

const STEPS = ['upload', 'zones', 'generate', 'estimate', 'report'];

export default function ProjectPage() {
  const [step, setStep] = useState(0);
  const [projectId, setProjectId] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  const goNext = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-slate-900">House Renovation AI</h1>
          <nav className="flex gap-2 mt-3 flex-wrap">
            {STEPS.map((label, i) => (
              <span
                key={label}
                className={`text-xs px-3 py-1 rounded-full ${
                  i === step ? 'bg-blue-600 text-white' : i < step ? 'bg-green-100 text-green-800' : 'bg-slate-200 text-slate-600'
                }`}
              >
                {i + 1}. {label}
              </span>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {step === 0 && (
          <UploadStep
            onComplete={({ projectId: pid, suggestions: sug, analysis: ana }) => {
              setProjectId(pid);
              setSuggestions(sug);
              setAnalysis(ana);
              goNext();
            }}
          />
        )}
        {step === 1 && projectId && (
          <ZoneStep projectId={projectId} suggestions={suggestions} analysis={analysis} onComplete={goNext} />
        )}
        {step === 2 && projectId && (
          <GenerationStep projectId={projectId} analysis={analysis} onComplete={goNext} />
        )}
        {step === 3 && projectId && (
          <EstimationStep projectId={projectId} onComplete={goNext} />
        )}
        {step === 4 && projectId && (
          <ReportStep projectId={projectId} />
        )}
      </main>
    </div>
  );
}
