import { useEffect, useState } from 'react';
import { api } from '../../services/api';

export default function EstimationStep({ projectId, onComplete }) {
  const [summary, setSummary] = useState(null);
  const [zones, setZones] = useState([]);
  const [overrides, setOverrides] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadEstimation = async (overrideList = null) => {
    const res = overrideList?.length
      ? await api.recalculateEstimation(projectId, overrideList)
      : await api.runEstimation(projectId);
    if (!res.success) throw new Error(res.msg);
    setSummary(res.data);
  };

  useEffect(() => {
    const init = async () => {
      try {
        const zonesRes = await api.getZones(projectId);
        setZones(zonesRes.data || []);
        await loadEstimation();
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [projectId]);

  const zoneLabel = (zoneId) => zones.find((z) => z.id === zoneId)?.label || zoneId;

  const handleOverrideChange = async (zoneId, field, value) => {
    const key = field === 'unit' ? 'custom_unit_price_inr' : 'custom_labour_rate_inr';
    const updated = {
      ...overrides,
      [zoneId]: { ...overrides[zoneId], zone_id: zoneId, [key]: parseFloat(value) || 0 },
    };
    setOverrides(updated);
    try {
      const list = Object.values(updated).filter((o) => o.zone_id);
      await loadEstimation(list);
    } catch (e) {
      setError(e.message);
    }
  };

  if (loading) return <p className="text-slate-600">Calculating costs...</p>;

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Step 4 — Cost Estimation</h2>
      <p className="text-slate-600 mb-6">Review and adjust material and labour rates.</p>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {summary && (
        <>
          <div className="overflow-x-auto bg-white rounded-xl border shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left p-3">Zone</th>
                  <th className="text-left p-3">Qty</th>
                  <th className="text-right p-3">Material (INR)</th>
                  <th className="text-right p-3">Labour (INR)</th>
                  <th className="text-right p-3">Total (INR)</th>
                  <th className="text-left p-3">Dimension logic</th>
                  <th className="text-right p-3">Unit Price</th>
                  <th className="text-right p-3">Labour/sqft</th>
                </tr>
              </thead>
              <tbody>
                {summary.items.map((item) => (
                  <tr key={item.id} className="border-t">
                    <td className="p-3">{zoneLabel(item.zone_id)}</td>
                    <td className="p-3">{item.qty_required.toFixed(1)} {item.unit}</td>
                    <td className="p-3 text-right">{item.material_cost_inr.toLocaleString()}</td>
                    <td className="p-3 text-right">{item.labour_cost_inr.toLocaleString()}</td>
                    <td className="p-3 text-right font-medium">{item.total_cost_inr.toLocaleString()}</td>
                    <td className="p-3 text-xs">
                      <div>{item.dimension_anchor_used || 'n/a'}</div>
                      <div className="text-slate-500">{item.dimension_reasoning || ''}</div>
                    </td>
                    <td className="p-3">
                      <input
                        type="number"
                        className="border rounded px-2 py-1 w-24 text-right"
                        placeholder="override"
                        onChange={(e) => handleOverrideChange(item.zone_id, 'unit', e.target.value)}
                      />
                    </td>
                    <td className="p-3">
                      <input
                        type="number"
                        className="border rounded px-2 py-1 w-24 text-right"
                        placeholder="override"
                        onChange={(e) => handleOverrideChange(item.zone_id, 'labour', e.target.value)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex gap-8 text-lg font-semibold">
            <span>Grand Total: INR {summary.grand_total_inr.toLocaleString()}</span>
            <span>Duration: {summary.total_days.toFixed(1)} days</span>
          </div>

          <button
            onClick={onComplete}
            className="mt-6 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
          >
            Proceed to Report
          </button>
        </>
      )}
    </div>
  );
}
