import { useEffect, useState } from 'react';
import { api } from '../../services/api';

export default function ReportStep({ projectId }) {
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    api.getProjectAnalysis(projectId).then((res) => setAnalysis(res.data)).catch(() => {});
  }, [projectId]);

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
    <div className="max-w-2xl mx-auto text-center">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Step 5 — Download Report</h2>
      <p className="text-slate-600 mb-6">Generate a PDF with before/after images and full cost breakdown.</p>
      {analysis?.house_description && (
        <p className="text-sm mb-5 p-3 rounded border bg-slate-50">{analysis.house_description}</p>
      )}

      {status === 'idle' && (
        <button
          onClick={handleGenerate}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
        >
          Generate PDF Report
        </button>
      )}

      {status === 'generating' && (
        <p className="text-blue-600">Generating report...</p>
      )}

      {error && <p className="text-red-600 mt-4">{error}</p>}

      {status === 'done' && report && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6">
          <p className="text-green-800 font-medium mb-4">Report generated successfully!</p>
          <p className="text-sm text-slate-600 mb-4">
            Grand Total: INR {report.grand_total_inr.toLocaleString()} · {report.total_days} days
          </p>
          <a
            href={api.reportDownloadUrl(projectId)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
          >
            Download PDF
          </a>
        </div>
      )}
    </div>
  );
}
