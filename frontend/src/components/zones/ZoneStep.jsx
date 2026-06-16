import { useCallback, useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Alert, Spinner, StepHeader } from '../ui/kit';

export default function ZoneStep({ projectId, suggestions, analysis, onComplete }) {
  const [zones, setZones] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [selections, setSelections] = useState({});
  const [sqftOverrides, setSqftOverrides] = useState({});
  const [frontWidth, setFrontWidth] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const loadZones = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [zonesRes, catalogRes] = await Promise.all([
        api.getZones(projectId),
        api.getCatalog(),
      ]);
      const zoneList = zonesRes.data || [];
      const mats = catalogRes.data || [];
      setZones(zoneList);
      setMaterials(mats);

      const suggestionMap = {};
      (suggestions?.suggestions || []).forEach((s) => {
        if (s.recommended_material_ids?.[0]) {
          suggestionMap[s.zone_key] = s.recommended_material_ids[0];
        }
      });

      const initial = {};
      const sqftInit = {};
      zoneList.forEach((z) => {
        initial[z.id] = suggestionMap[z.zone_key] || mats[0]?.id || '';
        sqftInit[z.id] = z.estimated_sqft ?? '';
      });
      setSelections(initial);
      setSqftOverrides(sqftInit);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [projectId, suggestions]);

  useEffect(() => {
    loadZones();
  }, [loadZones]);

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      for (const zone of zones) {
        const sqft = parseFloat(sqftOverrides[zone.id]);
        if (!isNaN(sqft) && sqft !== zone.estimated_sqft) {
          await api.updateZone(projectId, zone.id, sqft);
        }
      }
      if (frontWidth) {
        await api.setScaleAnchor(projectId, parseFloat(frontWidth));
      }
      const assignments = zones.map((z) => ({
        zone_id: z.id,
        material_id: selections[z.id],
      }));
      await api.assignMaterials(projectId, assignments);
      onComplete();
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 text-slate-500">
        <Spinner className="h-5 w-5 text-brand-600" />
        Loading detected zones…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <StepHeader
        index={2}
        total={5}
        title="Zones & materials"
        subtitle="Review the surfaces our AI detected, fine-tune areas if needed, and assign a finishing material to each zone."
      />

      <div className="mb-6 flex flex-wrap gap-3">
        {suggestions?.overall_style && (
          <span className="pill bg-brand-50 text-brand-700">
            <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="currentColor"><path d="M12 2l2.4 6.9L21 9.2l-5.4 4 2 6.8L12 16.6 6.4 20l2-6.8L3 9.2l6.6-.3z" /></svg>
            Suggested style: {suggestions.overall_style}
          </span>
        )}
      </div>

      {analysis?.renovation_needs?.length > 0 && (
        <div className="mb-6 rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-50 to-white p-5">
          <p className="mb-2 flex items-center gap-2 font-semibold text-brand-900">
            <span className="grid h-6 w-6 place-items-center rounded-md bg-brand-600 text-xs text-white">AI</span>
            Detected renovation needs
          </p>
          <ul className="grid gap-1.5 sm:grid-cols-2">
            {analysis.renovation_needs.slice(0, 4).map((need) => (
              <li key={need} className="flex items-start gap-2 text-sm text-slate-700">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-400" />
                {need}
              </li>
            ))}
          </ul>
        </div>
      )}

      {zones.length === 0 && (
        <Alert variant="warning" className="mb-6" title="No zones found for this project">
          <p>Go back and re-upload a clear house exterior photo, or retry loading.</p>
          <button type="button" onClick={loadZones} className="btn-secondary mt-3 py-1.5">
            Retry
          </button>
        </Alert>
      )}

      <div className="card mb-6 flex flex-wrap items-end gap-4 p-5">
        <div>
          <label className="label">Actual front width (ft)</label>
          <input
            type="number"
            value={frontWidth}
            onChange={(e) => setFrontWidth(e.target.value)}
            className="input w-40"
            placeholder="e.g. 30"
          />
        </div>
        <p className="pb-3 text-xs text-slate-500">
          Optional — improves area accuracy by calibrating scale to a real-world measurement.
        </p>
      </div>

      <div className="space-y-4">
        {zones.map((zone) => {
          const reason = (suggestions?.suggestions || []).find((s) => s.zone_key === zone.zone_key)?.reason;
          return (
            <div key={zone.id} className="card p-5 transition hover:shadow-card-hover">
              <div className="flex flex-wrap items-end gap-4">
                <div className="min-w-[200px] flex-1">
                  <h3 className="font-semibold text-slate-800">{zone.label}</h3>
                  {zone.description && <p className="mt-0.5 text-sm text-slate-500">{zone.description}</p>}
                  {reason && (
                    <p className="mt-2 inline-flex items-start gap-1.5 rounded-lg bg-brand-50 px-2.5 py-1 text-xs text-brand-700">
                      <svg viewBox="0 0 24 24" className="mt-0.5 h-3 w-3 shrink-0" fill="currentColor"><path d="M12 2l2.4 6.9L21 9.2l-5.4 4 2 6.8L12 16.6 6.4 20l2-6.8L3 9.2l6.6-.3z" /></svg>
                      {reason}
                    </p>
                  )}
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-500">Area (sq ft)</label>
                  <input
                    type="number"
                    value={sqftOverrides[zone.id] ?? ''}
                    onChange={(e) => setSqftOverrides((p) => ({ ...p, [zone.id]: e.target.value }))}
                    className="input w-28 py-2"
                  />
                </div>
                <div className="min-w-[220px]">
                  <label className="mb-1 block text-xs font-medium text-slate-500">Material</label>
                  <select
                    value={selections[zone.id] || ''}
                    onChange={(e) => setSelections((p) => ({ ...p, [zone.id]: e.target.value }))}
                    className="input py-2"
                  >
                    {materials.map((m) => (
                      <option key={m.id} value={m.id}>{m.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {error && <Alert variant="error" className="mt-5">{error}</Alert>}

      <div className="mt-8 flex justify-end">
        <button onClick={handleSubmit} disabled={submitting || zones.length === 0} className="btn-primary">
          {submitting && <Spinner />}
          {submitting ? 'Saving…' : 'Save & Generate Preview'}
          {!submitting && (
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
