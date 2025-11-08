import React from 'react';
import { ArrowLeft, CheckCircle2, XCircle, Clock, GitBranch, TrendingUp } from 'lucide-react';
import { ConstellationSummary } from '../../store/galaxyStore';

interface ConstellationStatsProps {
  constellation: ConstellationSummary;
  onBack: () => void;
}

const ConstellationStats: React.FC<ConstellationStatsProps> = ({ constellation, onBack }) => {
  // Get statistics from metadata (sent from backend via get_statistics())
  const stats = constellation.metadata?.statistics || {};
  const statusCounts = stats.task_status_counts || {};
  
  const totalTasks = stats.total_tasks || constellation.statistics.total;
  const totalDependencies = stats.total_dependencies || 0;
  const completedTasks = statusCounts.completed || 0;
  const failedTasks = statusCounts.failed || 0;
  const runningTasks = statusCounts.running || 0;
  const pendingTasks = statusCounts.pending || 0;
  const readyTasks = statusCounts.ready || 0;

  // Calculate success rate
  const terminalTasks = completedTasks + failedTasks;
  const successRate = terminalTasks > 0 ? (completedTasks / terminalTasks) * 100 : 0;

  // Get execution duration from stats
  const executionDuration = stats.execution_duration;
  const executionTime = executionDuration != null
    ? `${executionDuration.toFixed(2)}s`
    : 'N/A';

  // Get parallelism metrics
  const criticalPathLength = stats.critical_path_length;
  const totalWork = stats.total_work;
  const parallelismRatio = stats.parallelism_ratio;

  // Format timestamps
  const formatTime = (isoString?: string) => {
    if (!isoString) return 'N/A';
    try {
      const date = new Date(isoString);
      return new Intl.DateTimeFormat('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      }).format(date);
    } catch {
      return 'N/A';
    }
  };

  const createdAt = formatTime(stats.created_at);
  const startedAt = formatTime(stats.execution_start_time);
  const endedAt = formatTime(stats.execution_end_time);

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-1">
      {/* Header with back button */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="flex items-center gap-2 rounded-full border border-white/10 bg-black/30 px-3 py-2 text-xs text-slate-200 transition hover:border-white/30 hover:bg-black/40"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Back to DAG
        </button>
        <div className="text-sm font-semibold text-white">Execution Summary</div>
      </div>

      {/* Success Rate Card */}
      <div className="rounded-2xl border border-emerald-400/30 bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Success Rate</div>
            <div className="mt-1 text-3xl font-bold text-emerald-300">
              {terminalTasks > 0 ? `${successRate.toFixed(1)}%` : 'N/A'}
            </div>
            <div className="mt-1 text-xs text-slate-400">
              {completedTasks} of {terminalTasks} completed tasks
            </div>
          </div>
          <TrendingUp className="h-10 w-10 text-emerald-400/40" aria-hidden />
        </div>
      </div>

      {/* Task Overview - Total/Pending/Running/Done */}
      <div className="grid grid-cols-4 gap-2 text-center">
        <div className="rounded-xl border border-white/10 bg-white/5 px-2 py-2">
          <div className="text-[9px] uppercase tracking-[0.2em] text-slate-400">Total</div>
          <div className="mt-0.5 text-lg font-bold text-white">{totalTasks}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 px-2 py-2">
          <div className="text-[9px] uppercase tracking-[0.2em] text-slate-400">Pending</div>
          <div className="mt-0.5 text-lg font-bold text-slate-300">{pendingTasks}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 px-2 py-2">
          <div className="text-[9px] uppercase tracking-[0.2em] text-slate-400">Running</div>
          <div className="mt-0.5 text-lg font-bold text-cyan-300">{runningTasks}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 px-2 py-2">
          <div className="text-[9px] uppercase tracking-[0.2em] text-slate-400">Done</div>
          <div className="mt-0.5 text-lg font-bold text-emerald-300">{completedTasks}</div>
        </div>
      </div>

      {/* Task Statistics Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
            Completed
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-300">{completedTasks}</div>
          <div className="mt-1 text-xs text-slate-500">
            {totalTasks > 0 ? `${((completedTasks / totalTasks) * 100).toFixed(0)}%` : '0%'} of total
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">
            <XCircle className="h-3.5 w-3.5" aria-hidden />
            Failed
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-300">{failedTasks}</div>
          <div className="mt-1 text-xs text-slate-500">
            {totalTasks > 0 ? `${((failedTasks / totalTasks) * 100).toFixed(0)}%` : '0%'} of total
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">
            <Clock className="h-3.5 w-3.5" aria-hidden />
            Running
          </div>
          <div className="mt-2 text-2xl font-bold text-cyan-300">{runningTasks}</div>
          <div className="mt-1 text-xs text-slate-500">Active execution</div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">
            <GitBranch className="h-3.5 w-3.5" aria-hidden />
            Pending
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-300">{pendingTasks}</div>
          <div className="mt-1 text-xs text-slate-500">Awaiting execution</div>
        </div>
      </div>

      {/* Additional Metrics */}
      {(totalDependencies > 0 || readyTasks > 0) && (
        <div className="grid grid-cols-2 gap-3">
          {readyTasks > 0 && (
            <div className="rounded-2xl border border-yellow-400/30 bg-yellow-500/10 p-4">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Ready</div>
              <div className="mt-2 text-2xl font-bold text-yellow-300">{readyTasks}</div>
              <div className="mt-1 text-xs text-slate-500">Can be executed</div>
            </div>
          )}
          {totalDependencies > 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Dependencies</div>
              <div className="mt-2 text-2xl font-bold text-slate-300">{totalDependencies}</div>
              <div className="mt-1 text-xs text-slate-500">Total links</div>
            </div>
          )}
        </div>
      )}

      {/* Parallelism Metrics */}
      {parallelismRatio != null && (
        <div className="rounded-2xl border border-purple-400/30 bg-gradient-to-br from-purple-500/10 to-blue-500/10 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 mb-3">
            Parallelism Analysis
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-slate-400">Critical Path</div>
              <div className="mt-1 text-xl font-bold text-purple-300">
                {criticalPathLength != null ? Number(criticalPathLength).toFixed(2) : 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-400">Total Work</div>
              <div className="mt-1 text-xl font-bold text-blue-300">
                {totalWork != null ? Number(totalWork).toFixed(2) : 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-400">Ratio</div>
              <div className="mt-1 text-xl font-bold text-cyan-300">
                {parallelismRatio ? `${parallelismRatio.toFixed(2)}x` : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Timing Information */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 mb-3">
          Execution Timeline
        </div>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-slate-400">Created:</span>
            <span className="font-mono text-slate-200">{createdAt}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Started:</span>
            <span className="font-mono text-slate-200">{startedAt}</span>
          </div>
          {constellation.status === 'completed' && (
            <div className="flex justify-between">
              <span className="text-slate-400">Ended:</span>
              <span className="font-mono text-slate-200">{endedAt}</span>
            </div>
          )}
          <div className="flex justify-between border-t border-white/10 pt-2 mt-2">
            <span className="text-slate-400 font-semibold">Duration:</span>
            <span className="font-mono text-emerald-300 font-semibold">{executionTime}</span>
          </div>
        </div>
      </div>

      {/* Additional Metadata */}
      {constellation.metadata && Object.keys(constellation.metadata).length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 mb-3">
            Additional Information
          </div>
          <div className="space-y-2 text-xs">
            {constellation.description && (
              <div>
                <span className="text-slate-400">Description:</span>
                <div className="mt-1 text-slate-200">{constellation.description}</div>
              </div>
            )}
            {constellation.metadata.display_name && (
              <div className="flex justify-between">
                <span className="text-slate-400">Name:</span>
                <span className="text-slate-200">{constellation.metadata.display_name}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConstellationStats;
