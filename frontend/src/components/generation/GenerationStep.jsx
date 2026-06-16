import { useCallback, useEffect, useRef, useState } from 'react';
import { api, imageUrl } from '../../services/api';
import { useTaskPoller } from '../../hooks/useTaskPoller';
import { Alert, Spinner, StepHeader } from '../ui/kit';
import VariantBar from '../variants/VariantBar';

export default function GenerationStep({ projectId, analysis, onComplete }) {
  const [taskId, setTaskId] = useState(null);
  const [error, setError] = useState(null);
  const [images, setImages] = useState({ original: null, generated: null });
  const [activeVariantId, setActiveVariantId] = useState(null);
  const [running, setRunning] = useState(false);
  const [intent, setIntent] = useState('');
  const startedRef = useRef(false);

  const load = useCallback(async () => {
    try {
      const [variantsRes, imagesRes] = await Promise.all([
        api.listVariants(projectId),
        api.getImages(projectId),
      ]);
      const active = (variantsRes.data || []).find((v) => v.is_active);
      setActiveVariantId(active?.id || null);
      const data = imagesRes.data || [];
      setImages({
        original: data.find((i) => i.image_type === 'original') || null,
        generated: data.find((i) => i.image_type === 'generated' && i.variant_id === active?.id) || null,
      });
    } catch (e) {
      setError(e.message);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleTaskComplete = useCallback(async () => {
    setRunning(false);
    startedRef.current = false;
    await load();
  }, [load]);

  const handleTaskFailed = useCallback((msg) => {
    setRunning(false);
    startedRef.current = false;
    setError(msg || 'Generation failed');
  }, []);

  const { status } = useTaskPoller(taskId, {
    intervalMs: 4000,
    onComplete: handleTaskComplete,
    onFailed: handleTaskFailed,
  });

  const startGeneration = async () => {
    if (startedRef.current) return;
    startedRef.current = true;
    setRunning(true);
    setError(null);
    try {
      // Mask support still exists in the backend (mask_image_path); the UI just
      // doesn't expose a mask upload, so none is sent from here.
      const res = await api.triggerGeneration(projectId, {
        zone_context: intent,
        variant_id: activeVariantId,
      });
      if (!res.success) throw new Error(res.msg);
      setTaskId(res.data.task_id);
    } catch (e) {
      startedRef.current = false;
      setRunning(false);
      setError(e.message);
    }
  };

  const onVariantChanged = async () => {
    setTaskId(null);
    setRunning(false);
    startedRef.current = false;
    setError(null);
    // Intent is per-design — don't carry one design's prompt into another.
    setIntent('');
    await load();
  };

  // Gate on an active taskId so a stale poller status (left over from a previous
  // variant's generation) can't keep the spinner up after switching designs.
  const isLoading = running || (!!taskId && (status === 'pending' || status === 'processing'));
  const hasPreview = !!images.generated;

  return (
    <div className="mx-auto max-w-5xl">
      <StepHeader
        index={3}
        total={5}
        title="Renovation preview"
        subtitle="Generate a redesigned view of your home for the active design. Create more designs to compare different material combinations side by side."
      />

      <VariantBar projectId={projectId} onChanged={onVariantChanged} />

      {analysis?.house_description && (
        <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-relaxed text-slate-600 shadow-card">
          {analysis.house_description}
        </div>
      )}

      {!isLoading && !hasPreview && (
        <div className="card mb-6 space-y-5 p-6 sm:p-8">
          <p className="text-sm font-medium text-slate-700">Generate the preview for this design:</p>
          <div>
            <label className="label">Extra generation intent <span className="font-normal text-slate-400">(optional)</span></label>
            <input
              className="input"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g. keep balcony untouched, modern textured finish on upper wall"
            />
          </div>
          <button onClick={startGeneration} className="btn-primary">
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M13 3l2.5 6.5L22 12l-6.5 2.5L13 21l-2.5-6.5L4 12l6.5-2.5L13 3z" /></svg>
            Start Generation
          </button>
        </div>
      )}

      {isLoading && (
        <div className="card flex flex-col items-center justify-center gap-4 border-brand-200 bg-gradient-to-br from-brand-50 to-white p-12 text-center">
          <div className="relative grid h-16 w-16 place-items-center">
            <span className="absolute inset-0 animate-ping rounded-full bg-brand-300/50" />
            <span className="relative grid h-12 w-12 place-items-center rounded-full bg-brand-600 text-white"><Spinner className="h-6 w-6" /></span>
          </div>
          <div>
            <p className="font-semibold text-brand-900">Generating your renovation…</p>
            <p className="mt-1 text-sm text-brand-600">This usually takes 30–90 seconds{status ? ` · ${status}` : ''}</p>
          </div>
        </div>
      )}

      {error && <Alert variant="error" className="mb-6">{error}</Alert>}

      {images.original && images.generated && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {[
            { img: images.original, label: 'Before', tone: 'bg-slate-700' },
            { img: images.generated, label: 'After', tone: 'bg-emerald-600' },
          ].map(({ img, label, tone }) => (
            <figure key={label} className="card overflow-hidden p-0">
              <div className="relative">
                <span className={`absolute left-3 top-3 z-10 rounded-full px-3 py-1 text-xs font-semibold text-white ${tone}`}>{label}</span>
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
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
          </button>
        </div>
      )}
    </div>
  );
}
