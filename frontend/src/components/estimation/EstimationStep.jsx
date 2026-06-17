import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../../services/api';
import { Alert, Spinner, StepHeader } from '../ui/kit';
import VariantBar from '../variants/VariantBar';

const inr = (n) => '₹' + Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
// Whole number for countable items (tiles), one decimal for litres/sqft/rft.
const qty = (n) => (Number.isInteger(n) ? n.toString() : Number(n).toFixed(1));

// How this zone's surface area (dimension) was derived — kept transparent/advisory.
const basisLabel = (anchor) => {
  if (!anchor) return null;
  if (anchor === 'user_measurement') return 'measured';
  if (anchor.startsWith('reference:')) return `ref: ${anchor.split(':')[1]}`;
  if (anchor === 'vision_estimate') return 'AI visual estimate';
  if (anchor === 'architectural_prior') return 'typical proportions';
  return anchor;
};

// "Coverage" line (req 5.6) — only meaningful when a unit covers more than 1 sqft.
const coverageLabel = (item) => {
  const parts = [];
  if (item.coverage_sqft_per_unit && item.coverage_sqft_per_unit !== 1) {
    const u = item.unit ? item.unit.replace(/s$/, '') : 'unit';
    parts.push(`${item.coverage_sqft_per_unit} sqft / ${u}`);
  }
  if (item.coats_required && item.coats_required > 1) parts.push(`${item.coats_required} coats`);
  if (item.wastage_pct != null) parts.push(`${item.wastage_pct}% wastage`);
  return parts.join(' · ');
};

// An edited rate counts as an override only when it is a positive number that
// actually differs from the catalog rate; blank or "same as default" clears it.
const toCustom = (raw, base) => {
  const s = (raw ?? '').toString().trim();
  if (s === '') return null;
  const n = Number(s);
  if (!Number.isFinite(n) || n <= 0) return null;
  return n === base ? null : n;
};

export default function EstimationStep({ projectId, onComplete }) {
  const [summary, setSummary] = useState(null);
  const [rateInputs, setRateInputs] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);

  const initialized = useRef(false);
  const debounceRef = useRef(null);
  const reqIdRef = useRef(0);
  // Always-current copy of the edited rates, so blur/debounce never act on a
  // stale closure value (which previously dropped the user's latest keystroke).
  const rateInputsRef = useRef({});

  const applySummary = (data) => {
    setSummary(data);
    // Seed the editable fields from the effective rates only once, so a
    // recalculation response never overwrites what the user is typing.
    if (!initialized.current) {
      const seed = {};
      for (const it of data.items) {
        seed[it.zone_id] = {
          unit: String(it.applied_unit_price_inr ?? it.base_unit_price_inr ?? ''),
          labour: String(it.applied_labour_rate_inr ?? it.base_labour_rate_inr ?? ''),
        };
      }
      setRateInputs(seed);
      rateInputsRef.current = seed;
      initialized.current = true;
    }
  };

  const init = useCallback(async () => {
    setLoading(true);
    try {
      // Load a previously saved estimate (keeps any rate overrides) if one
      // exists; otherwise run a fresh calculation for the active variant.
      let res;
      try {
        res = await api.getEstimation(projectId);
      } catch {
        res = await api.runEstimation(projectId);
      }
      if (!res.success) throw new Error(res.msg);
      applySummary(res.data);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    init();
    return () => clearTimeout(debounceRef.current);
  }, [init]);

  // Switching the active design reloads its own materials, overrides and totals.
  const onVariantChanged = () => {
    initialized.current = false;
    setSummary(null);
    setRateInputs({});
    init();
  };

  const recalculate = async (inputs) => {
    const items = summary?.items || [];
    const overrides = items.map((it) => ({
      zone_id: it.zone_id,
      custom_unit_price_inr: toCustom(inputs[it.zone_id]?.unit, it.base_unit_price_inr),
      custom_labour_rate_inr: toCustom(inputs[it.zone_id]?.labour, it.base_labour_rate_inr),
    }));
    const reqId = ++reqIdRef.current;
    setRecalculating(true);
    try {
      const res = await api.recalculateEstimation(projectId, overrides);
      if (!res.success) throw new Error(res.msg);
      // Ignore stale responses from earlier keystrokes.
      if (reqId === reqIdRef.current) {
        setSummary(res.data);
        setError(null);
      }
    } catch (e) {
      if (reqId === reqIdRef.current) setError(e.message);
    } finally {
      if (reqId === reqIdRef.current) setRecalculating(false);
    }
  };

  const handleRateChange = (zoneId, field, value) => {
    const updated = {
      ...rateInputsRef.current,
      [zoneId]: { ...rateInputsRef.current[zoneId], [field]: value },
    };
    rateInputsRef.current = updated;
    setRateInputs(updated);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => recalculate(updated), 600);
  };

  const handleRateBlur = () => {
    clearTimeout(debounceRef.current);
    recalculate(rateInputsRef.current);
  };

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex items-start justify-between gap-4">
        <StepHeader
          index={4}
          total={5}
          title="Cost estimation"
          subtitle="An indicative Bill of Quantities for the active design — one line per detected zone, showing its surface area, material, quantity (with coverage & wastage), material and labour cost. Edit any unit or labour rate to recalculate; clear a field to restore the standard rate."
        />
        {recalculating && (
          <span className="pill mt-1 shrink-0 bg-brand-50 text-brand-700">
            <Spinner className="h-3.5 w-3.5" />
            Recalculating…
          </span>
        )}
      </div>

      <VariantBar projectId={projectId} onChanged={onVariantChanged} showCosts />

      {error && <Alert variant="error" className="mb-4">{error}</Alert>}

      {loading && (
        <div className="flex items-center justify-center gap-3 py-20 text-slate-500">
          <Spinner className="h-5 w-5 text-brand-600" />
          Preparing your cost estimate…
        </div>
      )}

      {!loading && summary && (
        <>
          <div className="card overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="p-3.5 text-left font-semibold">Zone</th>
                    <th className="p-3.5 text-left font-semibold">Material / Coverage</th>
                    <th className="p-3.5 text-right font-semibold">Surface Area (sqft)</th>
                    <th className="p-3.5 text-right font-semibold">Quantity Required</th>
                    <th className="p-3.5 text-right font-semibold">Unit Rate (₹)</th>
                    <th className="p-3.5 text-right font-semibold">Material (₹)</th>
                    <th className="p-3.5 text-right font-semibold">Labour/sqft (₹)</th>
                    <th className="p-3.5 text-right font-semibold">Labour (₹)</th>
                    <th className="p-3.5 text-right font-semibold">Total (₹)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {summary.items.map((item) => (
                    <tr key={item.zone_id} className="align-top transition hover:bg-slate-50/60">
                      <td className="p-3.5 font-medium text-slate-800">{item.zone_label || item.zone_id}</td>
                      <td className="p-3.5">
                        <div className="text-slate-700">{item.material_name}</div>
                        {coverageLabel(item) && (
                          <div className="mt-0.5 text-xs text-slate-400">{coverageLabel(item)}</div>
                        )}
                      </td>
                      <td className="p-3.5 text-right tabular-nums text-slate-600">
                        {item.area_sqft.toLocaleString('en-IN')}
                        {basisLabel(item.dimension_anchor_used) && (
                          <div className="text-xs font-sans text-slate-400">{basisLabel(item.dimension_anchor_used)}</div>
                        )}
                      </td>
                      <td className="p-3.5 text-right tabular-nums text-slate-600">
                        {qty(item.qty_required)} {item.unit}
                      </td>
                      <td className="p-3.5 text-right">
                        <input
                          type="number"
                          min="0"
                          value={rateInputs[item.zone_id]?.unit ?? ''}
                          onChange={(e) => handleRateChange(item.zone_id, 'unit', e.target.value)}
                          onBlur={handleRateBlur}
                          className={`w-24 rounded-lg border px-2.5 py-1.5 text-right tabular-nums shadow-sm transition focus:outline-none focus:ring-4 focus:ring-brand-500/15 ${
                            item.unit_price_overridden ? 'border-accent-400 bg-accent-50' : 'border-slate-300 focus:border-brand-500'
                          }`}
                        />
                        {item.unit_price_overridden && (
                          <div className="mt-0.5 text-xs text-accent-600">was {inr(item.base_unit_price_inr)}</div>
                        )}
                      </td>
                      <td className="p-3.5 text-right tabular-nums text-slate-700">{inr(item.material_cost_inr)}</td>
                      <td className="p-3.5 text-right">
                        <input
                          type="number"
                          min="0"
                          value={rateInputs[item.zone_id]?.labour ?? ''}
                          onChange={(e) => handleRateChange(item.zone_id, 'labour', e.target.value)}
                          onBlur={handleRateBlur}
                          className={`w-24 rounded-lg border px-2.5 py-1.5 text-right tabular-nums shadow-sm transition focus:outline-none focus:ring-4 focus:ring-brand-500/15 ${
                            item.labour_overridden ? 'border-accent-400 bg-accent-50' : 'border-slate-300 focus:border-brand-500'
                          }`}
                        />
                        {item.labour_overridden && (
                          <div className="mt-0.5 text-xs text-accent-600">was {inr(item.base_labour_rate_inr)}</div>
                        )}
                      </td>
                      <td className="p-3.5 text-right tabular-nums text-slate-700">{inr(item.labour_cost_inr)}</td>
                      <td className="p-3.5 text-right font-semibold tabular-nums text-slate-900">{inr(item.total_cost_inr)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <div className="card w-full max-w-sm p-5 text-sm">
              <Row label="Material subtotal" value={inr(summary.material_subtotal_inr)} />
              <Row label="Labour subtotal" value={inr(summary.labour_subtotal_inr)} />
              {summary.gst_pct > 0 && (
                <Row label={`GST @ ${summary.gst_pct}%`} value={inr(summary.gst_amount_inr)} />
              )}
              <div className="my-3 border-t border-dashed border-slate-200" />
              <div className="flex items-center justify-between rounded-xl bg-brand-50 px-3 py-2.5">
                <span className="font-semibold text-brand-900">Grand Total (incl. GST)</span>
                <span className="font-display text-xl font-bold text-brand-700">
                  {inr(summary.gst_pct > 0 ? summary.total_payable_inr : summary.grand_total_inr)}
                </span>
              </div>
            </div>
          </div>

          <p className="mt-2 text-right text-xs text-slate-400">
            Indicative estimate — advisory only, not a binding quotation.
          </p>

          <div className="mt-8 flex justify-end">
            <button onClick={onComplete} className="btn-success">
              Proceed to Report
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function Row({ label, value, bold }) {
  return (
    <div className={`flex justify-between py-1 ${bold ? 'font-semibold text-slate-800' : 'text-slate-600'}`}>
      <span>{label}</span>
      <span className="tabular-nums">{value}</span>
    </div>
  );
}
