import React from 'react';
import { ArrowLeft, Copy, Play, SkipForward } from 'lucide-react';
import clsx from 'clsx';
import { Task, TaskLogEntry, useGalaxyStore } from '../../store/galaxyStore';
import { getWebSocketClient } from '../../services/websocket';

interface TaskDetailPanelProps {
  task?: Task | null;
}

const renderJson = (value: any) => {
  if (!value) {
    return '∅';
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch (error) {
    return String(value);
  }
};

const renderLogs = (logs: TaskLogEntry[]) => {
  if (!logs.length) {
    return <div className="text-xs text-slate-400">No logs streamed yet.</div>;
  }
  return (
    <ul className="space-y-2 text-xs">
      {logs.map((log) => (
        <li key={log.id} className={clsx('rounded-xl border px-3 py-2', log.level === 'error' ? 'border-rose-400/40 bg-rose-500/10 text-rose-100' : 'border-white/10 bg-white/5 text-slate-200')}>
          <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-slate-400">
            <span>{log.level}</span>
            <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
          </div>
          <div className="mt-1 text-xs">{log.message}</div>
        </li>
      ))}
    </ul>
  );
};

const TaskDetailPanel: React.FC<TaskDetailPanelProps> = ({ task }) => {
  const setActiveTask = useGalaxyStore((state) => state.setActiveTask);

  if (!task) {
    return (
      <div className="glass-card flex h-full flex-col items-center justify-center gap-3 rounded-3xl p-6 text-center text-sm text-slate-300">
        Select a task to inspect details.
      </div>
    );
  }

  const handleRetry = () => {
    getWebSocketClient().send({
      type: 'task_retry',
      taskId: task.id,
      constellationId: task.constellationId,
      timestamp: Date.now(),
    });
  };

  const handleSkip = () => {
    getWebSocketClient().send({
      type: 'task_skip',
      taskId: task.id,
      constellationId: task.constellationId,
      timestamp: Date.now(),
    });
  };

  return (
    <div className="glass-card flex h-full flex-col gap-4 rounded-3xl p-5 text-xs text-slate-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setActiveTask(null)}
            className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-100 transition hover:border-white/30 hover:bg-white/10"
            title="Back to task list"
          >
            <ArrowLeft className="h-3 w-3" aria-hidden />
            Back
          </button>
          <div>
            <div className="text-xs uppercase tracking-[0.25em] text-slate-400">Task Detail</div>
            <div className="text-lg font-semibold text-white">{task.name || task.id}</div>
            <div className="text-[11px] text-slate-400">Status: {task.status}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRetry}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-100 transition hover:border-white/30 hover:bg-white/10"
          >
            <Play className="h-3 w-3" aria-hidden />
            Retry
          </button>
          <button
            type="button"
            onClick={handleSkip}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-100 transition hover:border-white/30 hover:bg-white/10"
          >
            <SkipForward className="h-3 w-3" aria-hidden />
            Skip
          </button>
        </div>
      </div>

      <div className="grid gap-3 text-[11px] text-slate-300">
        <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
          <div>Device: {task.deviceId || 'not assigned'}</div>
          <div>Started: {task.startedAt ? new Date(task.startedAt).toLocaleTimeString() : '—'}</div>
          <div>Completed: {task.completedAt ? new Date(task.completedAt).toLocaleTimeString() : '—'}</div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
          <div className="mb-1 text-[10px] uppercase tracking-[0.18em] text-slate-400">Dependencies</div>
          <div>{task.dependencies.length ? task.dependencies.join(', ') : 'None'}</div>
        </div>

        {task.error && (
          <div className="rounded-2xl border border-rose-400/40 bg-rose-500/10 px-3 py-2 text-rose-100">
            Error: {task.error}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3">
        <div className="rounded-2xl border border-white/10 bg-black/30">
          <div className="flex items-center justify-between border-b border-white/5 px-3 py-2 text-[10px] uppercase tracking-[0.18em] text-slate-400">
            Input
            <button
              type="button"
              className="inline-flex items-center gap-1 text-[10px] text-slate-400"
              onClick={() => {
                if (navigator?.clipboard) {
                  navigator.clipboard.writeText(renderJson(task.input));
                }
              }}
            >
              <Copy className="h-3 w-3" aria-hidden /> Copy
            </button>
          </div>
          <pre className="max-h-60 overflow-auto px-3 py-3 text-[11px] text-slate-200">{renderJson(task.input)}</pre>
        </div>

        <div className="rounded-2xl border border-white/10 bg-black/30">
          <div className="flex items-center justify-between border-b border-white/5 px-3 py-2 text-[10px] uppercase tracking-[0.18em] text-slate-400">
            Output
            <button
              type="button"
              className="inline-flex items-center gap-1 text-[10px] text-slate-400"
              onClick={() => {
                if (navigator?.clipboard) {
                  navigator.clipboard.writeText(renderJson(task.output || task.result));
                }
              }}
            >
              <Copy className="h-3 w-3" aria-hidden /> Copy
            </button>
          </div>
          <pre className="max-h-60 overflow-auto px-3 py-3 text-[11px] text-slate-200">{renderJson(task.output || task.result)}</pre>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto rounded-2xl border border-white/10 bg-black/30 px-3 py-3">
        <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-slate-400">Logs</div>
        {renderLogs(task.logs)}
      </div>
    </div>
  );
};

export default TaskDetailPanel;
