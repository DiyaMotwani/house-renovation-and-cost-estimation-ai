import { useCallback, useEffect, useState } from 'react';
import { api, imageUrl } from '../../services/api';
import { useTaskPoller } from '../../hooks/useTaskPoller';
import { Alert, Spinner, StepHeader } from '../ui/kit';

export default function UploadStep({ onComplete }) {
  const [name, setName] = useState('');
  const [projectId, setProjectId] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [sketchPath, setSketchPath] = useState(null);
  const [zoneCount, setZoneCount] = useState(0);
  const [analysis, setAnalysis] = useState(null);

  const handleTaskComplete = useCallback(async (taskResult) => {
    if (taskResult?.validation?.quality === 'fail') {
      setError(taskResult.validation.reason || 'Image quality check failed');
      return;
    }

    const zones = taskResult?.zones?.zones || [];
    setZoneCount(zones.length);

    if (taskResult?.sketch_path) {
      setSketchPath(taskResult.sketch_path);
    }
    setAnalysis(taskResult?.analysis || null);
  }, []);

  const handleTaskFailed = useCallback((msg) => {
    setError(msg || 'Image processing failed');
  }, []);

  const { status, result, error: pollError } = useTaskPoller(taskId, {
    intervalMs: 4000,
    onComplete: handleTaskComplete,
    onFailed: handleTaskFailed,
  });

  useEffect(() => {
    if (!result?.sketch_path || sketchPath) return;
    if (projectId) {
      api.getImages(projectId).then((images) => {
        const sketch = images.data?.find((i) => i.image_type === 'sketch');
        if (sketch) setSketchPath(sketch.file_path);
      }).catch(() => {});
    }
  }, [result, projectId, sketchPath]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSketchPath(null);
    setZoneCount(0);
    if (!name.trim() || !file) {
      setError('Enter a project name and select an image');
      return;
    }
    try {
      setSubmitting(true);
      let pid = projectId;
      if (!pid) {
        const created = await api.createProject(name.trim());
        pid = created?.data?.id;
        if (!pid) throw new Error(created?.msg || 'Project creation failed');
        setProjectId(pid);
      }
      const uploaded = await api.uploadImage(pid, file);
      const nextTaskId = uploaded?.data?.task_id;
      if (!nextTaskId) throw new Error(uploaded?.msg || 'Upload did not return a task id');
      setTaskId(nextTaskId);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const validationFailed = result?.validation?.quality === 'fail';
  const isProcessing = status === 'processing' || status === 'pending';
  const canProceed = status === 'completed' && !validationFailed && projectId && zoneCount > 0;

  return (
    <div className="mx-auto max-w-2xl">
      <StepHeader
        index={1}
        total={5}
        title="Upload your house photo"
        subtitle="Start with a clear, front-facing exterior shot. Our AI will detect renovatable zones and analyse the structure automatically."
      />

      <form onSubmit={handleSubmit} className="card space-y-6 p-6 sm:p-8">
        <div>
          <label className="label">Project name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="input"
            placeholder="My Home Renovation"
            disabled={!!projectId}
          />
        </div>

        <div>
          <label className="label">House photo</label>
          <label
            className={`group flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition ${
              file ? 'border-brand-300 bg-brand-50/50' : 'border-slate-300 bg-slate-50/60 hover:border-brand-400 hover:bg-brand-50/40'
            }`}
          >
            <div className="grid h-12 w-12 place-items-center rounded-full bg-white text-brand-600 shadow-soft transition group-hover:scale-105">
              <svg viewBox="0 0 24 24" fill="none" className="h-6 w-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 16V4m0 0L8 8m4-4l4 4" />
                <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
              </svg>
            </div>
            {file ? (
              <p className="mt-3 text-sm font-medium text-slate-700">{file.name}</p>
            ) : (
              <>
                <p className="mt-3 text-sm font-medium text-slate-700">Click to choose a photo</p>
                <p className="mt-1 text-xs text-slate-400">JPG or PNG · clear daytime exterior works best</p>
              </>
            )}
            <input
              type="file"
              accept="image/jpeg,image/png"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
            />
          </label>
        </div>

        <button type="submit" disabled={submitting || isProcessing} className="btn-primary w-full sm:w-auto">
          {(submitting || isProcessing) && <Spinner />}
          {submitting ? 'Uploading…' : isProcessing ? 'Validating…' : 'Upload & Validate'}
        </button>
      </form>

      {(error || pollError || validationFailed) && (
        <Alert variant="error" className="mt-5" title="We couldn't use that photo">
          {error || pollError || result?.validation?.reason || 'Validation failed. Please upload a clearer exterior photo.'}
        </Alert>
      )}

      {taskId && status && isProcessing && (
        <div className="mt-5 flex items-center gap-3 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
          <Spinner className="h-4 w-4" />
          <span>Analysing image & detecting zones — this may take 30–60 seconds.</span>
        </div>
      )}

      {status === 'completed' && !validationFailed && zoneCount > 0 && (
        <Alert variant="success" className="mt-5">
          <strong>{zoneCount}</strong> zone{zoneCount !== 1 ? 's' : ''} detected successfully.
        </Alert>
      )}

      {status === 'completed' && !validationFailed && zoneCount === 0 && (
        <Alert variant="warning" className="mt-5">
          Processing finished but no zones were detected. Try uploading a clearer exterior photo.
        </Alert>
      )}

      {sketchPath && (
        <div className="card mt-6 overflow-hidden p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Edge sketch</h3>
          <img src={imageUrl(sketchPath)} alt="Sketch" className="max-h-72 rounded-xl border border-slate-200" />
        </div>
      )}

      {analysis?.house_description && (
        <div className="mt-6 rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-50 to-white p-5">
          <h4 className="flex items-center gap-2 font-semibold text-brand-900">
            <span className="grid h-6 w-6 place-items-center rounded-md bg-brand-600 text-xs text-white">AI</span>
            House analysis
          </h4>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">{analysis.house_description}</p>
        </div>
      )}

      {canProceed && (
        <div className="mt-8 flex justify-end">
          <button
            onClick={() => onComplete({ projectId, suggestions: result?.suggestions, analysis })}
            className="btn-success"
          >
            Continue to Zones ({zoneCount})
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
