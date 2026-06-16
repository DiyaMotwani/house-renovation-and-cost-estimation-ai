import { useCallback, useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Alert, Spinner, StepHeader } from '../ui/kit';
import VariantBar from '../variants/VariantBar';

export default function ZoneStep({ projectId, suggestions, analysis, onComplete }) {
  const [zones, setZones] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [selections, setSelections] = useState({});
  const [sqftOverrides, setSqftOverrides] = useState({});
  const [labels, setLabels] = useState({});
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
        if (s.recommended_material_ids?.[0]) suggestionMap[s.zone_key] = s.recommended_material_ids[0];
      });

      const initial = {};
      const sqftInit = {};
      const labelInit = {};
      zoneList.forEach((z) => {
        // Prefer the material already assigned to this design variant.
        initial[z.id] = z.material_assignment?.material_id || suggestionMap[z.zone_key] || mats[0]?.id || '';
        sqftInit[z.id] = z.estimated_sqft ?? '';
        labelInit[z.id] = z.label;
      });
      setSelections(initial);
      setSqftOverrides(sqftInit);
      setLabels(labelInit);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [projectId, suggestions]);

  useEffect(() => {
    loadZones();
  }, [loadZones]);

  const addZone = async () => {
    setError(null);
    try {
      const res = await api.createZone(projectId, { label: 'New zone', estimated_sqft: 100 });
      const z = res.data;
      // Append in place (no full reload) so the page doesn't jump to the top.
      setZones((p) => [...p, z]);
      setSelections((p) => ({ ...p, [z.id]: materials[0]?.id || '' }));
      setSqftOverrides((p) => ({ ...p, [z.id]: z.estimated_sqft ?? '' }));
      setLabels((p) => ({ ...p, [z.id]: z.label }));
    } catch (e) {
      setError(e.message);
    }
  };

  const removeZone = async (zoneId) => {
    setError(null);
    try {
      await api.deleteZone(projectId, zoneId);
      // Remove in place — keeps scroll position, no spinner flash.
      setZones((p) => p.filter((z) => z.id !== zoneId));
    } catch (e) {
      setError(e.message);
    }
  };

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      for (const zone of zones) {
        const sqft = parseFloat(sqftOverrides[zone.id]);
        const fields = {};
        if (!isNaN(sqft) && sqft !== zone.estimated_sqft) fields.estimated_sqft = sqft;
        if (labels[zone.id] && labels[zone.id] !== zone.label) fields.label = labels[zone.id];
        if (Object.keys(fields).length) await api.updateZone(projectId, zone.id, fields);
      }
      if (frontWidth) await api.setScaleAnchor(projectId, parseFloat(frontWidth));
      const assignments = zones.map((z) => ({ zone_id: z.id, material_id: selections[z.id] }));
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
        subtitle="Review the surfaces our AI detected, correct any that are off (rename, resize, add or remove), then assign a finishing material to each. Materials apply to the active design."
      />

      <VariantBar projectId={projectId} onChanged={loadZones} />

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
          <p>Re-upload a clearer photo, retry, or add a zone manually below.</p>
          <button type="button" onClick={loadZones} className="btn-secondary mt-3 py-1.5">Retry</button>
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
        <p className="pb-3 text-xs text-slate-500">Optional — calibrates area estimates to a real measurement.</p>
      </div>

      <div className="space-y-4">
        {zones.map((zone, i) => {
          const reason = (suggestions?.suggestions || []).find((s) => s.zone_key === zone.zone_key)?.reason;
          return (
            <div key={zone.id} className="card p-5 transition hover:shadow-card-hover">
              <div className="flex flex-wrap items-end gap-4">
                <div className="min-w-[200px] flex-1">
                  <div className="flex items-center gap-2">
                    <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500">{i + 1}</span>
                    <input
                      value={labels[zone.id] ?? ''}
                      onChange={(e) => setLabels((p) => ({ ...p, [zone.id]: e.target.value }))}
                      className="input py-1.5 font-semibold"
                    />
                  </div>
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
                <div className="min-w-[200px]">
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
                <button
                  type="button"
                  onClick={() => removeZone(zone.id)}
                  title="Remove zone"
                  className="mb-1 grid h-9 w-9 place-items-center rounded-lg border border-slate-200 text-slate-400 transition hover:border-rose-300 hover:text-rose-500"
                >
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" /></svg>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <button type="button" onClick={addZone} className="btn-secondary mt-4">
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
        Add zone
      </button>

      {error && <Alert variant="error" className="mt-5">{error}</Alert>}

      <div className="mt-8 flex justify-end">
        <button onClick={handleSubmit} disabled={submitting || zones.length === 0} className="btn-primary">
          {submitting && <Spinner />}
          {submitting ? 'Saving…' : 'Save & Generate Preview'}
          {!submitting && (
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
          )}
        </button>
      </div>
    </div>
  );
}
