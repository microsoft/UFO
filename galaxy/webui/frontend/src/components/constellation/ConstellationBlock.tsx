import React, { useState } from 'react';
import { ShieldAlert, Timer, BarChart3 } from 'lucide-react';
import clsx from 'clsx';
import DagPreview from './DagPreview';
import ConstellationStats from './ConstellationStats';
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
  const [showStats, setShowStats] = useState(false);

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

  // Show stats button only when constellation is completed or failed
  const canShowStats = constellation.status === 'completed' || constellation.status === 'failed';

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
        <div className="flex items-center gap-2">
          {canShowStats && (
            <button
              onClick={() => setShowStats(!showStats)}
              className={clsx(
                'flex items-center gap-2 rounded-full border border-white/10 px-3 py-1.5 text-xs transition',
                showStats 
                  ? 'bg-emerald-500/20 border-emerald-400/40 text-emerald-300' 
                  : 'bg-black/30 text-slate-300 hover:border-white/30 hover:bg-black/40'
              )}
              title="View execution summary"
            >
              <BarChart3 className="h-3.5 w-3.5" aria-hidden />
              Stats
            </button>
          )}
          <div className="flex flex-col items-end text-xs text-slate-400">
            <div className="flex items-center gap-1">
              <Timer className="h-3 w-3" aria-hidden />
              Updated {constellation.updatedAt ? new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit' }).format(constellation.updatedAt) : 'recently'}
            </div>
            <div>{constellation.taskIds.length} tasks</div>
          </div>
        </div>
      </div>

      <div className={previewClasses}>
        {showStats ? (
          <ConstellationStats 
            constellation={constellation} 
            onBack={() => setShowStats(false)} 
          />
        ) : (
          <DagPreview
            nodes={constellation.dag.nodes}
            edges={constellation.dag.edges}
            onSelectNode={onSelectTask}
          />
        )}
      </div>
    </div>
  );
};

export default ConstellationBlock;
