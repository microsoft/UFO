import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { GalaxyEvent, getWebSocketClient } from './services/websocket';
import {
  createClientId,
  NotificationItem,
  Task,
  TaskLogEntry,
  useGalaxyStore,
} from './store/galaxyStore';

const wsClient = getWebSocketClient();

const statusUnsubscribe = wsClient.onStatusChange((status) => {
  const store = useGalaxyStore.getState();
  switch (status) {
    case 'connected':
      store.setConnectionStatus('connected');
      break;
    case 'connecting':
      store.setConnectionStatus('connecting');
      break;
    case 'reconnecting':
      store.setConnectionStatus('reconnecting');
      break;
    case 'disconnected':
      store.setConnectionStatus('disconnected');
      break;
  }
});

const safeTimestamp = (event: GalaxyEvent) =>
  event?.timestamp ? Math.round(event.timestamp * 1000) : Date.now();

const parseIsoOrUndefined = (value?: string | null) => {
  if (!value) {
    return undefined;
  }
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? undefined : parsed;
};

const stringifyPayload = (payload: any) => {
  try {
    return JSON.stringify(payload, null, 2);
  } catch (error) {
    console.error('Failed to stringify payload', error);
    return String(payload);
  }
};

const buildMarkdownList = (items: any[]) =>
  items
    .map((item) => `- ${typeof item === 'string' ? item : stringifyPayload(item)}`)
    .join('\n');

const buildAgentMarkdown = (output: any) => {
  if (!output) {
    return 'Agent responded.';
  }

  if (typeof output === 'string') {
    return output;
  }

  const sections: string[] = [];

  if (output.thought) {
    // Truncate long thoughts and add expandable details
    const thought = String(output.thought);
    if (thought.length > 200) {
      const preview = thought.substring(0, 200).trim();
      sections.push(`**💭 Thought**\n${preview}... <details><summary><i>See full thought</i></summary>\n\n${thought}\n\n</details>`);
    } else {
      sections.push(`**💭 Thought**\n${thought}`);
    }
  }

  if (output.plan) {
    const planText = Array.isArray(output.plan)
      ? buildMarkdownList(output.plan)
      : output.plan;
    sections.push(`**📋 Plan**\n${planText}`);
  }

  if (output.actions_summary) {
    sections.push(`**⚡ Actions Summary**\n${output.actions_summary}`);
  }

  if (output.response) {
    sections.push(`${output.response}`);
  }

  if (output.final_response) {
    sections.push(`${output.final_response}`);
  }

  if (sections.length === 0 && output.message) {
    sections.push(String(output.message));
  }

  if (sections.length === 0) {
    sections.push(stringifyPayload(output));
  }

  return sections.join('\n\n');
};

const buildActionMarkdown = (output: any) => {
  if (!output) {
    return 'Action executed.';
  }

  if (Array.isArray(output.actions)) {
    const actions = output.actions
      .map((action: any, index: number) => {
        const title = action.description || action.name || `Action ${index + 1}`;
        const target = action.target_device_id ? ` _(device: ${action.target_device_id})_` : '';
        return `**${title}**${target}\n${stringifyPayload(action.parameters ?? action)}`;
      })
      .join('\n\n');
    return actions;
  }

  if (output.action_type || output.name) {
    return `**${output.action_type || output.name}**\n${stringifyPayload(output)}`;
  }

  return stringifyPayload(output);
};

const extractConstellationPayload = (event: GalaxyEvent) => {
  const data = event.data || {};
  return (
    data.constellation ||
    data.updated_constellation ||
    data.new_constellation ||
    event.output_data?.constellation ||
    null
  );
};

const updateConstellationFromPayload = (event: GalaxyEvent) => {
  const constellation = extractConstellationPayload(event);
  if (!constellation) {
    return;
  }

  const store = useGalaxyStore.getState();
  const constellationId =
    constellation.constellation_id || event.constellation_id || store.ensureSession();

  const dependencies = constellation.dependencies || {};

  const tasks: Array<Partial<Task> & { id: string }> = [];
  if (constellation.tasks) {
    Object.entries(constellation.tasks).forEach(([taskId, raw]) => {
      const taskData = raw as any;
      const realId = taskData.task_id || taskId;
      tasks.push({
        id: realId,
        constellationId,
        name: taskData.name || realId,
        description: taskData.description,
        status: taskData.status,
        deviceId: taskData.target_device_id || taskData.device_id,
        input: taskData.input,
        output: taskData.output,
        result: taskData.result,
        error: taskData.error,
        startedAt: parseIsoOrUndefined(taskData.started_at),
        completedAt: parseIsoOrUndefined(taskData.completed_at),
        logs: Array.isArray(taskData.logs)
          ? (taskData.logs as any[]).map((entry, index) => ({
              id: `${realId}-log-${index}`,
              timestamp: Date.now(),
              level: entry.level || 'info',
              message: entry.message || stringifyPayload(entry),
              payload: entry.payload,
            }))
          : [],
      });
    });
  }

  store.bulkUpsertTasks(constellationId, tasks, dependencies);

  const nodes = tasks.map((task) => ({
    id: task.id,
    label: task.name || task.id,
    status: task.status as any,
    deviceId: task.deviceId,
  }));

  const edges = Object.entries(dependencies).flatMap(([childId, parents]) => {
    if (!Array.isArray(parents)) {
      return [];
    }
    return parents.map((parentId) => ({
      id: `${parentId}->${childId}`,
      source: parentId,
      target: childId,
    }));
  });

  store.upsertConstellation({
    id: constellationId,
    name: constellation.name || constellationId,
    status: constellation.state || event.constellation_state || 'running',
    description: constellation.description,
    metadata: constellation.metadata,
    createdAt: parseIsoOrUndefined(constellation.created_at),
    taskIds: tasks.map((task) => task.id),
    dag: {
      nodes,
      edges,
    },
  });
};

const emitNotification = (notification: Omit<NotificationItem, 'id' | 'timestamp' | 'read'>) => {
  const store = useGalaxyStore.getState();
  store.pushNotification({
    id: createClientId(),
    timestamp: Date.now(),
    read: false,
    ...notification,
  });
};

const handleAgentResponse = (event: GalaxyEvent) => {
  const store = useGalaxyStore.getState();
  const sessionId = store.ensureSession(event.data?.session_id || null);
  const content = buildAgentMarkdown(event.output_data);

  store.addMessage({
    id: createClientId(),
    sessionId,
    role: 'assistant',
    kind: 'response',
    author: event.agent_name || 'Galaxy Agent',
    content,
    payload: event.output_data,
    timestamp: safeTimestamp(event),
    agentName: event.agent_name,
  });

  updateConstellationFromPayload(event);
};

const handleAgentAction = (event: GalaxyEvent) => {
  const store = useGalaxyStore.getState();
  const sessionId = store.ensureSession(event.data?.session_id || null);

  const content = buildActionMarkdown(event.output_data);

  store.addMessage({
    id: createClientId(),
    sessionId,
    role: 'assistant',
    kind: 'action',
    author: event.agent_name || 'Galaxy Agent',
    content,
    payload: event.output_data,
    timestamp: safeTimestamp(event),
    agentName: event.agent_name,
    actionType: event.output_data?.action_type,
  });
};

const handleTaskEvent = (event: GalaxyEvent) => {
  const store = useGalaxyStore.getState();
  const constellationId =
    event.constellation_id || event.data?.constellation_id || extractConstellationPayload(event)?.constellation_id;

  if (!event.task_id || !constellationId) {
    return;
  }

  const taskPatch: Partial<Task> = {
    status: event.status as Task['status'] | undefined,
    result: event.result ?? event.data?.result,
    error: event.error ?? event.data?.error ?? null,
    deviceId: event.data?.device_id ?? event.data?.deviceId,
  };

  if (event.event_type === 'task_completed') {
    taskPatch.completedAt = safeTimestamp(event);
  }

  if (event.event_type === 'task_started') {
    taskPatch.startedAt = safeTimestamp(event);
  }

  store.updateTask(event.task_id, taskPatch);

  if (event.data?.log_entry) {
    const logEntry = event.data.log_entry as TaskLogEntry;
    store.appendTaskLog(event.task_id, logEntry);
  } else if (event.data?.message) {
    store.appendTaskLog(event.task_id, {
      id: `${event.task_id}-${event.event_type}-${Date.now()}`,
      timestamp: safeTimestamp(event),
      level: event.event_type === 'task_failed' ? 'error' : 'info',
      message: event.data.message,
      payload: event.data,
    });
  }

  if (event.event_type === 'task_failed') {
    emitNotification({
      severity: 'error',
      title: `Task ${event.task_id} failed`,
      description: event.error?.toString() || 'A task reported a failure.',
      source: constellationId,
    });
  }
};

const handleConstellationEvent = (event: GalaxyEvent) => {
  updateConstellationFromPayload(event);

  if (event.event_type === 'constellation_completed') {
    emitNotification({
      severity: 'success',
      title: 'Constellation completed',
      description: `Constellation ${event.constellation_id || ''} finished execution successfully.`,
      source: event.constellation_id,
    });
  }

  if (event.event_type === 'constellation_failed') {
    emitNotification({
      severity: 'error',
      title: 'Constellation failed',
      description: `Constellation ${event.constellation_id || ''} reported a failure.`,
      source: event.constellation_id,
    });
  }
};

const handleDeviceEvent = (event: GalaxyEvent) => {
  const store = useGalaxyStore.getState();
  const allDevices = event.all_devices || event.data?.all_devices;
  if (allDevices) {
    store.setDevicesFromSnapshot(allDevices);
  }

  const deviceInfo = event.device_info || event.data?.device_info || {};
  const deviceId =
    event.device_id || deviceInfo.device_id || event.data?.device_id || null;

  if (!deviceId) {
    return;
  }

  const { statusChanged, previousStatus } = store.upsertDevice({
    id: deviceId,
    name: deviceInfo.device_id || deviceId,
    status: event.device_status || deviceInfo.status,
    os: deviceInfo.os,
    serverUrl: deviceInfo.server_url,
    capabilities: deviceInfo.capabilities,
    metadata: deviceInfo.metadata,
    lastHeartbeat: deviceInfo.last_heartbeat,
    connectionAttempts: deviceInfo.connection_attempts,
    maxRetries: deviceInfo.max_retries,
    currentTaskId: deviceInfo.current_task_id,
    tags: deviceInfo.metadata?.tags,
    metrics: deviceInfo.metrics,
  });

  window.setTimeout(() => {
    useGalaxyStore.getState().clearDeviceHighlight(deviceId);
  }, 4000);

  if (statusChanged) {
    const status = event.device_status || deviceInfo.status;
    const severity =
      status === 'connected'
        ? 'success'
        : status === 'device_disconnected' || status === 'disconnected'
          ? 'warning'
          : 'info';
    const description = previousStatus
      ? `Device transitioned from ${previousStatus} → ${status}`
      : `Device status updated to ${status}`;

    emitNotification({
      severity: severity as NotificationItem['severity'],
      title: `Device ${deviceId} status`,
      description,
      source: deviceId,
    });
  }
};

const handleGenericEvent = (event: GalaxyEvent) => {
  if (event.event_type?.startsWith('device_')) {
    handleDeviceEvent(event);
    return;
  }

  switch (event.event_type) {
    case 'agent_response':
      handleAgentResponse(event);
      break;
    case 'agent_action':
      handleAgentAction(event);
      break;
    case 'constellation_started':
    case 'constellation_modified':
    case 'constellation_completed':
    case 'constellation_failed':
      handleConstellationEvent(event);
      break;
    case 'task_started':
    case 'task_completed':
    case 'task_failed':
      handleTaskEvent(event);
      break;
    default:
      break;
  }
};

wsClient
  .connect()
  .catch((error) => {
    console.error('❌ Failed to connect to Galaxy WebSocket server:', error);
    useGalaxyStore.getState().setConnectionStatus('disconnected');
  });

wsClient.onEvent((event) => {
  const store = useGalaxyStore.getState();
  store.addEventToLog(event);
  handleGenericEvent(event);
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Ensure we clean up listeners when hot module reloading or teardown occurs.
if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    statusUnsubscribe();
    wsClient.disconnect();
  });
}
