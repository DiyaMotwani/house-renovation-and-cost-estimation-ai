// Presentational UI kit — no business logic, pure styling/markup helpers.

export function Spinner({ className = 'h-4 w-4' }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  );
}

const ALERT_STYLES = {
  error: { box: 'bg-rose-50 border-rose-200 text-rose-800', icon: 'text-rose-500' },
  warning: { box: 'bg-amber-50 border-amber-200 text-amber-900', icon: 'text-amber-500' },
  info: { box: 'bg-brand-50 border-brand-200 text-brand-800', icon: 'text-brand-500' },
  success: { box: 'bg-emerald-50 border-emerald-200 text-emerald-800', icon: 'text-emerald-500' },
};

export function Alert({ variant = 'error', title, children, className = '' }) {
  const s = ALERT_STYLES[variant] || ALERT_STYLES.error;
  return (
    <div className={`flex gap-3 rounded-xl border p-4 ${s.box} ${className}`}>
      <svg className={`h-5 w-5 shrink-0 mt-0.5 ${s.icon}`} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path
          fillRule="evenodd"
          d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zM12 8a1 1 0 011 1v4a1 1 0 11-2 0V9a1 1 0 011-1zm0 8.5a1.125 1.125 0 100-2.25 1.125 1.125 0 000 2.25z"
          clipRule="evenodd"
        />
      </svg>
      <div className="text-sm leading-relaxed">
        {title && <p className="font-semibold mb-0.5">{title}</p>}
        <div>{children}</div>
      </div>
    </div>
  );
}

export function StepHeader({ index, total, title, subtitle }) {
  return (
    <div className="mb-8">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand-600 mb-2">
        Step {index} of {total}
      </p>
      <h2 className="font-display text-3xl font-bold text-slate-900 tracking-tight">{title}</h2>
      {subtitle && <p className="mt-2 text-slate-500 max-w-2xl">{subtitle}</p>}
    </div>
  );
}

export function SectionTitle({ children, className = '' }) {
  return <h3 className={`font-semibold text-slate-800 ${className}`}>{children}</h3>;
}

// Step icons (stroke SVGs)
const iconProps = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  viewBox: '0 0 24 24',
};

export const Icons = {
  upload: (p) => (
    <svg {...iconProps} {...p}>
      <path d="M12 16V4m0 0L8 8m4-4l4 4" />
      <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
    </svg>
  ),
  zones: (p) => (
    <svg {...iconProps} {...p}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  ),
  generate: (p) => (
    <svg {...iconProps} {...p}>
      <path d="M5 3v4M3 5h4M6 17v4M4 19h4" />
      <path d="M13 3l2.5 6.5L22 12l-6.5 2.5L13 21l-2.5-6.5L4 12l6.5-2.5L13 3z" />
    </svg>
  ),
  estimate: (p) => (
    <svg {...iconProps} {...p}>
      <rect x="5" y="3" width="14" height="18" rx="2" />
      <path d="M9 7h6M9 11h6M9 15h3" />
    </svg>
  ),
  report: (p) => (
    <svg {...iconProps} {...p}>
      <path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" />
      <path d="M14 3v5h5M9 13h6M9 17h6" />
    </svg>
  ),
  check: (p) => (
    <svg {...iconProps} {...p}>
      <path d="M20 6L9 17l-5-5" />
    </svg>
  ),
};
