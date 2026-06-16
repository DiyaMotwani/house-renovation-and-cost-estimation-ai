import { useCallback, useEffect, useState } from 'react';
import { api } from '../../services/api';

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

  if (loading) return <p className="text-slate-600">Loading zones...</p>;

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Step 2 — Zones & Materials</h2>
      <p className="text-slate-600 mb-6">Review detected zones and choose materials for each.</p>

      {suggestions?.overall_style && (
        <p className="mb-4 text-sm text-blue-700 bg-blue-50 px-3 py-2 rounded-lg inline-block">
          Suggested style: {suggestions.overall_style}
        </p>
      )}
      {analysis?.renovation_needs?.length > 0 && (
        <div className="mb-4 text-sm bg-indigo-50 border border-indigo-200 rounded-lg p-3">
          <p className="font-medium text-indigo-900 mb-1">Detected renovation needs</p>
          <ul className="list-disc ml-5 text-indigo-900">
            {analysis.renovation_needs.slice(0, 4).map((need) => <li key={need}>{need}</li>)}
          </ul>
        </div>
      )}

      {zones.length === 0 && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800">
          <p className="font-medium">No zones found for this project.</p>
          <p className="text-sm mt-1">Go back and re-upload a clear house exterior photo, or retry loading.</p>
          <button
            type="button"
            onClick={loadZones}
            className="mt-3 text-sm bg-amber-600 text-white px-4 py-1.5 rounded-lg hover:bg-amber-700"
          >
            Retry
          </button>
        </div>
      )}

      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Actual front width (ft) — optional scale correction
        </label>
        <input
          type="number"
          value={frontWidth}
          onChange={(e) => setFrontWidth(e.target.value)}
          className="border rounded-lg px-3 py-2 w-40"
          placeholder="e.g. 30"
        />
      </div>

      <div className="space-y-4">
        {zones.map((zone) => (
          <div key={zone.id} className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex-1 min-w-[200px]">
                <h3 className="font-semibold">{zone.label}</h3>
                <p className="text-sm text-slate-500">{zone.description}</p>
                {(suggestions?.suggestions || []).find((s) => s.zone_key === zone.zone_key)?.reason && (
                  <p className="text-xs text-indigo-700 mt-1">
                    {(suggestions.suggestions || []).find((s) => s.zone_key === zone.zone_key)?.reason}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Sq ft</label>
                <input
                  type="number"
                  value={sqftOverrides[zone.id] ?? ''}
                  onChange={(e) => setSqftOverrides((p) => ({ ...p, [zone.id]: e.target.value }))}
                  className="border rounded px-2 py-1 w-24"
                />
              </div>
              <div className="min-w-[220px]">
                <label className="block text-xs text-slate-500 mb-1">Material</label>
                <select
                  value={selections[zone.id] || ''}
                  onChange={(e) => setSelections((p) => ({ ...p, [zone.id]: e.target.value }))}
                  className="border rounded-lg px-2 py-1 w-full"
                >
                  {materials.map((m) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>

      {error && <p className="mt-4 text-red-600">{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={submitting || zones.length === 0}
        className="mt-6 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? 'Saving...' : 'Save & Generate Preview'}
      </button>
    </div>
  );
}
