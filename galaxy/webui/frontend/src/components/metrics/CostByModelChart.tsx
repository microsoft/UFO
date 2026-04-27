import React from 'react';

interface BarChartProps {
  data: Record<string, number>;
  label: string;
  colorClass?: string;
}

/**
 * Horizontal bar chart rendered with pure Tailwind CSS.
 * Used to show cost broken down by model name or agent type.
 */
const CostByModelChart: React.FC<BarChartProps> = ({
  data,
  label,
  colorClass = 'bg-cyan-500',
}) => {
  const entries = Object.entries(data).sort(([, a], [, b]) => b - a);
  const max = entries.length > 0 ? entries[0][1] : 0;

  if (entries.length === 0) {
    return (
      <div className="text-xs text-slate-500 py-2">No data yet</div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400 mb-1">{label}</div>
      {entries.map(([key, value]) => {
        const pct = max > 0 ? (value / max) * 100 : 0;
        return (
          <div key={key} className="flex items-center gap-2 text-xs">
            <div className="w-28 shrink-0 truncate text-slate-300" title={key}>{key}</div>
            <div className="flex-1 rounded-full bg-white/5 h-2 overflow-hidden">
              <div
                className={`h-full rounded-full ${colorClass} transition-all duration-500`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="w-16 text-right font-mono text-slate-300">
              ${value.toFixed(4)}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default CostByModelChart;
