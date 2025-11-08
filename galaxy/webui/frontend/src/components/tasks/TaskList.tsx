import React, { useMemo, useState } from 'react';
import clsx from 'clsx';
import { CheckCircle, XCircle, Loader2, Clock, CircleDashed } from 'lucide-react';
import { Task } from '../../store/galaxyStore';

interface TaskListProps {
  tasks: Task[];
  activeTaskId: string | null;
  onSelectTask: (taskId: string) => void;
}

/**
 * Get animated status icon for task
 */
const getStatusIcon = (status: string): React.ReactNode => {
  const normalized = status.toLowerCase();
  
  if (normalized === 'running' || normalized === 'in_progress') {
    return <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-300" aria-hidden />;
  }
  
  if (normalized === 'completed' || normalized === 'success' || normalized === 'finish') {
    return <CheckCircle className="h-3.5 w-3.5 text-emerald-300" aria-hidden />;
  }
  
  if (normalized === 'failed' || normalized === 'error') {
    return <XCircle className="h-3.5 w-3.5 text-rose-400" aria-hidden />;
  }
  
  if (normalized === 'pending' || normalized === 'waiting') {
    return <Clock className="h-3.5 w-3.5 animate-pulse text-slate-300" aria-hidden />;
  }
  
  if (normalized === 'skipped') {
    return <CircleDashed className="h-3.5 w-3.5 text-amber-300" aria-hidden />;
  }
  
  return <CircleDashed className="h-3.5 w-3.5 text-slate-300" aria-hidden />;
};

const statusFilters = ['all', 'pending', 'running', 'completed', 'failed'] as const;
const statusLabel: Record<string, string> = {
  all: 'All',
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
};

const TaskList: React.FC<TaskListProps> = ({ tasks, activeTaskId, onSelectTask }) => {
  const [filter, setFilter] = useState<(typeof statusFilters)[number]>('all');

  const filteredTasks = useMemo(() => {
    const order: Record<string, number> = {
      running: 0,
      pending: 1,
      failed: 2,
      completed: 3,
      skipped: 4,
    };

    return tasks
      .filter((task) => filter === 'all' || task.status === filter)
      .sort((a, b) => {
        const orderDiff = (order[a.status] ?? 99) - (order[b.status] ?? 99);
        if (orderDiff !== 0) {
          return orderDiff;
        }
        return (a.name || a.id).localeCompare(b.name || b.id);
      });
  }, [filter, tasks]);

  return (
    <div className="flex h-full flex-col gap-3 text-xs text-slate-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 rounded-full border border-white/10 bg-black/30 px-2 py-1">
          {statusFilters.map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => setFilter(status)}
              className={clsx(
                'rounded-full px-2 py-1 text-[10px] uppercase tracking-[0.18em]',
                filter === status
                  ? 'bg-gradient-to-r from-galaxy-blue/40 to-galaxy-purple/40 text-white'
                  : 'text-slate-400',
              )}
            >
              {statusLabel[status]}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto">
        {filteredTasks.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-center text-xs text-slate-400">
            No tasks match this filter yet.
          </div>
        ) : (
          filteredTasks.map((task) => {
            const icon = getStatusIcon(task.status);
            return (
              <button
                key={task.id}
                type="button"
                onClick={() => onSelectTask(task.id)}
                className={clsx(
                  'w-full rounded-2xl border px-3 py-3 text-left transition',
                  activeTaskId === task.id
                    ? 'border-galaxy-blue/60 bg-galaxy-blue/15 shadow-glow'
                    : 'border-white/10 bg-white/5 hover:border-white/25 hover:bg-white/10',
                )}
              >
                <div className="flex items-center justify-between gap-3 text-xs text-slate-200">
                  <div className="flex items-center gap-2">
                    {icon}
                    <span className="font-medium text-white">{task.name || task.id}</span>
                  </div>
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-400">{task.status}</div>
                </div>
                <div className="mt-1 text-[11px] text-slate-400">
                  {task.deviceId ? `device: ${task.deviceId}` : 'No device assigned'}
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};

export default TaskList;
