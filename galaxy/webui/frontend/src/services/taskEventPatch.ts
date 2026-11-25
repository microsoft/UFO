import type { Task } from '../store/galaxyStore';
import type { GalaxyEvent } from './websocket';

export function taskEventPatch(event: GalaxyEvent, timestamp: number): Partial<Task> {
  const patch: Partial<Task> = { status: event.status as Task['status'] };
  const deviceId = event.data?.device_id ?? event.data?.deviceId;
  if (deviceId != null) patch.deviceId = deviceId;

  if (event.event_type === 'task_started') {
    return {
      ...patch, startedAt: timestamp, completedAt: undefined,
      output: undefined, result: undefined, error: null,
    };
  }

  // The snapshot is applied first. A task event can omit fields it hasn't changed.
  const result = event.result ?? event.data?.result;
  const error = event.error ?? event.data?.error;
  if (result != null) patch.result = result;
  if (error != null) patch.error = error;
  patch.completedAt = timestamp;
  return patch;
}
