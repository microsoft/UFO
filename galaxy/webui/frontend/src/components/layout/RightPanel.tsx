import React, { useEffect, useMemo } from 'react';
import { shallow } from 'zustand/shallow';
import ConstellationBlock from '../constellation/ConstellationBlock';
import TaskList from '../tasks/TaskList';
import TaskDetailPanel from '../tasks/TaskDetailPanel';
import { ConstellationSummary, Task, useGalaxyStore } from '../../store/galaxyStore';

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
      <div className="glass-card flex flex-shrink-0 flex-col gap-4 rounded-3xl p-5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.25em] text-slate-400">Insights</div>
            <div className="text-lg font-semibold text-white">Workflow Overview</div>
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

      <div className="flex min-h-0 flex-1 flex-col gap-4">
        <div className="min-h-0 flex-1">
          <TaskList
            tasks={taskList}
            activeTaskId={ui.activeTaskId}
            onSelectTask={(taskId) => setActiveTask(taskId)}
          />
        </div>
        <div className="min-h-[220px]">
          <TaskDetailPanel task={activeTask} />
        </div>
      </div>
    </div>
  );
};

export default RightPanel;
