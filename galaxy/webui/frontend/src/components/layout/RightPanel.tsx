import React, { useEffect, useMemo } from 'react';
import { shallow } from 'zustand/shallow';
import clsx from 'clsx';
import { Network, Star } from 'lucide-react';
import ConstellationBlock from '../constellation/ConstellationBlock';
import TaskList from '../tasks/TaskList';
import TaskDetailPanel from '../tasks/TaskDetailPanel';
import { ConstellationSummary, Task, useGalaxyStore } from '../../store/galaxyStore';

const statusColors: Record<string, string> = {
  pending: 'bg-slate-500/20 text-slate-300 border-slate-400/30',
  running: 'bg-cyan-500/20 text-cyan-300 border-cyan-400/40',
  executing: 'bg-cyan-500/20 text-cyan-300 border-cyan-400/40',
  completed: 'bg-emerald-500/20 text-emerald-300 border-emerald-400/40',
  failed: 'bg-rose-500/20 text-rose-300 border-rose-400/40',
};

const RightPanel: React.FC = () => {
  const {
    constellations,
    tasks,
    ui,
    setActiveConstellation,
    setActiveTask,
  } = useGalaxyStore(
    (state) => ({
      constellations: state.constellations,
      tasks: state.tasks,
      ui: state.ui,
      setActiveConstellation: state.setActiveConstellation,
      setActiveTask: state.setActiveTask,
    }),
    shallow,
  );

  const constellationList = useMemo(() => {
    return Object.values(constellations).sort(
      (a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0),
    );
  }, [constellations]);

  // Map constellation IDs to their request numbers (1-indexed, based on creation order)
  const constellationRequestNumbers = useMemo(() => {
    const sorted = Object.values(constellations).sort(
      (a, b) => (a.createdAt ?? 0) - (b.createdAt ?? 0), // Sort by creation time (oldest first)
    );
    const numberMap: Record<string, number> = {};
    sorted.forEach((constellation, index) => {
      numberMap[constellation.id] = index + 1;
    });
    return numberMap;
  }, [constellations]);

  useEffect(() => {
    if (!ui.activeConstellationId && constellationList.length > 0) {
      setActiveConstellation(constellationList[0].id);
    }
  }, [constellationList, setActiveConstellation, ui.activeConstellationId]);

  const activeConstellation: ConstellationSummary | undefined = ui.activeConstellationId
    ? constellations[ui.activeConstellationId]
    : constellationList[0];

  const taskList: Task[] = useMemo(() => {
    if (!activeConstellation) {
      return [];
    }
    return activeConstellation.taskIds
      .map((taskId) => tasks[taskId])
      .filter((task): task is Task => Boolean(task));
  }, [activeConstellation, tasks]);

  const activeTask = ui.activeTaskId ? tasks[ui.activeTaskId] : undefined;

  const handleConstellationChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = event.target.value;
    setActiveConstellation(selected || null);
  };

  return (
    <div className="flex h-full w-full flex-col gap-3">
      {/* Constellation Overview - Top half */}
      <div className="flex flex-1 min-h-0 flex-col gap-3 rounded-[28px] border border-white/10 bg-gradient-to-br from-[rgba(11,30,45,0.88)] via-[rgba(8,20,35,0.85)] to-[rgba(6,15,28,0.88)] p-4 overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.4),0_2px_8px_rgba(147,51,234,0.12),inset_0_1px_1px_rgba(255,255,255,0.08)] ring-1 ring-inset ring-white/5">
        <div className="flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <Network className="h-5 w-5 text-purple-400 drop-shadow-[0_0_8px_rgba(147,51,234,0.5)]" aria-hidden />
            <div className="font-heading text-xl font-semibold tracking-tight text-white">Constellation Overview</div>
            {activeConstellation && (
              <span className={clsx(
                'rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.2),inset_0_1px_1px_rgba(255,255,255,0.1)]',
                statusColors[activeConstellation.status] || statusColors.pending
              )}>
                {activeConstellation.status}
              </span>
            )}
          </div>
          <select
            value={activeConstellation?.id || ''}
            onChange={handleConstellationChange}
            className="rounded-full border border-white/5 bg-gradient-to-r from-black/30 to-black/20 px-3 py-1.5 text-xs text-slate-200 shadow-[inset_0_2px_8px_rgba(0,0,0,0.3)] focus:border-white/15 focus:outline-none focus:ring-1 focus:ring-white/10"
          >
            {constellationList.map((constellation) => (
              <option key={constellation.id} value={constellation.id}>
                Request {constellationRequestNumbers[constellation.id] || '?'}
              </option>
            ))}
            {constellationList.length === 0 && <option value="">No constellations</option>}
          </select>
        </div>

        <div className="flex-1 min-h-0 overflow-hidden">
          <ConstellationBlock
            constellation={activeConstellation}
            onSelectTask={(taskId) => setActiveTask(taskId)}
            variant="embedded"
          />
        </div>
      </div>

      {/* TaskStar List or Task Detail - Bottom half */}
      <div className="flex flex-1 min-h-0 flex-col gap-3 rounded-[28px] border border-white/10 bg-gradient-to-br from-[rgba(11,30,45,0.88)] via-[rgba(8,20,35,0.85)] to-[rgba(6,15,28,0.88)] p-4 overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.4),0_2px_8px_rgba(6,182,212,0.12),inset_0_1px_1px_rgba(255,255,255,0.08)] ring-1 ring-inset ring-white/5">
        {activeTask ? (
          <TaskDetailPanel 
            task={activeTask} 
            onBack={() => setActiveTask(null)}
          />
        ) : (
          <>
            <div className="flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-2">
                <Star className="h-5 w-5 text-cyan-400 drop-shadow-[0_0_8px_rgba(6,182,212,0.5)]" aria-hidden />
                <div className="font-heading text-xl font-semibold tracking-tight text-white">TaskStar List</div>
              </div>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              <TaskList
                tasks={taskList}
                activeTaskId={ui.activeTaskId}
                onSelectTask={(taskId) => setActiveTask(taskId)}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default RightPanel;
