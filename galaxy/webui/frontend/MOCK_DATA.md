# Mock Data for Development

在开发模式下（`npm run dev`），WebUI 会自动加载 mock 数据，无需启动后端服务器即可预览完整的界面功能。

## 自动加载的 Mock 数据

### 1. **消息对话** (Messages)
- 6 条对话消息：用户和 Agent 的交互
- 包含多种消息类型：
  - User 消息（紫粉色图标）
  - Agent Response 消息（青蓝色 UFO 图标 + 步骤编号）
  - build_constellation 操作（5 个任务，4 个依赖）
  - execute_task 操作（运行中的任务）
- 展示完整的 thought、response 和 action 树结构

### 2. **设备列表** (Devices)
- 4 个模拟设备：
  - **MacBook Pro** (laptop) - 忙碌状态，CPU 85%
  - **Cloud Server** (server) - 忙碌状态，带 GPU，CPU 45%
  - **iPad Pro** (tablet) - 空闲状态，CPU 15%
  - **Desktop Workstation** - 已连接状态，CPU 30%
- 每个设备包含：
  - 实时资源使用率 (CPU/Memory/Disk)
  - 系统信息 (OS, hostname, IP)
  - 能力标签 (compute, storage, network, gpu)

### 3. **任务列表** (Tasks)
- 5 个任务展示完整的执行流程：
  1. **Data Preprocessing** ✅ 完成 (device-laptop)
  2. **Feature Extraction** ✅ 完成 (device-server)
  3. **Data Validation** 🔄 运行中 (device-desktop)
  4. **Model Training** ⏳ 待执行 (device-server)
  5. **Results Aggregation** ⏳ 待执行
- 包含依赖关系、日志、输入输出等完整信息
- 动态状态图标（旋转加载、脉冲时钟等）

### 4. **Constellation DAG**
- **Data Processing Pipeline** constellation
- 完整的 DAG 可视化：
  - 5 个节点按拓扑排序
  - 5 条边展示任务依赖关系
  - 节点状态用颜色和图标区分
  - 优化的布局算法（400px 列间距，动态行间距）
- 实时统计信息：
  - 总共 5 个任务
  - 2 个完成，1 个运行中，2 个待执行
  - 0 个失败

## 使用方法

### 开发模式
```bash
npm run dev
```
启动后会自动加载 mock 数据，无需任何配置。

### 生产模式
```bash
npm run build
npm run preview
```
生产构建不会加载 mock 数据，需要连接真实的后端 WebSocket。

## 实现细节

### 文件位置
- **Mock 数据定义**: `src/store/mockData.ts`
- **Store 集成**: `src/store/galaxyStore.ts`

### 检测机制
```typescript
const isDev = import.meta.env.DEV;
const mockData = isDev ? loadMockData() : null;
```

### 初始化时机
Store 创建时自动初始化：
- `messages: mockData?.messages || []`
- `tasks: mockData ? Object.fromEntries(mockData.tasks.map(t => [t.id, t])) : {}`
- `devices: mockData ? Object.fromEntries(mockData.devices.map(d => [d.id, d])) : {}`
- `constellations: mockData ? { [mockData.constellation.id]: mockData.constellation } : {}`
- `ui.activeConstellationId: mockData?.constellation.id || null`

## 调试和测试

Mock 数据非常适合以下场景：

1. **UI 开发**: 无需后端即可开发和调试前端组件
2. **样式调整**: 快速预览不同状态下的界面效果
3. **动画测试**: 测试状态图标、过渡动画等
4. **布局验证**: 验证响应式布局、固定宽度等
5. **性能优化**: 在已知数据集上测试渲染性能

## 自定义 Mock 数据

如需修改 mock 数据，编辑 `src/store/mockData.ts`：

```typescript
// 添加更多消息
export const mockMessages: Message[] = [
  // ... 添加你的消息
];

// 修改设备状态
export const mockDevices: Device[] = [
  {
    id: 'my-device',
    name: 'My Custom Device',
    status: 'busy',
    // ... 其他字段
  },
];

// 调整任务数量和依赖关系
export const mockTasks: Task[] = [
  // ... 你的任务配置
];
```

重新加载页面即可看到修改后的效果。
