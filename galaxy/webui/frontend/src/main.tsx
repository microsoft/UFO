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
    // Create a copy to avoid mutating the original
    const payloadCopy = { ...payload };
    
    // Truncate thought field if it exists and is too long
    if (payloadCopy.thought && typeof payloadCopy.thought === 'string') {
      const maxLength = 100;
      if (payloadCopy.thought.length > maxLength) {
        // Find a good break point (end of sentence or word)
        let truncateAt = maxLength;
        const breakChars = ['. ', '.\n', '! ', '!\n', '? ', '?\n'];
        for (const breakChar of breakChars) {
          const idx = payloadCopy.thought.lastIndexOf(breakChar, maxLength);
          if (idx > maxLength * 0.7) {
            truncateAt = idx + breakChar.length;
            break;
          }
        }
        payloadCopy.thought = payloadCopy.thought.substring(0, truncateAt).trim() + `... [Truncated: ${payloadCopy.thought.length} chars total]`;
      }
    }
    
    return JSON.stringify(payloadCopy, null, 2);
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

  // If output is a string, treat it as thought and truncate if needed
  if (typeof output === 'string') {
    const maxLength = 100;
    if (output.length > maxLength) {
      let truncateAt = maxLength;
      const breakChars = ['. ', '.\n', '! ', '!\n', '? ', '?\n'];
      for (const breakChar of breakChars) {
        const idx = output.lastIndexOf(breakChar, maxLength);
        if (idx > maxLength * 0.7) {
          truncateAt = idx + breakChar.length;
          break;
        }
      }
      const truncated = output.substring(0, truncateAt).trim();
      return `${truncated}...\n\n_[Truncated: ${output.length} chars total]_`;
    }
    return output;
  }

  const sections: string[] = [];

  if (output.thought) {
    // Truncate long thoughts
    const thought = String(output.thought);
    const maxLength = 100;  // Aggressive truncation for better UX
    if (thought.length > maxLength) {
      // Find a good break point (end of sentence or word)
      let truncateAt = maxLength;
      const breakChars = ['. ', '.\n', '! ', '!\n', '? ', '?\n'];
      for (const breakChar of breakChars) {
        const idx = thought.lastIndexOf(breakChar, maxLength);
        if (idx > maxLength * 0.7) {  // If we find a break point in last 30%
          truncateAt = idx + breakChar.length;
          break;
        }
      }
      const truncated = thought.substring(0, truncateAt).trim();
      sections.push(`**💭 Thought**\n${truncated}...\n\n_[Truncated: ${thought.length} chars total]_`);
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
        tips: taskData.tips,
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
    metadata: {
      ...(constellation.metadata || {}),
      statistics: constellation.statistics,  // Include statistics at top level of metadata
      execution_start_time: constellation.metadata?.execution_start_time,
      execution_end_time: constellation.metadata?.execution_end_time,
    },
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
  
  // Ignore agent responses if task has been stopped
  if (store.ui.isTaskStopped) {
    console.log('⚠️ Ignoring agent response - task was stopped by user');
    return;
  }
  
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

  // Check if the agent response indicates task completion (finish or fail)
  const status = event.output_data?.status?.toLowerCase();
  if (status === 'finish' || status === 'fail') {
    store.setTaskRunning(false);
  }
};

const handleAgentAction = (event: GalaxyEvent) => {
  const store = useGalaxyStore.getState();
  
  // Ignore agent actions if task has been stopped
  if (store.ui.isTaskStopped) {
    console.log('⚠️ Ignoring agent action - task was stopped by user');
    return;
  }
  
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

  // Update constellation from task event data FIRST if available
  // This ensures constellation state (including tips) is populated before individual task updates
  if ((event.event_type === 'task_completed' || event.event_type === 'task_failed') && event.data?.constellation) {
    updateConstellationFromPayload(event);
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
      id: `${event.task_id}-${event.task_id}-${event.event_type}-${Date.now()}`,
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

  // Auto-switch to new constellation when it starts
  if (event.event_type === 'constellation_started') {
    const store = useGalaxyStore.getState();
    const constellationId = event.constellation_id;
    if (constellationId) {
      // Remove any temporary constellations that were created as placeholders
      Object.keys(store.constellations).forEach((id) => {
        if (id.startsWith('temp-')) {
          store.removeConstellation(id);
          console.log(`🗑️ Removed temporary constellation: ${id}`);
        }
      });
      
      store.setActiveConstellation(constellationId);
      console.log(`🌟 Auto-switched to new constellation: ${constellationId}`);
    }
  }

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
  console.log('📱 Device event received:', {
    event_type: event.event_type,
    device_id: event.device_id,
    device_status: event.device_status,
    device_info_status: event.device_info?.status,
    full_event: event
  });
  
  const store = useGalaxyStore.getState();
  
  // Only update full snapshot for device_snapshot events (initial sync)
  // Don't update snapshot on individual device status changes to avoid overwriting
  const allDevices = event.all_devices || event.data?.all_devices;
  if (allDevices && event.event_type === 'device_snapshot') {
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

  console.log('📱 Device upserted:', {
    deviceId,
    statusChanged,
    previousStatus,
    newStatus: event.device_status || deviceInfo.status
  });

  window.setTimeout(() => {
    useGalaxyStore.getState().clearDeviceHighlight(deviceId);
  }, 4000);

  // Device status changes are now silent - no notifications
  // Status is still tracked and displayed in the UI
};

const handleGenericEvent = (event: GalaxyEvent) => {
  // Handle session control messages (use 'type' field instead of 'event_type')
  const messageType = event.type || event.event_type;

  // Handle reset/next session acknowledgments
  if (messageType === 'reset_acknowledged') {
    console.log('✅ Session reset acknowledged:', event);
    useGalaxyStore.getState().pushNotification({
      id: `reset-${Date.now()}`,
      title: 'Session Reset',
      description: event.message || 'Session has been reset successfully',
      severity: 'success',
      timestamp: Date.now(),
      read: false,
    });
    return;
  }

  if (messageType === 'next_session_acknowledged') {
    console.log('✅ Next session acknowledged:', event);
    useGalaxyStore.getState().pushNotification({
      id: `next-session-${Date.now()}`,
      title: 'New Session',
      description: event.message || 'New session created successfully',
      severity: 'success',
      timestamp: Date.now(),
      read: false,
    });
    return;
  }

  if (messageType === 'stop_acknowledged') {
    console.log('✅ Task stop acknowledged:', event);
    useGalaxyStore.getState().pushNotification({
      id: `stop-task-${Date.now()}`,
      title: 'Task Stopped',
      description: event.message || 'Task stopped and new session created',
      severity: 'info',
      timestamp: Date.now(),
      read: false,
    });
    // Note: We don't clear constellation/tasks/devices - they persist after stop
    return;
  }

  // Handle device events
  if (event.event_type?.startsWith('device_')) {
    handleDeviceEvent(event);
    return;
  }

  // Handle other event types
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
