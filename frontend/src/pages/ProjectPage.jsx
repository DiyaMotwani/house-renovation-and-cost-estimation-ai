import { useEffect, useState } from 'react';
import UploadStep from '../components/upload/UploadStep';
import ZoneStep from '../components/zones/ZoneStep';
import GenerationStep from '../components/generation/GenerationStep';
import EstimationStep from '../components/estimation/EstimationStep';
import ReportStep from '../components/report/ReportStep';
import { Icons } from '../components/ui/kit';

const STEPS = [
  { key: 'upload', label: 'Upload', icon: Icons.upload },
  { key: 'zones', label: 'Zones & Materials', icon: Icons.zones },
  { key: 'generate', label: 'Preview', icon: Icons.generate },
  { key: 'estimate', label: 'Estimate', icon: Icons.estimate },
  { key: 'report', label: 'Report', icon: Icons.report },
];

const STORAGE_KEY = 'hra_session';

// Restore an in-progress project so a page refresh resumes where you left off.
function loadSession() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

export default function ProjectPage() {
  const saved = loadSession();
  const [step, setStep] = useState(saved.projectId ? saved.step ?? 0 : 0);
  const [maxStep, setMaxStep] = useState(saved.projectId ? saved.maxStep ?? saved.step ?? 0 : 0);
  const [projectId, setProjectId] = useState(saved.projectId ?? null);
  const [suggestions, setSuggestions] = useState(saved.suggestions ?? null);
  const [analysis, setAnalysis] = useState(saved.analysis ?? null);

  // Persist progress on every change so refresh / accidental close is safe.
  useEffect(() => {
    if (!projectId) {
      localStorage.removeItem(STORAGE_KEY);
      return;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ step, maxStep, projectId, suggestions, analysis }));
  }, [step, maxStep, projectId, suggestions, analysis]);

  const goNext = () =>
    setStep((s) => {
      const next = Math.min(s + 1, STEPS.length - 1);
      setMaxStep((m) => Math.max(m, next));
      return next;
    });

  const goBack = () => setStep((s) => Math.max(0, s - 1));

  // Jump to any step already reached (never skip ahead to unvisited steps).
  const goTo = (i) => {
    if (i <= maxStep) setStep(i);
  };

  const startOver = () => {
    if (projectId && !window.confirm('Start a new project? Your current progress will be cleared from this browser.')) {
      return;
    }
    localStorage.removeItem(STORAGE_KEY);
    setProjectId(null);
    setSuggestions(null);
    setAnalysis(null);
    setStep(0);
    setMaxStep(0);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Ambient background accents */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-32 h-96 w-96 rounded-full bg-brand-200/30 blur-3xl" />
        <div className="absolute top-1/3 -left-40 h-96 w-96 rounded-full bg-accent-100/40 blur-3xl" />
      </div>

      <div className="relative">
        <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/80 backdrop-blur-lg">
          <div className="mx-auto max-w-6xl px-4">
            <div className="flex items-center justify-between py-4">
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-soft">
                  <svg viewBox="0 0 24 24" fill="none" className="h-6 w-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 11l9-7 9 7" />
                    <path d="M5 10v10h14V10" />
                    <path d="M9 20v-6h6v6" />
                  </svg>
                </div>
                <div>
                  <h1 className="font-display text-lg font-bold leading-none text-slate-900">
                    House Renovation <span className="text-brand-600">AI</span>
                  </h1>
                  <p className="mt-1 text-xs text-slate-500">Visualize · Estimate · Renovate</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="pill hidden bg-brand-50 text-brand-700 sm:inline-flex">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-500" />
                  AI-powered planning
                </span>
                {projectId && (
                  <button onClick={startOver} className="btn-secondary px-3.5 py-2 text-sm">
                    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 2v6h6" />
                      <path d="M3.5 8a9 9 0 109-5.5" />
                    </svg>
                    New project
                  </button>
                )}
              </div>
            </div>

            <Stepper current={step} maxStep={maxStep} onSelect={goTo} />
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-10">
          {step > 0 && (
            <button
              onClick={goBack}
              className="mb-5 inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 transition hover:text-brand-700"
            >
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 12H5M11 18l-6-6 6-6" />
              </svg>
              Back to {STEPS[step - 1].label}
            </button>
          )}
          <div key={step} className="animate-fade-in-up">
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
            {step === 3 && projectId && <EstimationStep projectId={projectId} onComplete={goNext} />}
            {step === 4 && projectId && <ReportStep projectId={projectId} />}
          </div>
        </main>

        <footer className="relative border-t border-slate-200/70 py-6">
          <p className="mx-auto max-w-6xl px-4 text-center text-xs text-slate-400">
            Estimates are advisory and intended as a pre-construction planning aid — not a binding quotation.
          </p>
        </footer>
      </div>
    </div>
  );
}

function Stepper({ current, maxStep, onSelect }) {
  return (
    <nav className="-mx-1 flex items-center gap-1 overflow-x-auto pb-4 pt-1">
      {STEPS.map((s, i) => {
        const done = i < current;
        const active = i === current;
        const reachable = i <= maxStep;
        const Icon = s.icon;
        return (
          <div key={s.key} className="flex min-w-fit flex-1 items-center">
            <button
              type="button"
              onClick={() => onSelect(i)}
              disabled={!reachable}
              title={reachable ? `Go to ${s.label}` : 'Not available yet'}
              className={`flex items-center gap-2.5 rounded-xl px-1 py-1 text-left transition ${
                reachable && !active ? 'cursor-pointer hover:bg-slate-100/70' : ''
              } ${reachable ? '' : 'cursor-not-allowed'}`}
            >
              <div
                className={`grid h-9 w-9 shrink-0 place-items-center rounded-full border transition-colors ${
                  active
                    ? 'border-brand-600 bg-brand-600 text-white shadow-soft'
                    : done
                      ? 'border-emerald-500 bg-emerald-500 text-white'
                      : 'border-slate-300 bg-white text-slate-400'
                }`}
              >
                {done ? <Icons.check className="h-4 w-4" /> : <Icon className="h-[18px] w-[18px]" />}
              </div>
              <div className="hidden sm:block">
                <p
                  className={`text-[11px] font-semibold uppercase tracking-wide ${
                    active ? 'text-brand-700' : done ? 'text-emerald-600' : 'text-slate-400'
                  }`}
                >
                  Step {i + 1}
                </p>
                <p className={`text-sm font-medium leading-tight ${active || done ? 'text-slate-800' : 'text-slate-400'}`}>
                  {s.label}
                </p>
              </div>
            </button>
            {i < STEPS.length - 1 && (
              <div className="mx-2 h-px flex-1 min-w-[16px] rounded bg-gradient-to-r from-slate-200 to-slate-200">
                <div className={`h-px rounded transition-all duration-500 ${done ? 'w-full bg-emerald-400' : 'w-0'}`} />
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}
