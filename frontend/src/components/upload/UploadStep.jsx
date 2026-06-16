import { useCallback, useEffect, useState } from 'react';
import { api, imageUrl } from '../../services/api';
import { useTaskPoller } from '../../hooks/useTaskPoller';

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
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Step 1 — Upload House Photo</h2>
      <p className="text-slate-600 mb-6">Upload a clear exterior photo of your house (JPG or PNG).</p>

      <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded-xl shadow-sm border">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Project name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border rounded-lg px-3 py-2"
            placeholder="My Home Renovation"
            disabled={!!projectId}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">House photo</label>
          <input
            type="file"
            accept="image/jpeg,image/png"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full"
          />
        </div>
        <button
          type="submit"
          disabled={submitting || isProcessing}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? 'Uploading...' : isProcessing ? 'Validating...' : 'Upload & Validate'}
        </button>
      </form>

      {(error || pollError || validationFailed) && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error || pollError || result?.validation?.reason || 'Validation failed. Please upload a clearer exterior photo.'}
        </div>
      )}

      {taskId && status && (
        <p className="mt-4 text-sm text-slate-500">
          Task status: {status}
          {isProcessing && ' — detecting zones (this may take 30–60 seconds)'}
        </p>
      )}

      {status === 'completed' && !validationFailed && zoneCount > 0 && (
        <p className="mt-2 text-sm text-green-700">
          {zoneCount} zone{zoneCount !== 1 ? 's' : ''} detected successfully.
        </p>
      )}

      {status === 'completed' && !validationFailed && zoneCount === 0 && (
        <p className="mt-2 text-sm text-amber-700">
          Processing finished but no zones were detected. Try uploading a clearer exterior photo.
        </p>
      )}

      {sketchPath && (
        <div className="mt-6">
          <h3 className="font-semibold mb-2">Edge sketch</h3>
          <img src={imageUrl(sketchPath)} alt="Sketch" className="rounded-lg border max-h-64" />
        </div>
      )}

      {analysis?.house_description && (
        <div className="mt-4 p-4 rounded-lg bg-indigo-50 border border-indigo-200">
          <h4 className="font-semibold text-indigo-900">House analysis</h4>
          <p className="text-sm text-indigo-900 mt-1">{analysis.house_description}</p>
        </div>
      )}

      {canProceed && (
        <button
          onClick={() => onComplete({ projectId, suggestions: result?.suggestions, analysis })}
          className="mt-6 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
        >
          Proceed to Zones ({zoneCount})
        </button>
      )}
    </div>
  );
}
