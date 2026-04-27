import React, { useState } from 'react';
import { shallow } from 'zustand/shallow';
import { DollarSign, Zap, Activity, X } from 'lucide-react';
import { useGalaxyStore, LLMCallRecord } from '../../store/galaxyStore';
import CostByModelChart from './CostByModelChart';

const formatCost = (v: number) => `$${v.toFixed(4)}`;
const formatTs = (ts: number) => {
  try {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(new Date(ts));
  } catch {
    return '—';
  }
};

interface CostAlertBannerProps {
  message: string;
  onDismiss: () => void;
}

const CostAlertBanner: React.FC<CostAlertBannerProps> = ({ message, onDismiss }) => (
  <div className="flex items-center justify-between gap-3 rounded-xl border border-amber-400/40 bg-amber-500/10 px-4 py-2.5 text-sm text-amber-200">
    <span>{message}</span>
    <button
      onClick={onDismiss}
      className="shrink-0 rounded p-0.5 text-amber-300 hover:text-white transition"
      aria-label="Dismiss alert"
    >
      <X className="h-4 w-4" />
    </button>
  </div>
);

interface RecentCallsTableProps {
  calls: LLMCallRecord[];
}

const RecentCallsTable: React.FC<RecentCallsTableProps> = ({ calls }) => {
  const recent = [...calls].reverse().slice(0, 50);

  if (recent.length === 0) {
    return (
      <div className="py-6 text-center text-xs text-slate-500">
        No LLM calls recorded yet.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/10 text-[10px] uppercase tracking-[0.2em] text-slate-400">
            <th className="pb-2 text-left">Time</th>
            <th className="pb-2 text-left">Agent</th>
            <th className="pb-2 text-left">Model</th>
            <th className="pb-2 text-right">In</th>
            <th className="pb-2 text-right">Out</th>
            <th className="pb-2 text-right">Cost</th>
            <th className="pb-2 text-right">ms</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {recent.map((call, i) => (
            <tr key={i} className="text-slate-300 hover:bg-white/5 transition">
              <td className="py-1.5 font-mono text-slate-400">{formatTs(call.timestamp)}</td>
              <td className="py-1.5 max-w-[80px] truncate" title={call.agent_type}>
                {call.agent_type}
              </td>
              <td className="py-1.5 max-w-[120px] truncate pr-2" title={call.model}>
                {call.model}
              </td>
              <td className="py-1.5 text-right font-mono">{call.prompt_tokens.toLocaleString()}</td>
              <td className="py-1.5 text-right font-mono">{call.completion_tokens.toLocaleString()}</td>
              <td className="py-1.5 text-right font-mono text-emerald-300">
                {formatCost(call.cost)}
              </td>
              <td className="py-1.5 text-right font-mono text-slate-400">
                {call.duration_ms.toFixed(0)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

/**
 * CostDashboard — shows LLM cost and token metrics accumulated during the
 * current Galaxy session.  Updates in real-time via WebSocket events handled
 * by the Zustand store (appendLLMCall / pushNotification).
 */
const CostDashboard: React.FC = () => {
  const { llmMetrics, notifications, dismissNotification } = useGalaxyStore(
    (state) => ({
      llmMetrics: state.llmMetrics,
      notifications: state.notifications,
      dismissNotification: state.dismissNotification,
    }),
    shallow,
  );

  // Surface the most recent unread cost_alert notification as a banner.
  const costAlert = notifications.find(
    (n) => !n.read && n.source === 'llm_metrics' && n.severity === 'warning',
  );

  const [showTable, setShowTable] = useState(false);

  return (
    <div className="flex flex-col gap-4 p-1">
      {/* Cost alert banner */}
      {costAlert && (
        <CostAlertBanner
          message={costAlert.title + (costAlert.description ? ` — ${costAlert.description}` : '')}
          onDismiss={() => dismissNotification(costAlert.id)}
        />
      )}

      {/* Summary row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-2xl border border-emerald-400/30 bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 p-3">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.2em] text-slate-400">
            <DollarSign className="h-3 w-3" aria-hidden />
            Total Cost
          </div>
          <div className="mt-1 text-2xl font-bold text-emerald-300">
            {formatCost(llmMetrics.totalCost)}
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.2em] text-slate-400">
            <Zap className="h-3 w-3" aria-hidden />
            Prompt Tokens
          </div>
          <div className="mt-1 text-2xl font-bold text-cyan-300">
            {llmMetrics.totalPromptTokens.toLocaleString()}
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.2em] text-slate-400">
            <Zap className="h-3 w-3" aria-hidden />
            Completion
          </div>
          <div className="mt-1 text-2xl font-bold text-purple-300">
            {llmMetrics.totalCompletionTokens.toLocaleString()}
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.2em] text-slate-400">
            <Activity className="h-3 w-3" aria-hidden />
            API Calls
          </div>
          <div className="mt-1 text-2xl font-bold text-slate-200">
            {llmMetrics.totalApiCalls}
          </div>
        </div>
      </div>

      {/* Cost by model */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <CostByModelChart
          data={llmMetrics.costByModel}
          label="Cost by Model"
          colorClass="bg-cyan-500"
        />
      </div>

      {/* Cost by agent */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <CostByModelChart
          data={llmMetrics.costByAgent}
          label="Cost by Agent"
          colorClass="bg-purple-500"
        />
      </div>

      {/* Recent calls toggle */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <button
          onClick={() => setShowTable((v) => !v)}
          className="mb-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-slate-400 hover:text-slate-200 transition"
        >
          <Activity className="h-3 w-3" aria-hidden />
          Recent Calls
          <span className="ml-auto text-slate-500">{showTable ? '▲' : '▼'}</span>
        </button>
        {showTable && (
          <RecentCallsTable calls={llmMetrics.recentCalls} />
        )}
      </div>
    </div>
  );
};

export default CostDashboard;
