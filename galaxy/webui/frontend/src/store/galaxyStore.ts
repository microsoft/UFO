import { create } from 'zustand';
import { GalaxyEvent, getWebSocketClient } from '../services/websocket';
import { loadMockData } from './mockData';

// Check if we're in development mode
const isDev = import.meta.env.DEV;
const mockData = isDev ? loadMockData() : null;

export type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'disconnected';

export type MessageRole = 'user' | 'assistant' | 'system';
export type MessageKind = 'user' | 'response' | 'action' | 'system';

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
export type DependencyType = 'unconditional' | 'conditional' | 'success_only' | 'completion_only';
export type DeviceStatus =
  | 'idle'
  | 'busy'
  | 'connected'
  | 'connecting'
  | 'disconnected'
  | 'failed'
  | 'offline'
  | 'unknown';

export type NotificationSeverity = 'info' | 'success' | 'warning' | 'error';

export interface Message {
  id: string;
  sessionId: string | null;
  role: MessageRole;
  kind: MessageKind;
  author: string;
  content: string;
  payload?: any;
  timestamp: number;
  agentName?: string;
  actionType?: string;
  status?: 'pending' | 'sent' | 'error';
}

export interface DagNode {
  id: string;
  label: string;
  status: TaskStatus;
  deviceId?: string;
}

export interface DagEdge {
  id: string;
  source: string;
  target: string;
  isSatisfied?: boolean;  // Whether the dependency is satisfied
}

export interface TaskLogEntry {
  id: string;
  timestamp: number;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  payload?: any;
}

export interface Task {
  id: string;
  constellationId: string;
  name: string;
  description?: string;
  tips?: string[];
  status: TaskStatus;
  deviceId?: string;
  input?: any;
  output?: any;
  result?: any;
  error?: string | null;
  startedAt?: number;
  completedAt?: number;
  retries?: {
    current: number;
    max: number;
  };
  dependencies: string[];
  dependents: string[];
  logs: TaskLogEntry[];
}

export interface ConstellationSummary {
  id: string;
  name: string;
  status: TaskStatus | 'pending' | 'running' | 'completed' | 'failed';
  description?: string;
  metadata?: Record<string, any>;
  createdAt?: number | null;
  updatedAt?: number | null;
  taskIds: string[];
  dag: {
    nodes: DagNode[];
    edges: DagEdge[];
  };
  statistics: {
    total: number;
    pending: number;
    running: number;
    completed: number;
    failed: number;
  };
}

export interface Device {
  id: string;
  name: string;
  status: DeviceStatus;
  os?: string;
  serverUrl?: string;
  capabilities?: string[];
  metadata?: Record<string, any>;
  lastHeartbeat?: string | null;
  connectionAttempts?: number;
  maxRetries?: number;
  currentTaskId?: string | null;
  tags?: string[];
  metrics?: Record<string, any>;
  updatedAt: number;
  highlightUntil?: number;
}

export interface NotificationItem {
  id: string;
  title: string;
  description?: string;
  severity: NotificationSeverity;
  timestamp: number;
  read: boolean;
  source?: string;
  actionLabel?: string;
  actionPayload?: any;
}

interface SessionState {
  id: string | null;
  displayName: string;
  welcomeText: string;
  startedAt: number | null;
  debugMode: boolean;
  highContrast: boolean;
}

interface UIState {
  searchQuery: string;
  messageKindFilter: MessageKind | 'all';
  rightPanelTab: 'constellation' | 'tasks' | 'details';
  activeConstellationId: string | null;
  activeTaskId: string | null;
  activeDeviceId: string | null;
  showDeviceDrawer: boolean;
  showComposerShortcuts: boolean;
  isTaskRunning: boolean; // Track if a task is currently executing
  isTaskStopped: boolean; // Track if a task was stopped by user
  showLeftDrawer: boolean; // Mobile/tablet left sidebar drawer
  showRightDrawer: boolean; // Mobile/tablet right sidebar drawer
}

interface GalaxyStore {
  connected: boolean;
  connectionStatus: ConnectionStatus;
  setConnected: (connected: boolean) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;

  session: SessionState;
  setSessionInfo: (info: Partial<SessionState>) => void;
  ensureSession: (sessionId?: string | null, displayName?: string) => string;
  endSession: () => void;

  messages: Message[];
  addMessage: (message: Message) => void;
  updateMessage: (id: string, patch: Partial<Message>) => void;
  clearMessages: () => void;

  eventLog: GalaxyEvent[];
  addEventToLog: (event: GalaxyEvent) => void;
  clearEventLog: () => void;

  constellations: Record<string, ConstellationSummary>;
  upsertConstellation: (constellation: Partial<ConstellationSummary> & { id: string }) => void;
  removeConstellation: (id: string) => void;
  setActiveConstellation: (id: string | null) => void;

  tasks: Record<string, Task>;
  bulkUpsertTasks: (constellationId: string, tasks: Array<Partial<Task> & { id: string }>, dependencies?: Record<string, string[]>) => void;
  updateTask: (taskId: string, patch: Partial<Task>) => void;
  appendTaskLog: (taskId: string, entry: TaskLogEntry) => void;

  devices: Record<string, Device>;
  setDevicesFromSnapshot: (snapshot: Record<string, any>) => void;
  upsertDevice: (device: Partial<Device> & { id: string }) => { statusChanged: boolean; previousStatus?: DeviceStatus };
  clearDeviceHighlight: (deviceId: string) => void;

  notifications: NotificationItem[];
  pushNotification: (notification: NotificationItem) => void;
  dismissNotification: (id: string) => void;
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;

  ui: UIState;
  setSearchQuery: (query: string) => void;
  setMessageKindFilter: (filter: MessageKind | 'all') => void;
  setRightPanelTab: (tab: UIState['rightPanelTab']) => void;
  setActiveTask: (taskId: string | null) => void;
  setActiveDevice: (deviceId: string | null) => void;
  toggleDeviceDrawer: (open?: boolean) => void;
  toggleComposerShortcuts: () => void;
  setTaskRunning: (isRunning: boolean) => void;
  stopCurrentTask: () => void;
  toggleLeftDrawer: (open?: boolean) => void;
  toggleRightDrawer: (open?: boolean) => void;

  toggleDebugMode: () => void;
  toggleHighContrast: () => void;
  resetSessionState: (options?: { clearHistory?: boolean }) => void;
}

const MAX_MESSAGES = 500;
const MAX_NOTIFICATIONS = 30;
const MAX_EVENTS = 200;

const getNow = () => Date.now();

const normalizeTaskStatus = (status?: string | null): TaskStatus => {
  const normalized = (status || 'pending').toString().toLowerCase();
  switch (normalized) {
    case 'completed':
    case 'complete':
    case 'success':
      return 'completed';
    case 'running':
    case 'in_progress':
    case 'active':
      return 'running';
    case 'failed':
    case 'error':
      return 'failed';
    case 'skipped':
      return 'skipped';
    default:
      return 'pending';
  }
};

const normalizeDeviceStatus = (status?: string | null): DeviceStatus => {
  const normalized = (status || 'unknown').toString().toLowerCase();
  switch (normalized) {
    case 'idle':
      return 'idle';
    case 'busy':
    case 'running':
      return 'busy';
    case 'connected':
    case 'online':
      return 'connected';
    case 'connecting':
      return 'connecting';
    case 'disconnected':
      return 'disconnected';
    case 'failed':
      return 'failed';
    case 'offline':
      return 'offline';
    default:
      return 'unknown';
  }
};

const computeConstellationStats = (
  constellationId: string,
  taskIds: string[],
  tasks: Record<string, Task>,
) => {
  const stats = {
    total: 0,
    pending: 0,
    running: 0,
    completed: 0,
    failed: 0,
  };

  taskIds.forEach((taskId) => {
    const task = tasks[taskId];
    if (!task || task.constellationId !== constellationId) {
      return;
    }

    stats.total += 1;
    switch (task.status) {
      case 'pending':
        stats.pending += 1;
        break;
      case 'running':
        stats.running += 1;
        break;
      case 'completed':
        stats.completed += 1;
        break;
      case 'failed':
        stats.failed += 1;
        break;
    }
  });

  return stats;
};

const defaultSessionState = (): SessionState => ({
  id: null,
  displayName: 'Galaxy Session',
  welcomeText: 'Launch a request to orchestrate a new TaskConstellation.',
  startedAt: null,
  debugMode: false,
  highContrast: false,
});

const defaultUIState = (): UIState => ({
  searchQuery: '',
  messageKindFilter: 'all',
  rightPanelTab: 'constellation',
  activeConstellationId: null,
  activeTaskId: null,
  activeDeviceId: null,
  showDeviceDrawer: false,
  showComposerShortcuts: true,
  isTaskRunning: false,
  isTaskStopped: false,
  showLeftDrawer: false,
  showRightDrawer: false,
});

export const createClientId = () => {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `id_${Math.random().toString(36).slice(2, 10)}_${Date.now()}`;
};

export const useGalaxyStore = create<GalaxyStore>()((set, get) => ({
  connected: false,
  connectionStatus: 'idle',
  setConnected: (connected) =>
    set({
      connected,
      connectionStatus: connected ? 'connected' : 'disconnected',
    }),
  setConnectionStatus: (status) =>
    set({
      connectionStatus: status,
      connected: status === 'connected',
    }),

  session: defaultSessionState(),
  setSessionInfo: (info) =>
    set((state) => ({
      session: {
        ...state.session,
        ...info,
      },
    })),
  ensureSession: (sessionId, displayName) => {
    const current = get().session;
    if (current.id && !sessionId) {
      return current.id;
    }

    const nextId = sessionId || `session-${createClientId()}`;

    set((state) => ({
      session: {
        ...state.session,
        id: nextId,
        displayName: displayName || state.session.displayName,
        startedAt: state.session.startedAt || getNow(),
      },
    }));

    return nextId;
  },
  endSession: () =>
    set((state) => ({
      session: {
        ...state.session,
        id: null,
        startedAt: null,
      },
    })),

  messages: mockData?.messages || [],
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message].slice(-MAX_MESSAGES),
    })),
  updateMessage: (id, patch) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id
          ? {
              ...msg,
              ...patch,
            }
          : msg,
      ),
    })),
  clearMessages: () => set({ messages: [] }),

  eventLog: [],
  addEventToLog: (event) =>
    set((state) => ({
      eventLog: [...state.eventLog, event].slice(-MAX_EVENTS),
    })),
  clearEventLog: () => set({ eventLog: [] }),

  constellations: mockData ? { [mockData.constellation.id]: mockData.constellation } : {},
  upsertConstellation: (constellation) => {
    set((state) => {
      const existing = state.constellations[constellation.id];
      const taskIds = constellation.taskIds || existing?.taskIds || [];
      const updatedStats = computeConstellationStats(
        constellation.id,
        taskIds,
        state.tasks,
      );

      const updated: ConstellationSummary = {
        id: constellation.id,
        name: constellation.name || existing?.name || constellation.id,
        status: (constellation.status as TaskStatus) || existing?.status || 'pending',
        description: constellation.description ?? existing?.description,
        metadata: constellation.metadata ?? existing?.metadata,
        createdAt: constellation.createdAt ?? existing?.createdAt ?? getNow(),
        updatedAt: getNow(),
        taskIds,
        dag: {
          nodes: constellation.dag?.nodes ?? existing?.dag.nodes ?? [],
          edges: constellation.dag?.edges ?? existing?.dag.edges ?? [],
        },
        statistics: updatedStats,
      };

      return {
        constellations: {
          ...state.constellations,
          [constellation.id]: updated,
        },
        ui: {
          ...state.ui,
          activeConstellationId:
            state.ui.activeConstellationId || constellation.id,
        },
      };
    });
  },
  removeConstellation: (id) =>
    set((state) => {
      const { [id]: removed, ...remaining } = state.constellations;
      return {
        constellations: remaining,
        ui: {
          ...state.ui,
          // If the removed constellation was active, clear the active selection
          activeConstellationId:
            state.ui.activeConstellationId === id
              ? null
              : state.ui.activeConstellationId,
        },
      };
    }),
  setActiveConstellation: (id) =>
    set((state) => ({
      ui: {
        ...state.ui,
        activeConstellationId: id,
        activeTaskId: id ? state.ui.activeTaskId : null,
      },
    })),

  tasks: mockData ? Object.fromEntries(mockData.tasks.map(t => [t.id, t])) : {},
  bulkUpsertTasks: (constellationId, tasks, dependencies = {}) => {
    set((state) => {
      const nextTasks = { ...state.tasks };
      const dependencyGraph: Record<string, string[]> = {};

      Object.entries(dependencies).forEach(([taskId, deps]) => {
        dependencyGraph[taskId] = Array.isArray(deps) ? deps : [];
      });

      const taskIds = new Set<string>(
        state.constellations[constellationId]?.taskIds ?? [],
      );

      tasks.forEach((task) => {
        const normalizedStatus = normalizeTaskStatus(task.status as string);
        const deps = dependencyGraph[task.id] || task.dependencies || [];

        const existing = state.tasks[task.id];
        const dependents = new Set(existing?.dependents ?? []);

        Object.entries(dependencyGraph).forEach(([childId, parents]) => {
          if (parents?.includes(task.id)) {
            dependents.add(childId);
          }
        });

        nextTasks[task.id] = {
          id: task.id,
          constellationId,
          name: task.name || existing?.name || task.id,
          description: task.description ?? existing?.description,
          status: normalizedStatus,
          deviceId:
            task.deviceId ?? (task as Record<string, any>).device ?? existing?.deviceId,
          input: task.input ?? existing?.input,
          output: task.output ?? existing?.output,
          result: task.result ?? existing?.result,
          error: task.error ?? existing?.error ?? null,
          tips: task.tips ?? existing?.tips,
          startedAt: task.startedAt ?? existing?.startedAt,
          completedAt: task.completedAt ?? existing?.completedAt,
          retries: task.retries ?? existing?.retries,
          dependencies: deps,
          dependents: Array.from(dependents),
          logs: task.logs ?? existing?.logs ?? [],
        };

        taskIds.add(task.id);
      });

      const updatedTaskIdList = Array.from(taskIds);

      const updatedStats = computeConstellationStats(
        constellationId,
        updatedTaskIdList,
        nextTasks,
      );

      const existingConstellation = state.constellations[constellationId];

      return {
        tasks: nextTasks,
        constellations: {
          ...state.constellations,
          [constellationId]: existingConstellation
            ? {
                ...existingConstellation,
                taskIds: updatedTaskIdList,
                statistics: updatedStats,
                updatedAt: getNow(),
              }
            : {
                id: constellationId,
                name: constellationId,
                status: 'pending',
                taskIds: updatedTaskIdList,
                dag: { nodes: [], edges: [] },
                statistics: updatedStats,
                createdAt: getNow(),
                updatedAt: getNow(),
              },
        },
      };
    });
  },
  updateTask: (taskId, patch) => {
    set((state) => {
      const existing = state.tasks[taskId];
      if (!existing) {
        return state;
      }

      const updatedTask: Task = {
        ...existing,
        ...patch,
        status: patch.status ? normalizeTaskStatus(patch.status) : existing.status,
      };

      const constellation = state.constellations[existing.constellationId];

      const nextState: Partial<GalaxyStore> = {
        tasks: {
          ...state.tasks,
          [taskId]: updatedTask,
        },
      } as Partial<GalaxyStore>;

      if (constellation) {
        nextState.constellations = {
          ...state.constellations,
          [constellation.id]: {
            ...constellation,
            statistics: computeConstellationStats(
              constellation.id,
              constellation.taskIds,
              {
                ...state.tasks,
                [taskId]: updatedTask,
              },
            ),
            updatedAt: getNow(),
          },
        };
      }

      return nextState as GalaxyStore;
    });
  },
  appendTaskLog: (taskId, entry) =>
    set((state) => {
      const existing = state.tasks[taskId];
      if (!existing) {
        return state;
      }

      const updatedLogs = [...existing.logs, entry];

      return {
        tasks: {
          ...state.tasks,
          [taskId]: {
            ...existing,
            logs: updatedLogs,
          },
        },
      };
    }),

  devices: mockData ? Object.fromEntries(mockData.devices.map(d => [d.id, d])) : {},
  setDevicesFromSnapshot: (snapshot) => {
    set((state) => {
      const nextDevices: Record<string, Device> = { ...state.devices };
      Object.entries(snapshot || {}).forEach(([deviceId, raw]) => {
        const normalizedStatus = normalizeDeviceStatus((raw as any)?.status);
        nextDevices[deviceId] = {
          id: deviceId,
          name: (raw as any)?.device_id || deviceId,
          status: normalizedStatus,
          os: (raw as any)?.os,
          serverUrl: (raw as any)?.server_url,
          capabilities: (raw as any)?.capabilities || [],
          metadata: (raw as any)?.metadata || {},
          lastHeartbeat: (raw as any)?.last_heartbeat || null,
          connectionAttempts: (raw as any)?.connection_attempts,
          maxRetries: (raw as any)?.max_retries,
          currentTaskId: (raw as any)?.current_task_id,
          tags: ((raw as any)?.metadata?.tags as string[]) || [],
          metrics: (raw as any)?.metrics || {},
          updatedAt: getNow(),
        };
      });

      return {
        devices: nextDevices,
      };
    });
  },
  upsertDevice: (device) => {
    const previous = get().devices[device.id];
    const nextStatus = normalizeDeviceStatus(device.status || previous?.status);
    set((state) => ({
      devices: {
        ...state.devices,
        [device.id]: {
          id: device.id,
          name: device.name || previous?.name || device.id,
          status: nextStatus,
          os: device.os ?? previous?.os,
          serverUrl: device.serverUrl ?? previous?.serverUrl,
          capabilities: device.capabilities ?? previous?.capabilities ?? [],
          metadata: device.metadata ?? previous?.metadata ?? {},
          lastHeartbeat: device.lastHeartbeat ?? previous?.lastHeartbeat ?? null,
          connectionAttempts:
            device.connectionAttempts ?? previous?.connectionAttempts,
          maxRetries: device.maxRetries ?? previous?.maxRetries,
          currentTaskId: device.currentTaskId ?? previous?.currentTaskId ?? null,
          tags: device.tags ?? previous?.tags ?? [],
          metrics: device.metrics ?? previous?.metrics ?? {},
          updatedAt: getNow(),
          highlightUntil: getNow() + 4_000,
        },
      },
    }));

    return {
      statusChanged: previous?.status !== nextStatus,
      previousStatus: previous?.status,
    };
  },
  clearDeviceHighlight: (deviceId) =>
    set((state) => {
      const device = state.devices[deviceId];
      if (!device) {
        return state;
      }

      return {
        devices: {
          ...state.devices,
          [deviceId]: {
            ...device,
            highlightUntil: 0,
          },
        },
      };
    }),

  notifications: [],
  pushNotification: (notification) =>
    set((state) => ({
      notifications: [notification, ...state.notifications].slice(
        0,
        MAX_NOTIFICATIONS,
      ),
    })),
  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((notification) => notification.id !== id),
    })),
  markNotificationRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((notification) =>
        notification.id === id
          ? {
              ...notification,
              read: true,
            }
          : notification,
      ),
    })),
  markAllNotificationsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((notification) => ({
        ...notification,
        read: true,
      })),
    })),

  ui: {
    ...defaultUIState(),
    activeConstellationId: mockData?.constellation.id || null,
  },
  setSearchQuery: (query) =>
    set((state) => ({
      ui: {
        ...state.ui,
        searchQuery: query,
      },
    })),
  setMessageKindFilter: (filter) =>
    set((state) => ({
      ui: {
        ...state.ui,
        messageKindFilter: filter,
      },
    })),
  setRightPanelTab: (tab) =>
    set((state) => ({
      ui: {
        ...state.ui,
        rightPanelTab: tab,
      },
    })),
  setActiveTask: (taskId) =>
    set((state) => ({
      ui: {
        ...state.ui,
        activeTaskId: taskId,
        rightPanelTab: taskId ? 'details' : state.ui.rightPanelTab,
      },
    })),
  setActiveDevice: (deviceId) =>
    set((state) => ({
      ui: {
        ...state.ui,
        activeDeviceId: deviceId,
      },
    })),
  toggleDeviceDrawer: (open) =>
    set((state) => ({
      ui: {
        ...state.ui,
        showDeviceDrawer:
          typeof open === 'boolean' ? open : !state.ui.showDeviceDrawer,
      },
    })),
  toggleComposerShortcuts: () =>
    set((state) => ({
      ui: {
        ...state.ui,
        showComposerShortcuts: !state.ui.showComposerShortcuts,
      },
    })),

  setTaskRunning: (isRunning) =>
    set((state) => ({
      ui: {
        ...state.ui,
        isTaskRunning: isRunning,
        isTaskStopped: isRunning ? false : state.ui.isTaskStopped, // Clear stopped state when new task starts
      },
    })),

  stopCurrentTask: () => {
    // Send stop message to backend
    const wsClient = getWebSocketClient();
    wsClient.send({ type: 'stop_task', timestamp: Date.now() });
    
    // Update UI state - mark as stopped
    set((state) => ({
      ui: {
        ...state.ui,
        isTaskRunning: false,
        isTaskStopped: true,
      },
    }));
  },

  toggleLeftDrawer: (open) =>
    set((state) => ({
      ui: {
        ...state.ui,
        showLeftDrawer:
          typeof open === 'boolean' ? open : !state.ui.showLeftDrawer,
      },
    })),

  toggleRightDrawer: (open) =>
    set((state) => ({
      ui: {
        ...state.ui,
        showRightDrawer:
          typeof open === 'boolean' ? open : !state.ui.showRightDrawer,
      },
    })),

  toggleDebugMode: () =>
    set((state) => ({
      session: {
        ...state.session,
        debugMode: !state.session.debugMode,
      },
    })),
  toggleHighContrast: () =>
    set((state) => ({
      session: {
        ...state.session,
        highContrast: !state.session.highContrast,
      },
    })),

  resetSessionState: (options?: { clearHistory?: boolean }) =>
    set((state) => {
      const clearHistory = options?.clearHistory ?? true; // Default to true for backward compatibility
      
      return {
        messages: [],
        eventLog: [],
        constellations: clearHistory ? {} : state.constellations,
        tasks: clearHistory ? {} : state.tasks,
        // Keep devices - they should persist across session resets
        // devices: {}, // Don't clear devices
        notifications: [],
        ui: {
          ...defaultUIState(),
          showComposerShortcuts: state.ui.showComposerShortcuts,
        },
        session: {
          ...state.session,
          id: null,
          startedAt: null,
        },
      };
    }),
}));
