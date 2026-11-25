import assert from 'node:assert/strict';
import test from 'node:test';
import { loadModule } from './loadModule.mjs';

const { useGalaxyStore, taskKey } = await loadModule('/src/store/galaxyStore.ts');
const { taskEventPatch } = await loadModule('/src/services/taskEventPatch.ts');

test('two constellations can finish tasks with the same ID in either order', () => {
  const id = 'clean-orders';
  const store = useGalaxyStore.getState();
  store.bulkUpsertTasks('first', [{ id, status: 'running' }]);
  store.bulkUpsertTasks('second', [{ id, status: 'completed', result: 'second result' }]);
  store.updateTask('first', id, { status: 'failed', error: 'Device disconnected' });
  store.bulkUpsertTasks('first', [{ id, status: 'failed', result: null }]);

  const { tasks, constellations } = useGalaxyStore.getState();
  assert.equal(tasks[taskKey('first', id)].error, 'Device disconnected');
  assert.equal(tasks[taskKey('second', id)].result, 'second result');
  assert.equal(constellations.first.statistics.failed, 1);
  assert.equal(constellations.second.statistics.completed, 1);
});

test('an explicit empty result in a snapshot clears earlier evidence', () => {
  const id = 'export';
  const store = useGalaxyStore.getState();
  store.bulkUpsertTasks('retry', [{ id, status: 'failed', result: 'old', error: 'Timeout' }]);
  store.bulkUpsertTasks('retry', [{ id, status: 'running', result: null, error: null }]);
  const task = useGalaxyStore.getState().tasks[taskKey('retry', id)];
  assert.equal(task.result, null);
  assert.equal(task.error, null);
});

test('starting another attempt clears its old evidence and keeps the assigned device', () => {
  const store = useGalaxyStore.getState();
  const id = 'export';
  store.bulkUpsertTasks('new-attempt', [{
    id, deviceId: 'workstation', status: 'failed', result: 'old', output: 'old', error: 'Timeout', completedAt: 10,
  }]);
  store.updateTask('new-attempt', id, taskEventPatch({
    event_type: 'task_started', task_id: id, status: 'running', result: null, error: null,
    timestamp: 1, data: { constellation_id: 'new-attempt' },
  }, 1000));
  const task = useGalaxyStore.getState().tasks[taskKey('new-attempt', id)];
  assert.equal(task.startedAt, 1000);
  assert.equal(task.deviceId, 'workstation');
  assert.equal(task.result, undefined);
  assert.equal(task.output, undefined);
  assert.equal(task.error, null);
  assert.equal(task.completedAt, undefined);
});

test('terminal events retain the device and result included in a constellation snapshot', () => {
  const store = useGalaxyStore.getState();
  const id = 'export';
  const result = { task_id: id, status: 'completed', result: 'receipt' };
  store.bulkUpsertTasks('with-snapshot', [{ id, deviceId: 'workstation', status: 'completed', result }]);
  for (const eventResult of [result, null]) {
    const event = {
      event_type: 'task_completed', timestamp: 2, task_id: id, status: 'completed', result: eventResult, error: null,
      data: { constellation_id: 'with-snapshot', constellation: { tasks: { [id]: { target_device_id: 'workstation', result } } } },
    };
    store.updateTask('with-snapshot', id, taskEventPatch(event, 2000));
    const task = useGalaxyStore.getState().tasks[taskKey('with-snapshot', id)];
    assert.equal(task.deviceId, 'workstation');
    assert.deepEqual(task.result, result);
    assert.equal(task.completedAt, 2000);
  }
});

test('a repeated terminal notification does not discard the known status, result or error', () => {
  const store = useGalaxyStore.getState();
  const id = 'export';
  const result = { task_id: id, status: 'failed', error: 'Device disconnected' };
  store.bulkUpsertTasks('replay', [{ id, status: 'failed', result, error: result.error }]);
  store.bulkUpsertTasks('replay', [{ id }]);
  const event = { event_type: 'task_failed', task_id: id, timestamp: 2, result: null, error: null };
  store.updateTask('replay', id, taskEventPatch(event, 2000));
  const task = useGalaxyStore.getState().tasks[taskKey('replay', id)];
  assert.equal(task.status, 'failed');
  assert.deepEqual(task.result, result);
  assert.equal(task.error, result.error);
});
