import React from 'react';
import { ShieldAlert, Timer } from 'lucide-react';
import clsx from 'clsx';
import DagPreview from './DagPreview';
import { ConstellationSummary } from '../../store/galaxyStore';

interface ConstellationBlockProps {
  constellation?: ConstellationSummary;
  onSelectTask?: (taskId: string) => void;
  variant?: 'standalone' | 'embedded';
}

const statusAccent: Record<string, string> = {
  pending: 'text-slate-300',
  running: 'text-cyan-300',
  completed: 'text-emerald-300',
  failed: 'text-rose-300',
};

const ConstellationBlock: React.FC<ConstellationBlockProps> = ({ constellation, onSelectTask, variant = 'standalone' }) => {
  if (!constellation) {
    return (
      <div
        className={clsx(
          'flex h-full flex-col items-center justify-center gap-3 rounded-3xl p-8 text-center text-sm text-slate-300',
          variant === 'standalone' ? 'glass-card' : 'border border-white/5 bg-black/30',
        )}
      >
        <ShieldAlert className="h-6 w-6" aria-hidden />
        <div>No active constellation yet.</div>
        <div className="text-xs text-slate-500">Launch a request to generate a TaskConstellation.</div>
      </div>
    );
  }

  const statusClass = statusAccent[constellation.status] || 'text-slate-300';
  const containerClasses = clsx(
    'flex h-full flex-col gap-4 rounded-3xl p-5',
    variant === 'standalone' ? 'glass-card' : 'border border-white/5 bg-black/30',
    variant === 'embedded' && 'max-h-[420px]'
  );
  const previewClasses = clsx(
    'flex-1 overflow-hidden rounded-3xl border border-white/5 bg-black/30',
    variant === 'embedded' ? 'h-[260px]' : 'h-[320px]'
  );

  return (
    <div className={containerClasses}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.25em] text-slate-400">Constellation</div>
          <div className="text-lg font-semibold text-white">
            {constellation.metadata?.display_name || constellation.description || 'Task Workflow'}
          </div>
          <div className={clsx('text-[11px] uppercase tracking-[0.2em]', statusClass)}>
            {constellation.status}
          </div>
        </div>
        <div className="flex flex-col items-end text-xs text-slate-400">
          <div className="flex items-center gap-1">
            <Timer className="h-3 w-3" aria-hidden />
            Updated {constellation.updatedAt ? new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit' }).format(constellation.updatedAt) : 'recently'}
          </div>
          <div>{constellation.taskIds.length} tasks</div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 text-center text-xs text-slate-300">
        <div className="rounded-2xl border border-white/5 bg-white/5 px-2 py-3">
          <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Total</div>
          <div className="text-base font-semibold text-white">{constellation.statistics.total}</div>
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 px-2 py-3">
          <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Pending</div>
          <div className="text-base font-semibold text-slate-200">{constellation.statistics.pending}</div>
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 px-2 py-3">
          <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Running</div>
          <div className="text-base font-semibold text-cyan-200">{constellation.statistics.running}</div>
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 px-2 py-3">
          <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Done</div>
          <div className="text-base font-semibold text-emerald-200">{constellation.statistics.completed}</div>
        </div>
      </div>

      <div className={previewClasses}>
        <DagPreview
          nodes={constellation.dag.nodes}
          edges={constellation.dag.edges}
          onSelectNode={onSelectTask}
        />
      </div>
    </div>
  );
};

export default ConstellationBlock;
