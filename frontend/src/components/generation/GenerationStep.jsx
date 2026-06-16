import { useCallback, useEffect, useState } from 'react';
import { api, imageUrl } from '../../services/api';
import { useTaskPoller } from '../../hooks/useTaskPoller';
import { Alert, Spinner, StepHeader } from '../ui/kit';

export default function GenerationStep({ projectId, analysis, onComplete }) {
  const [taskId, setTaskId] = useState(null);
  const [error, setError] = useState(null);
  const [images, setImages] = useState({ original: null, generated: null });
  const [started, setStarted] = useState(false);
  const [maskFile, setMaskFile] = useState(null);
  const [intent, setIntent] = useState('');
  const [autoStartRequested, setAutoStartRequested] = useState(false);

  const handleTaskComplete = useCallback(async () => {
    const res = await api.getImages(projectId);
    const original = res.data?.find((i) => i.image_type === 'original');
    const generated = res.data?.find((i) => i.image_type === 'generated');
    setImages({ original, generated });
  }, [projectId]);

  const handleTaskFailed = useCallback((msg) => {
    setError(msg || 'Generation failed');
  }, []);

  const { status } = useTaskPoller(taskId, {
    intervalMs: 4000,
    onComplete: handleTaskComplete,
    onFailed: handleTaskFailed,
  });

  useEffect(() => {
    const start = async () => {
      try {
        setStarted(true);
        let maskPath = null;
        if (maskFile) {
          const maskUpload = await api.uploadMask(projectId, maskFile);
          maskPath = maskUpload?.data?.file_path || null;
        }
        const res = await api.triggerGeneration(projectId, {
          mask_image_path: maskPath,
          zone_context: intent,
        });
        if (!res.success) throw new Error(res.msg);
        setTaskId(res.data.task_id);
      } catch (e) {
        setError(e.message);
      }
    };
    if (projectId && !started && autoStartRequested) start();
  }, [projectId, started, maskFile, intent, autoStartRequested]);

  const isLoading = (status === 'pending' || status === 'processing' || (!images.generated && !error && started));

  return (
    <div className="mx-auto max-w-5xl">
      <StepHeader
        index={3}
        total={5}
        title="Renovation preview"
        subtitle="Our AI renders your home with the selected materials while preserving the original structure. Compare before and after side by side."
      />

      {analysis?.house_description && (
        <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-relaxed text-slate-600 shadow-card">
          {analysis.house_description}
        </div>
      )}

      {!started && (
        <div className="card mb-6 space-y-5 p-6 sm:p-8">
          <div>
            <label className="label">Mask image <span className="font-normal text-slate-400">(optional — white area = edit zone)</span></label>
            <input
              type="file"
              accept="image/png,image/jpeg"
              onChange={(e) => setMaskFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-slate-500 file:mr-4 file:rounded-lg file:border-0 file:bg-brand-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-brand-700 hover:file:bg-brand-100"
            />
          </div>
          <div>
            <label className="label">Extra generation intent <span className="font-normal text-slate-400">(optional)</span></label>
            <input
              className="input"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g. keep balcony untouched, modern textured finish on upper wall"
            />
          </div>
          <button onClick={() => setAutoStartRequested(true)} className="btn-primary">
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M13 3l2.5 6.5L22 12l-6.5 2.5L13 21l-2.5-6.5L4 12l6.5-2.5L13 3z" />
            </svg>
            Start Generation
          </button>
        </div>
      )}

      {isLoading && (
        <div className="card flex flex-col items-center justify-center gap-4 border-brand-200 bg-gradient-to-br from-brand-50 to-white p-12 text-center">
          <div className="relative grid h-16 w-16 place-items-center">
            <span className="absolute inset-0 animate-ping rounded-full bg-brand-300/50" />
            <span className="relative grid h-12 w-12 place-items-center rounded-full bg-brand-600 text-white">
              <Spinner className="h-6 w-6" />
            </span>
          </div>
          <div>
            <p className="font-semibold text-brand-900">Generating your renovation…</p>
            <p className="mt-1 text-sm text-brand-600">This usually takes 30–90 seconds{status ? ` · ${status}` : ''}</p>
          </div>
        </div>
      )}

      {error && <Alert variant="error">{error}</Alert>}

      {images.original && images.generated && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {[
            { img: images.original, label: 'Before', tone: 'bg-slate-700' },
            { img: images.generated, label: 'After', tone: 'bg-emerald-600' },
          ].map(({ img, label, tone }) => (
            <figure key={label} className="card overflow-hidden p-0">
              <div className="relative">
                <span className={`absolute left-3 top-3 z-10 rounded-full px-3 py-1 text-xs font-semibold text-white ${tone}`}>
                  {label}
                </span>
                <img src={imageUrl(img.file_path)} alt={label} className="w-full object-cover" />
              </div>
            </figure>
          ))}
        </div>
      )}

      {images.generated && (
        <div className="mt-8 flex justify-end">
          <button onClick={onComplete} className="btn-success">
            Proceed to Estimation
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
