import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Alert, Spinner, StepHeader } from '../ui/kit';
import VariantBar from '../variants/VariantBar';

export default function ReportStep({ projectId }) {
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    api.getProjectAnalysis(projectId).then((res) => setAnalysis(res.data)).catch(() => {});
  }, [projectId]);

  // Switching the active design lets the user report a different one.
  const onVariantChanged = () => {
    setStatus('idle');
    setReport(null);
    setError(null);
  };

  const handleGenerate = async () => {
    setError(null);
    setStatus('generating');
    try {
      const res = await api.generateReport(projectId);
      if (!res.success) throw new Error(res.msg);
      setReport(res.data);
      setStatus('done');
    } catch (e) {
      setError(e.message);
      setStatus('error');
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <StepHeader
        index={5}
        total={5}
        title="Your renovation report"
        subtitle="Generate a shareable PDF for the active design — before/after images, materials, quantities and the full cost breakdown. Switch designs below to report a different one."
      />

      <VariantBar projectId={projectId} onChanged={onVariantChanged} />

      {analysis?.house_description && (
        <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-relaxed text-slate-600 shadow-card">
          {analysis.house_description}
        </div>
      )}

      {status !== 'done' && (
        <div className="card flex flex-col items-center gap-5 p-10 text-center">
          <div className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-soft">
            <svg viewBox="0 0 24 24" fill="none" className="h-8 w-8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" />
              <path d="M14 3v5h5M9 13h6M9 17h6" />
            </svg>
          </div>
          <div>
            <p className="font-semibold text-slate-800">Compile your full renovation report</p>
            <p className="mt-1 text-sm text-slate-500">Everything from the previous steps in one professional PDF.</p>
          </div>
          <button onClick={handleGenerate} disabled={status === 'generating'} className="btn-primary">
            {status === 'generating' ? <Spinner /> : (
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 16V4m0 0L8 8m4-4l4 4" transform="rotate(180 12 10)" />
                <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
              </svg>
            )}
            {status === 'generating' ? 'Generating…' : 'Generate PDF Report'}
          </button>
        </div>
      )}

      {error && <Alert variant="error" className="mt-5">{error}</Alert>}

      {status === 'done' && report && (
        <div className="card overflow-hidden p-0">
          <div className="flex flex-col items-center gap-2 border-b border-emerald-100 bg-gradient-to-br from-emerald-50 to-white p-8 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-full bg-emerald-600 text-white shadow-soft">
              <svg viewBox="0 0 24 24" fill="none" className="h-7 w-7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6L9 17l-5-5" />
              </svg>
            </div>
            <p className="font-display text-xl font-bold text-slate-900">Report ready!</p>
            <p className="text-sm text-slate-500">Your renovation plan has been compiled successfully.</p>
          </div>

          <div className="grid grid-cols-2 divide-x divide-slate-100 border-b border-slate-100">
            <div className="p-5 text-center">
              <p className="text-xs uppercase tracking-wide text-slate-400">Grand Total</p>
              <p className="mt-1 font-display text-2xl font-bold text-slate-900">
                ₹{Number(report.grand_total_inr).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <div className="p-5 text-center">
              <p className="text-xs uppercase tracking-wide text-slate-400">Duration</p>
              <p className="mt-1 font-display text-2xl font-bold text-slate-900">{report.total_days} days</p>
            </div>
          </div>

          <div className="p-6 text-center">
            <a
              href={api.reportDownloadUrl(projectId)}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-success w-full sm:w-auto"
            >
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 4v12m0 0l-4-4m4 4l4-4" />
                <path d="M4 18v1a2 2 0 002 2h12a2 2 0 002-2v-1" />
              </svg>
              Download PDF
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
