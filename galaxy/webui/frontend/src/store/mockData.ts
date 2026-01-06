import { Message, Device, Task, ConstellationSummary, TaskStatus } from './galaxyStore';

// Mock Messages (User + Agent interactions)
export const mockMessages: Message[] = [
  {
    id: 'msg-1',
    sessionId: 'session-123',
    role: 'user',
    kind: 'user',
    author: 'User',
    content: 'Create a constellation to process data across multiple devices',
    timestamp: Date.now() - 180000,
  },
  {
    id: 'msg-2',
    sessionId: 'session-123',
    role: 'assistant',
    kind: 'response',
    author: 'UFO',
    content: 'I will create a constellation with multiple tasks distributed across available devices.',
    payload: {
      thought: 'The user wants to create a multi-device constellation. I need to analyze available devices, design a task graph with proper dependencies, and distribute workload efficiently across the cluster.',
      response: 'I will create a constellation with multiple tasks distributed across available devices.',
      status: 'completed',
    },
    timestamp: Date.now() - 175000,
  },
  {
    id: 'msg-3',
    sessionId: 'session-123',
    role: 'assistant',
    kind: 'response',
    author: 'UFO',
    content: '',
    payload: {
      actions: [
        {
          function: 'build_constellation',
          arguments: {
            task_count: 5,
            dependency_count: 4,
          },
          status: 'completed',
          result: {
            status: 'completed',
          },
        },
      ],
      status: 'completed',
    },
    timestamp: Date.now() - 170000,
  },
  {
    id: 'msg-4',
    sessionId: 'session-123',
    role: 'assistant',
    kind: 'response',
    author: 'UFO',
    content: '',
    payload: {
      actions: [
        {
          function: 'execute_task',
          arguments: {
            task_id: 'task-1',
            device_id: 'device-laptop',
          },
          status: 'running',
          result: {
            status: 'running',
          },
        },
      ],
      status: 'running',
    },
    timestamp: Date.now() - 165000,
  },
  {
    id: 'msg-5',
    sessionId: 'session-123',
    role: 'user',
    kind: 'user',
    author: 'User',
    content: 'Show me the current status of all tasks',
    timestamp: Date.now() - 120000,
  },
  {
    id: 'msg-6',
    sessionId: 'session-123',
    role: 'assistant',
    kind: 'response',
    author: 'UFO',
    content: 'Here is the current constellation status.',
    payload: {
      thought: 'I need to query the constellation status and present the task execution progress to the user.',
      response: 'Here is the current constellation status with 3 completed tasks, 1 running task, and 1 pending task.',
      status: 'completed',
    },
    timestamp: Date.now() - 115000,
  },
];

// Mock Devices
export const mockDevices: Device[] = [
  {
    id: 'device-laptop',
    name: 'MacBook Pro',
    status: 'busy',
    os: 'macOS',
    capabilities: ['compute', 'storage', 'network'],
    metadata: {
      hostname: 'macbook-pro.local',
      ip: '192.168.1.100',
      type: 'laptop',
      cpu: 85,
      memory: 72,
      disk: 45,
    },
    lastHeartbeat: new Date(Date.now() - 5000).toISOString(),
    updatedAt: Date.now() - 5000,
  },
  {
    id: 'device-server',
    name: 'Cloud Server',
    status: 'busy',
    os: 'Linux',
    capabilities: ['compute', 'storage', 'network', 'gpu'],
    metadata: {
      hostname: 'cloud-server-01',
      ip: '10.0.0.50',
      gpu: 'NVIDIA A100',
      type: 'server',
      cpu: 45,
      memory: 38,
      disk: 22,
    },
    lastHeartbeat: new Date(Date.now() - 3000).toISOString(),
    updatedAt: Date.now() - 3000,
  },
  {
    id: 'device-tablet',
    name: 'iPad Pro',
    status: 'idle',
    os: 'iOS',
    capabilities: ['compute', 'storage'],
    metadata: {
      hostname: 'ipad-pro',
      ip: '192.168.1.101',
      type: 'tablet',
      cpu: 15,
      memory: 25,
      disk: 60,
    },
    lastHeartbeat: new Date(Date.now() - 10000).toISOString(),
    updatedAt: Date.now() - 10000,
  },
  {
    id: 'device-desktop',
    name: 'Desktop Workstation',
    status: 'connected',
    os: 'Windows',
    capabilities: ['compute', 'storage', 'network'],
    metadata: {
      hostname: 'workstation-01',
      ip: '192.168.1.102',
      type: 'desktop',
      cpu: 30,
      memory: 42,
      disk: 35,
    },
    lastHeartbeat: new Date(Date.now() - 8000).toISOString(),
    updatedAt: Date.now() - 8000,
  },
];

// Mock Tasks
export const mockTasks: Task[] = [
  {
    id: 'task-1',
    constellationId: 'constellation-1',
    name: 'Data Preprocessing',
    description: 'Load and preprocess raw data files',
    status: 'completed' as TaskStatus,
    deviceId: 'device-laptop',
    input: { files: ['data1.csv', 'data2.csv'] },
    output: { processed_files: ['processed_data.parquet'] },
    result: { success: true, records: 15420 },
    startedAt: Date.now() - 160000,
    completedAt: Date.now() - 140000,
    dependencies: [],
    dependents: ['task-2', 'task-3'],
    logs: [
      {
        id: 'log-1',
        timestamp: Date.now() - 160000,
        level: 'info',
        message: 'Started data preprocessing',
      },
      {
        id: 'log-2',
        timestamp: Date.now() - 140000,
        level: 'info',
        message: 'Completed preprocessing 15,420 records',
      },
    ],
  },
  {
    id: 'task-2',
    constellationId: 'constellation-1',
    name: 'Feature Extraction',
    description: 'Extract features from preprocessed data',
    status: 'completed' as TaskStatus,
    deviceId: 'device-server',
    input: { processed_files: ['processed_data.parquet'] },
    output: { features: ['feature_matrix.npy'] },
    result: { success: true, feature_count: 128 },
    startedAt: Date.now() - 135000,
    completedAt: Date.now() - 110000,
    dependencies: ['task-1'],
    dependents: ['task-4'],
    logs: [
      {
        id: 'log-3',
        timestamp: Date.now() - 135000,
        level: 'info',
        message: 'Started feature extraction',
      },
      {
        id: 'log-4',
        timestamp: Date.now() - 110000,
        level: 'info',
        message: 'Extracted 128 features',
      },
    ],
  },
  {
    id: 'task-3',
    constellationId: 'constellation-1',
    name: 'Data Validation',
    description: 'Validate data quality and consistency',
    status: 'running' as TaskStatus,
    deviceId: 'device-desktop',
    input: { processed_files: ['processed_data.parquet'] },
    startedAt: Date.now() - 100000,
    dependencies: ['task-1'],
    dependents: ['task-5'],
    logs: [
      {
        id: 'log-5',
        timestamp: Date.now() - 100000,
        level: 'info',
        message: 'Started data validation',
      },
      {
        id: 'log-6',
        timestamp: Date.now() - 80000,
        level: 'info',
        message: 'Validating schema and constraints...',
      },
    ],
  },
  {
    id: 'task-4',
    constellationId: 'constellation-1',
    name: 'Model Training',
    description: 'Train ML model on extracted features',
    status: 'pending' as TaskStatus,
    deviceId: 'device-server',
    input: { features: ['feature_matrix.npy'] },
    dependencies: ['task-2'],
    dependents: ['task-5'],
    logs: [],
  },
  {
    id: 'task-5',
    constellationId: 'constellation-1',
    name: 'Results Aggregation',
    description: 'Aggregate and summarize final results',
    status: 'pending' as TaskStatus,
    input: {},
    dependencies: ['task-3', 'task-4'],
    dependents: [],
    logs: [],
  },
];

// Mock Constellation
export const mockConstellation: ConstellationSummary = {
  id: 'constellation-1',
  name: 'Data Processing Pipeline',
  status: 'running' as TaskStatus,
  description: 'Multi-device data processing and ML training pipeline',
  metadata: {
    owner: 'User',
    priority: 'high',
  },
  createdAt: Date.now() - 180000,
  updatedAt: Date.now() - 5000,
  taskIds: ['task-1', 'task-2', 'task-3', 'task-4', 'task-5'],
  dag: {
    nodes: [
      { id: 'task-1', label: 'Data Preprocessing', status: 'completed' as TaskStatus, deviceId: 'device-laptop' },
      { id: 'task-2', label: 'Feature Extraction', status: 'completed' as TaskStatus, deviceId: 'device-server' },
      { id: 'task-3', label: 'Data Validation', status: 'running' as TaskStatus, deviceId: 'device-desktop' },
      { id: 'task-4', label: 'Model Training', status: 'pending' as TaskStatus, deviceId: 'device-server' },
      { id: 'task-5', label: 'Results Aggregation', status: 'pending' as TaskStatus },
    ],
    edges: [
      { id: 'edge-1', source: 'task-1', target: 'task-2' },
      { id: 'edge-2', source: 'task-1', target: 'task-3' },
      { id: 'edge-3', source: 'task-2', target: 'task-4' },
      { id: 'edge-4', source: 'task-3', target: 'task-5' },
      { id: 'edge-5', source: 'task-4', target: 'task-5' },
    ],
  },
  statistics: {
    total: 5,
    pending: 2,
    running: 1,
    completed: 2,
    failed: 0,
  },
};

// Helper to load mock data into store
export const loadMockData = () => {
  return {
    messages: mockMessages,
    devices: mockDevices,
    tasks: mockTasks,
    constellation: mockConstellation,
  };
};
