import { useCallback, useEffect, useState } from 'react';
import { api, imageUrl } from '../../services/api';
import { useTaskPoller } from '../../hooks/useTaskPoller';

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
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Step 3 — Renovation Preview</h2>
      <p className="text-slate-600 mb-6">AI-generated visualization of your renovated house.</p>
      {analysis?.house_description && (
        <p className="text-sm text-slate-700 mb-4 bg-slate-50 border rounded-lg p-3">{analysis.house_description}</p>
      )}
      {!started && (
        <div className="grid gap-3 mb-5">
          <label className="text-sm">
            <span className="block mb-1 text-slate-600">Optional mask image (white area = edit zone)</span>
            <input type="file" accept="image/png,image/jpeg" onChange={(e) => setMaskFile(e.target.files?.[0] || null)} />
          </label>
          <label className="text-sm">
            <span className="block mb-1 text-slate-600">Extra generation intent</span>
            <input
              className="border rounded px-3 py-2 w-full"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g. keep balcony untouched, modern textured finish on upper wall"
            />
          </label>
          <button
            onClick={() => setAutoStartRequested(true)}
            className="w-fit bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Start Generation
          </button>
        </div>
      )}

      {isLoading && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-8 text-center">
          <div className="animate-pulse text-blue-700 font-medium">
            Generating your renovation — this takes 30–90 seconds
          </div>
          {status && <p className="text-sm text-blue-500 mt-2">Status: {status}</p>}
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>
      )}

      {images.original && images.generated && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold mb-2 text-center">Before</h3>
            <img
              src={imageUrl(images.original.file_path)}
              alt="Before"
              className="rounded-lg border w-full"
            />
          </div>
          <div>
            <h3 className="font-semibold mb-2 text-center">After</h3>
            <img
              src={imageUrl(images.generated.file_path)}
              alt="After"
              className="rounded-lg border w-full"
            />
          </div>
        </div>
      )}

      {images.generated && (
        <button
          onClick={onComplete}
          className="mt-6 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
        >
          Proceed to Estimation
        </button>
      )}
    </div>
  );
}
