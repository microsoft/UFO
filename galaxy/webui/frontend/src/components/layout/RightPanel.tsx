import React, { useEffect, useMemo } from 'react';
import { shallow } from 'zustand/shallow';
import clsx from 'clsx';
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
    <div className="flex h-full w-full flex-col gap-4 overflow-hidden">
      {/* Constellation Overview - Top half */}
      <div className="glass-card flex h-1/2 flex-shrink-0 flex-col gap-4 rounded-3xl p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div>
              <div className="text-xs uppercase tracking-[0.25em] text-slate-400">Insights</div>
              <div className="text-lg font-semibold text-white">Constellation Overview</div>
            </div>
            {activeConstellation && (
              <span className={clsx(
                'rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider',
                statusColors[activeConstellation.status] || statusColors.pending
              )}>
                {activeConstellation.status}
              </span>
            )}
          </div>
          <select
            value={activeConstellation?.id || ''}
            onChange={handleConstellationChange}
            className="rounded-full border border-white/10 bg-black/40 px-3 py-1 text-xs text-slate-200 focus:outline-none"
          >
            {constellationList.map((constellation, index) => (
              <option key={constellation.id} value={constellation.id}>
                Constellation {index + 1}
              </option>
            ))}
            {constellationList.length === 0 && <option value="">No constellations</option>}
          </select>
        </div>

        <ConstellationBlock
          constellation={activeConstellation}
          onSelectTask={(taskId) => setActiveTask(taskId)}
          variant="embedded"
        />
      </div>

      {/* TaskStar List or Task Detail - Bottom half */}
      <div className="glass-card flex h-1/2 flex-shrink-0 flex-col gap-4 rounded-3xl p-5">
        {activeTask ? (
          <TaskDetailPanel 
            task={activeTask} 
            onBack={() => setActiveTask(null)}
          />
        ) : (
          <>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.25em] text-slate-400">Tasks</div>
                <div className="text-lg font-semibold text-white">TaskStar List</div>
              </div>
            </div>
            <TaskList
              tasks={taskList}
              activeTaskId={ui.activeTaskId}
              onSelectTask={(taskId) => setActiveTask(taskId)}
            />
          </>
        )}
      </div>
    </div>
  );
};

export default RightPanel;
