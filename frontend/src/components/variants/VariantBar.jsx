import { useCallback, useEffect, useState } from 'react';
import { api, imageUrl } from '../../services/api';
import { Spinner } from '../ui/kit';

const inr = (n) =>
  n == null ? '—' : '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 });

export default function VariantBar({ projectId, onChanged }) {
  const [variants, setVariants] = useState([]);
  const [busy, setBusy] = useState(false);
  const [compare, setCompare] = useState(null); // null | [] (loading) | items
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const res = await api.listVariants(projectId);
      setVariants(res.data || []);
    } catch (e) {
      setError(e.message);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const act = async (fn) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await load();
      onChanged?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const activate = (v) => !v.is_active && act(() => api.activateVariant(projectId, v.id));
  const addVariant = () => act(() => api.createVariant(projectId, null));
  const rename = (v) => {
    const name = window.prompt('Rename design', v.name);
    if (name && name.trim()) act(() => api.renameVariant(projectId, v.id, name.trim()));
  };
  const remove = (v) => {
    if (window.confirm(`Delete "${v.name}"? Its materials, preview and estimate will be removed.`)) {
      act(() => api.deleteVariant(projectId, v.id));
    }
  };

  const openCompare = async () => {
    setCompare([]);
    try {
      const res = await api.compareVariants(projectId);
      setCompare(res.data || []);
    } catch (e) {
      setError(e.message);
      setCompare(null);
    }
  };

  return (
    <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-3 shadow-card">
      <div className="flex flex-wrap items-center gap-2">
        <span className="mr-1 text-xs font-bold uppercase tracking-wide text-slate-400">Designs</span>
        {variants.map((v) => (
          <div
            key={v.id}
            className={`group flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition ${
              v.is_active
                ? 'border-brand-600 bg-brand-600 text-white shadow-soft'
                : 'border-slate-300 bg-white text-slate-600 hover:border-brand-400'
            }`}
          >
            <button onClick={() => activate(v)} disabled={busy} className="font-medium">
              {v.name}
            </button>
            <button
              onClick={() => rename(v)}
              title="Rename"
              className={`opacity-60 hover:opacity-100 ${v.is_active ? 'text-white' : 'text-slate-400'}`}
            >
              <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z" /></svg>
            </button>
            {variants.length > 1 && (
              <button
                onClick={() => remove(v)}
                title="Delete design"
                className={`opacity-60 hover:opacity-100 ${v.is_active ? 'text-white' : 'text-slate-400'}`}
              >
                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
              </button>
            )}
          </div>
        ))}
        <button onClick={addVariant} disabled={busy} className="btn-secondary px-3 py-1.5 text-sm">
          {busy ? <Spinner className="h-3.5 w-3.5" /> : '+'} New design
        </button>
        {variants.length > 1 && (
          <button onClick={openCompare} className="btn-secondary px-3 py-1.5 text-sm">
            Compare
          </button>
        )}
      </div>
      {error && <p className="mt-2 text-xs text-rose-600">{error}</p>}

      {compare !== null && (
        <CompareModal items={compare} onClose={() => setCompare(null)} inr={inr} />
      )}
    </div>
  );
}

function CompareModal({ items, onClose, inr }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" onClick={onClose}>
      <div
        className="max-h-[85vh] w-full max-w-5xl overflow-auto rounded-2xl bg-white p-6 shadow-card-hover"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-display text-xl font-bold text-slate-900">Compare designs</h3>
          <button onClick={onClose} className="btn-secondary px-3 py-1.5 text-sm">Close</button>
        </div>
        {items.length === 0 ? (
          <p className="py-10 text-center text-slate-500">Building comparison…</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((it) => (
              <div key={it.variant.id} className="overflow-hidden rounded-xl border border-slate-200">
                <div className="flex items-center justify-between bg-slate-50 px-3 py-2">
                  <span className="font-semibold text-slate-800">{it.variant.name}</span>
                  {it.variant.is_active && <span className="pill bg-brand-100 text-brand-700">Active</span>}
                </div>
                {it.generated_image_path ? (
                  <img src={imageUrl(it.generated_image_path)} alt={it.variant.name} className="aspect-[4/3] w-full object-cover" />
                ) : (
                  <div className="flex aspect-[4/3] items-center justify-center bg-slate-100 text-xs text-slate-400">
                    No preview generated
                  </div>
                )}
                <div className="space-y-1 p-3 text-sm">
                  <Row label="Subtotal" value={inr(it.grand_total_inr)} />
                  <Row label="Total payable" value={inr(it.total_payable_inr)} bold />
                  <Row label="Duration" value={it.total_days != null ? `${it.total_days} days` : '—'} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ label, value, bold }) {
  return (
    <div className={`flex justify-between ${bold ? 'font-semibold text-slate-900' : 'text-slate-500'}`}>
      <span>{label}</span>
      <span className="tabular-nums">{value}</span>
    </div>
  );
}
