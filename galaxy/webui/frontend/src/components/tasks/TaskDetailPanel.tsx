import React, { useMemo } from 'react';
import { ArrowLeft, Copy, ChevronRight, Cpu, Clock, CheckCircle2, XCircle, Loader2, Zap, FileText, GitBranch } from 'lucide-react';
import clsx from 'clsx';
import { Task, useGalaxyStore } from '../../store/galaxyStore';

interface TaskDetailPanelProps {
  task?: Task | null;
  onBack?: () => void;
}

const extractResultValue = (taskResult: any): string => {
  if (!taskResult) {
    return '∅';
  }
  
  // If result is an object with a 'result' property that is an array
  if (taskResult && typeof taskResult === 'object' && !Array.isArray(taskResult)) {
    if ('result' in taskResult && Array.isArray(taskResult.result)) {
      const resultArray = taskResult.result;
      if (resultArray.length > 0) {
        const firstItem = resultArray[0];
        if (firstItem && typeof firstItem === 'object' && 'result' in firstItem) {
          return String(firstItem.result);
        }
      }
    }
  }
  
  // If result is an array and has at least one item
  if (Array.isArray(taskResult) && taskResult.length > 0) {
    const firstItem = taskResult[0];
    
    // If the first item has a 'result' field, use it
    if (firstItem && typeof firstItem === 'object' && 'result' in firstItem) {
      return String(firstItem.result);
    }
  }
  
  // Otherwise, render the whole result as JSON
  try {
    return JSON.stringify(taskResult, null, 2);
  } catch (error) {
    return String(taskResult);
  }
};

const getStatusConfig = (status: string) => {
  const normalized = status.toLowerCase();
  
  if (normalized === 'completed' || normalized === 'success' || normalized === 'finish') {
    return {
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bgGlow: 'bg-emerald-500/10',
      borderGlow: 'border-emerald-400/30',
      label: 'COMPLETED'
    };
  }
  
  if (normalized === 'running' || normalized === 'in_progress') {
    return {
      icon: Loader2,
      color: 'text-cyan-400',
      bgGlow: 'bg-cyan-500/10',
      borderGlow: 'border-cyan-400/30',
      label: 'RUNNING'
    };
  }
  
  if (normalized === 'failed' || normalized === 'error') {
    return {
      icon: XCircle,
      color: 'text-rose-400',
      bgGlow: 'bg-rose-500/10',
      borderGlow: 'border-rose-400/30',
      label: 'FAILED'
    };
  }
  
  if (normalized === 'pending' || normalized === 'waiting') {
    return {
      icon: Clock,
      color: 'text-slate-400',
      bgGlow: 'bg-slate-500/10',
      borderGlow: 'border-slate-400/30',
      label: 'PENDING'
    };
  }
  
  return {
    icon: Zap,
    color: 'text-slate-400',
    bgGlow: 'bg-slate-500/10',
    borderGlow: 'border-slate-400/30',
    label: status.toUpperCase()
  };
};

const TaskDetailPanel: React.FC<TaskDetailPanelProps> = ({ task, onBack }) => {
  const { tasks, setActiveTask } = useGalaxyStore((state) => ({
    tasks: state.tasks,
    setActiveTask: state.setActiveTask,
  }));

  const statusConfig = useMemo(() => 
    task ? getStatusConfig(task.status) : null
  , [task?.status]);

  const executionDuration = useMemo(() => {
    if (!task?.startedAt || !task?.completedAt) return null;
    const duration = (task.completedAt - task.startedAt) / 1000;
    if (duration < 60) return `${duration.toFixed(1)}s`;
    return `${Math.floor(duration / 60)}m ${(duration % 60).toFixed(0)}s`;
  }, [task?.startedAt, task?.completedAt]);

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      setActiveTask(null);
    }
  };

  const constellationTasks = useMemo(() => {
    if (!task) return [];
    return Object.values(tasks)
      .filter(t => t.constellationId === task.constellationId)
      .sort((a, b) => a.id.localeCompare(b.id));
  }, [task, tasks]);

  const currentTaskIndex = useMemo(() => {
    if (!task || constellationTasks.length === 0) return -1;
    return constellationTasks.findIndex(t => t.id === task.id);
  }, [task, constellationTasks]);

  const handlePrevious = () => {
    if (currentTaskIndex > 0) {
      setActiveTask(constellationTasks[currentTaskIndex - 1].id);
    }
  };

  const handleNext = () => {
    if (currentTaskIndex >= 0 && currentTaskIndex < constellationTasks.length - 1) {
      setActiveTask(constellationTasks[currentTaskIndex + 1].id);
    }
  };

  const canGoPrevious = currentTaskIndex > 0;
  const canGoNext = currentTaskIndex >= 0 && currentTaskIndex < constellationTasks.length - 1;

  // Get dependency task status color
  const getDependencyColor = (depId: string) => {
    const depTask = tasks[depId];
    if (!depTask) {
      return {
        border: 'border-slate-500/30',
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        shadow: 'shadow-[0_0_6px_rgba(148,163,184,0.2)]'
      };
    }
    
    const status = depTask.status.toLowerCase();
    
    if (status === 'completed' || status === 'success' || status === 'finish') {
      return {
        border: 'border-emerald-400/30',
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        shadow: 'shadow-[0_0_6px_rgba(52,211,153,0.3)]'
      };
    }
    
    if (status === 'running' || status === 'in_progress') {
      return {
        border: 'border-cyan-400/30',
        bg: 'bg-cyan-500/10',
        text: 'text-cyan-400',
        shadow: 'shadow-[0_0_6px_rgba(34,211,238,0.3)]'
      };
    }
    
    if (status === 'failed' || status === 'error') {
      return {
        border: 'border-rose-400/30',
        bg: 'bg-rose-500/10',
        text: 'text-rose-400',
        shadow: 'shadow-[0_0_6px_rgba(251,113,133,0.3)]'
      };
    }
    
    // Default/pending
    return {
      border: 'border-amber-400/30',
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      shadow: 'shadow-[0_0_6px_rgba(251,191,36,0.3)]'
    };
  };

  if (!task) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-sm text-slate-300">
        <Zap className="h-8 w-8 text-galaxy-blue/50" aria-hidden />
        <div className="font-heading text-base">Select a task to view details</div>
        <div className="text-xs text-slate-500">Choose from the TaskStar list above</div>
      </div>
    );
  }

  const StatusIcon = statusConfig?.icon || Zap;

  return (
    <div className="flex h-full gap-4 overflow-hidden">
      {/* Left Column - Metadata */}
      <div className="flex w-[40%] flex-shrink-0 flex-col gap-3 overflow-hidden">
        {/* Task Header - Fixed */}
        <div className="flex-shrink-0 rounded-xl border border-white/10 bg-gradient-to-br from-galaxy-dark/80 via-galaxy-indigo/20 to-galaxy-dark/90 p-3 shadow-[0_4px_20px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.08)]">
          <div className="mb-2 flex items-center gap-2">
            <div className={clsx(
              "flex items-center justify-center rounded-lg p-1.5",
              statusConfig?.bgGlow,
              "border",
              statusConfig?.borderGlow,
              "shadow-[0_0_16px_rgba(0,0,0,0.3)]"
            )}>
              <StatusIcon 
                className={clsx(
                  "h-5 w-5", 
                  statusConfig?.color,
                  task.status.toLowerCase() === 'running' && "animate-spin"
                )} 
                aria-hidden 
              />
            </div>
            <div className="flex-1 min-w-0">
              <div className="truncate font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                Task ID
              </div>
              <div className="truncate font-mono text-xs font-semibold text-galaxy-glow drop-shadow-[0_0_8px_rgba(33,240,255,0.5)]">
                {task.id}
              </div>
            </div>
          </div>
          <div className="mb-1.5 truncate font-heading text-lg font-bold text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.4)]">
            {task.name || task.id}
          </div>
          <div className={clsx(
            "inline-block rounded-full border px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.15em]",
            statusConfig?.color,
            statusConfig?.borderGlow,
            statusConfig?.bgGlow
          )}>
            {statusConfig?.label}
          </div>
        </div>

        {/* Execution Info - Fixed */}
        <div className="flex-shrink-0 space-y-2 rounded-xl border border-white/10 bg-gradient-to-br from-black/60 to-black/40 p-3 shadow-[0_4px_14px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.05)]">
          <div className="mb-2 flex items-center gap-1.5 border-b border-white/10 pb-2">
            <Cpu className="h-4 w-4 text-galaxy-blue" aria-hidden />
            <div className="font-mono text-[11px] font-semibold uppercase tracking-[0.15em] text-slate-300">
              Execution
            </div>
          </div>
          
          <div className="space-y-2 font-mono text-[11px]">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Device:</span>
              <span className="font-semibold text-galaxy-teal">
                {task.deviceId || '—'}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Started:</span>
              <span className="font-semibold text-slate-300">
                {task.startedAt ? new Date(task.startedAt).toLocaleTimeString() : '—'}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Completed:</span>
              <span className="font-semibold text-slate-300">
                {task.completedAt ? new Date(task.completedAt).toLocaleTimeString() : '—'}
              </span>
            </div>
            
            <div className="flex items-center justify-between border-t border-white/5 pt-2">
              <span className="text-slate-500">Duration:</span>
              <span className="font-bold text-emerald-400">
                {executionDuration || '—'}
              </span>
            </div>
          </div>
        </div>

        {/* Dependencies - Fixed with horizontal scroll */}
        <div className="flex-shrink-0 rounded-xl border border-white/10 bg-gradient-to-br from-black/60 to-black/40 p-3 shadow-[0_4px_14px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.05)]">
          <div className="mb-2 flex items-center gap-2">
            <div className="flex h-5 w-5 items-center justify-center rounded-md bg-gradient-to-br from-galaxy-teal/20 to-galaxy-blue/10">
              <GitBranch className="h-3 w-3 text-galaxy-teal" aria-hidden />
            </div>
            <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400">
              Dependencies
            </span>
          </div>
          {task.dependencies.length > 0 ? (
            <div className="flex gap-1.5 overflow-x-auto pb-1">
              {task.dependencies.map((depId) => {
                const colors = getDependencyColor(depId);
                return (
                  <span
                    key={depId}
                    className={clsx(
                      "flex-shrink-0 rounded-md border px-2 py-1 font-mono text-[10px] font-medium transition-all",
                      colors.border,
                      colors.bg,
                      colors.text,
                      colors.shadow
                    )}
                  >
                    {depId}
                  </span>
                );
              })}
            </div>
          ) : (
            <div className="font-mono text-[11px] text-slate-500">None</div>
          )}
        </div>

        {/* Error Display - Only show when exists, otherwise fills with flexible space */}
        {task.error ? (
          <div className="min-h-0 flex-1 overflow-y-auto pr-1">
            <div className="animate-pulse-slow rounded-xl border border-rose-400/50 bg-gradient-to-br from-rose-500/20 to-rose-600/10 p-3 shadow-[0_0_20px_rgba(244,63,94,0.3),inset_0_1px_2px_rgba(255,255,255,0.1)]">
              <div className="mb-1.5 flex items-center gap-1.5">
                <XCircle className="h-4 w-4 text-rose-400" aria-hidden />
                <div className="font-mono text-[10px] font-semibold uppercase tracking-[0.15em] text-rose-300">
                  Error
                </div>
              </div>
              <div className="font-mono text-[11px] leading-relaxed text-rose-100">
                {task.error}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1" />
        )}

        {/* Fixed Navigation Buttons at Bottom */}
        <div className="flex-shrink-0 space-y-2">
          {/* Previous & Next Buttons - Side by Side */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrevious}
              disabled={!canGoPrevious}
              className={clsx(
                "group flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.3),inset_0_1px_1px_rgba(255,255,255,0.06)] transition-all",
                canGoPrevious
                  ? "border-white/10 bg-gradient-to-r from-white/5 to-white/3 text-slate-300 hover:border-galaxy-teal/40 hover:from-galaxy-teal/10 hover:to-galaxy-teal/5 hover:text-slate-100 hover:shadow-[0_3px_10px_rgba(56,189,248,0.25)]"
                  : "cursor-not-allowed border-white/5 bg-white/3 text-slate-600 opacity-30"
              )}
              title={canGoPrevious ? "Previous task" : "No previous task"}
            >
              <ChevronRight className="h-3.5 w-3.5 rotate-180 transition-transform group-hover:-translate-x-0.5" aria-hidden />
              Prev
            </button>
            <button
              type="button"
              onClick={handleNext}
              disabled={!canGoNext}
              className={clsx(
                "group flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.3),inset_0_1px_1px_rgba(255,255,255,0.06)] transition-all",
                canGoNext
                  ? "border-white/10 bg-gradient-to-r from-white/5 to-white/3 text-slate-300 hover:border-galaxy-purple/40 hover:from-galaxy-purple/10 hover:to-galaxy-purple/5 hover:text-slate-100 hover:shadow-[0_3px_10px_rgba(123,44,191,0.25)]"
                  : "cursor-not-allowed border-white/5 bg-white/3 text-slate-600 opacity-30"
              )}
              title={canGoNext ? "Next task" : "No next task"}
            >
              Next
              <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden />
            </button>
          </div>
          
          {/* Back Button - Full Width */}
          <button
            type="button"
            onClick={handleBack}
            className="group flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-gradient-to-r from-white/5 to-white/3 px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-slate-200 shadow-[0_2px_8px_rgba(0,0,0,0.3),inset_0_1px_1px_rgba(255,255,255,0.06)] transition-all hover:border-galaxy-blue/40 hover:from-galaxy-blue/10 hover:to-galaxy-blue/5 hover:shadow-[0_3px_10px_rgba(15,123,255,0.25)]"
            title="Back to task list"
          >
            <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-0.5" aria-hidden />
            Back to List
          </button>
        </div>
      </div>

      {/* Right Column - Content */}
      <div className="flex w-[60%] flex-shrink-0 flex-col gap-3 overflow-hidden">
        {/* Description */}
        {task.description && (
          <div className="rounded-xl border border-white/10 bg-gradient-to-br from-black/60 to-black/40 p-3 shadow-[0_4px_14px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.05)]">
            <div className="mb-2 flex items-center gap-2">
              <div className="flex h-5 w-5 items-center justify-center rounded-md bg-gradient-to-br from-slate-500/20 to-slate-600/10">
                <FileText className="h-3 w-3 text-slate-400" aria-hidden />
              </div>
              <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400">
                Description
              </span>
            </div>
            <div className="font-sans text-[12px] leading-relaxed text-slate-200">
              {task.description}
            </div>
          </div>
        )}

        {/* Tips */}
        {task.tips && task.tips.length > 0 && (
          <div className="rounded-xl border border-galaxy-purple/30 bg-gradient-to-br from-galaxy-purple/10 via-galaxy-indigo/5 to-black/60 p-4 shadow-[0_4px_20px_rgba(123,44,191,0.3),0_0_1px_rgba(123,44,191,0.4),inset_0_1px_1px_rgba(255,255,255,0.08)]">
            <div className="mb-3 flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-br from-galaxy-purple to-galaxy-indigo shadow-[0_0_12px_rgba(123,44,191,0.5)]">
                <span className="text-[14px]">💡</span>
              </div>
              <span className="font-mono text-[11px] font-bold uppercase tracking-[0.2em] text-transparent bg-clip-text bg-gradient-to-r from-galaxy-purple via-purple-300 to-galaxy-purple">
                Execution Tips
              </span>
            </div>
            <ul className="space-y-2.5">
              {task.tips.map((tip, index) => (
                <li key={index} className="group flex items-start gap-3 transition-all duration-200 hover:translate-x-1">
                  <span className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md border border-galaxy-purple/40 bg-gradient-to-br from-galaxy-purple/20 to-galaxy-indigo/10 font-mono text-[10px] font-extrabold text-purple-200 shadow-[0_0_8px_rgba(123,44,191,0.3)] transition-all group-hover:border-galaxy-purple/60 group-hover:shadow-[0_0_12px_rgba(123,44,191,0.5)] group-hover:scale-110">
                    {index + 1}
                  </span>
                  <span className="flex-1 font-sans text-[12px] leading-relaxed text-slate-100 group-hover:text-white transition-colors">{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Result Output - Takes remaining space */}
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-galaxy-blue/20 bg-gradient-to-br from-black/80 to-galaxy-dark/60 shadow-[0_8px_28px_rgba(0,0,0,0.5),0_0_1px_rgba(15,123,255,0.3),inset_0_1px_1px_rgba(255,255,255,0.08)]">
          <div className="flex items-center justify-between border-b border-white/10 bg-gradient-to-r from-galaxy-blue/10 to-galaxy-purple/10 px-3 py-2.5">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 animate-pulse rounded-full bg-galaxy-glow shadow-[0_0_6px_rgba(33,240,255,0.8)]" />
              <span className="font-mono text-[11px] font-bold uppercase tracking-[0.2em] text-slate-200">
                Result
              </span>
            </div>
            <button
              type="button"
              className="group inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-slate-400 transition-all hover:border-galaxy-glow/40 hover:bg-galaxy-glow/10 hover:text-galaxy-glow hover:shadow-[0_0_10px_rgba(33,240,255,0.3)]"
              onClick={() => {
                if (navigator?.clipboard) {
                  const resultValue = task.output || task.result;
                  navigator.clipboard.writeText(extractResultValue(resultValue));
                }
              }}
            >
              <Copy className="h-3 w-3" aria-hidden />
              Copy
            </button>
          </div>
          <div className="flex-1 overflow-auto p-3">
            <pre className="font-mono text-[11px] leading-relaxed text-slate-200 selection:bg-galaxy-blue/30">
              {extractResultValue(task.output || task.result)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskDetailPanel;
