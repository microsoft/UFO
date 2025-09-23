# Galaxy Client Module

The Client module manages device connectivity, task distribution, and multi-device coordination within the Galaxy Framework. It provides seamless integration between constellation execution and heterogeneous device environments.

## 📡 Overview

The Client module abstracts device management complexity, enabling Galaxy to execute tasks across various devices including desktops, mobile devices, servers, and IoT devices. It handles device discovery, capability matching, task assignment, and result aggregation.

## 🏗️ Architecture

```
ufo/galaxy/client/
├── __init__.py                     # Module exports
├── constellation_client.py         # Main client interface
├── device_manager.py              # Device discovery and management
├── task_distributor.py            # Task distribution logic
├── result_aggregator.py           # Result collection and processing
└── devices/                       # Device-specific implementations
    ├── __init__.py
    ├── base_device.py             # Abstract device base class
    ├── desktop_device.py          # Desktop device implementation
    ├── mobile_device.py           # Mobile device implementation
    ├── server_device.py           # Server device implementation
    └── web_device.py              # Web browser device implementation
```

## 📱 Core Components

### ConstellationClient

The main client interface that coordinates constellation execution across devices.

#### Key Responsibilities
- **Device Orchestration**: Coordinate task execution across multiple devices
- **Load Balancing**: Distribute tasks based on device capabilities and load
- **Result Aggregation**: Collect and consolidate results from distributed execution
- **Error Recovery**: Handle device failures and task redistribution
- **Performance Optimization**: Optimize task assignment for maximum throughput

#### Usage Example
```python
from ufo.galaxy.client import ConstellationClient
from ufo.galaxy.constellation import TaskConstellation

# Initialize client
client = ConstellationClient(
    enable_auto_discovery=True,
    max_concurrent_devices=5,
    load_balancing_strategy="capability_based"
)

# Discover and connect to devices
await client.discover_devices()
print(f"Connected to {len(client.get_connected_devices())} devices")

# Execute constellation across devices
constellation = TaskConstellation(name="Multi-Device Workflow")
execution_result = await client.execute_constellation(constellation)

print(f"Execution completed: {execution_result.success}")
print(f"Tasks distributed across {len(execution_result.device_assignments)} devices")
```

#### Key Methods
```python
class ConstellationClient:
    async def discover_devices(self) -> List[Device]
    async def connect_device(self, device: Device) -> bool
    async def disconnect_device(self, device_id: str) -> bool
    async def execute_constellation(self, constellation: TaskConstellation) -> ExecutionResult
    def assign_task(self, task: TaskStar, device: Device) -> bool
    def get_connected_devices(self) -> List[Device]
    def get_device_status(self, device_id: str) -> DeviceStatus
    async def redistribute_failed_tasks(self, failed_tasks: List[str]) -> bool
    def get_load_balancing_metrics(self) -> Dict[str, Any]
```

### DeviceManager

Manages device lifecycle, discovery, and capability tracking.

#### Device Management Features
- **Auto-Discovery**: Automatically discover compatible devices on the network
- **Capability Detection**: Analyze and track device capabilities
- **Health Monitoring**: Monitor device health and performance
- **Connection Management**: Handle device connections and disconnections
- **Resource Tracking**: Track device resource usage and availability

#### Usage Example
```python
from ufo.galaxy.client import DeviceManager, DeviceType

# Initialize device manager
device_manager = DeviceManager(
    discovery_methods=["network_scan", "bluetooth", "usb"],
    capability_detection=True,
    health_monitoring_interval=30
)

# Start device discovery
discovered_devices = await device_manager.discover_devices()

for device in discovered_devices:
    print(f"Device: {device.name}")
    print(f"  Type: {device.device_type}")
    print(f"  Capabilities: {device.capabilities}")
    print(f"  Status: {device.status}")

# Connect to specific devices
desktop_devices = device_manager.get_devices_by_type(DeviceType.DESKTOP)
await device_manager.connect_devices(desktop_devices)

# Monitor device health
health_report = device_manager.get_health_report()
print(f"Healthy devices: {health_report.healthy_count}")
print(f"Offline devices: {health_report.offline_count}")
```

#### Key Methods
```python
class DeviceManager:
    async def discover_devices(self) -> List[Device]
    async def connect_device(self, device: Device) -> bool
    async def disconnect_device(self, device_id: str) -> bool
    def get_device_capabilities(self, device_id: str) -> List[str]
    def get_devices_by_type(self, device_type: DeviceType) -> List[Device]
    def get_devices_by_capability(self, capability: str) -> List[Device]
    def monitor_device_health(self, device_id: str) -> DeviceHealthStatus
    def get_resource_usage(self, device_id: str) -> ResourceUsage
    def update_device_capabilities(self, device_id: str, capabilities: List[str])
```

### TaskDistributor

Intelligent task distribution engine that optimizes task assignment across devices.

#### Distribution Strategies
- **Capability-Based**: Assign tasks based on device capabilities
- **Load-Based**: Balance load across available devices
- **Proximity-Based**: Consider device proximity and network latency
- **Cost-Based**: Optimize for resource costs and efficiency
- **Hybrid**: Combine multiple strategies for optimal distribution

#### Usage Example
```python
from ufo.galaxy.client import TaskDistributor, DistributionStrategy

# Initialize task distributor
distributor = TaskDistributor(
    strategy=DistributionStrategy.HYBRID,
    load_balancing=True,
    enable_real_time_rebalancing=True
)

# Configure distribution parameters
distributor.set_distribution_config({
    "capability_weight": 0.4,
    "load_weight": 0.3,
    "proximity_weight": 0.2,
    "cost_weight": 0.1
})

# Distribute tasks
devices = device_manager.get_connected_devices()
tasks = constellation.get_executable_tasks()

distribution_plan = distributor.create_distribution_plan(tasks, devices)

for device_id, assigned_tasks in distribution_plan.assignments.items():
    print(f"Device {device_id}: {len(assigned_tasks)} tasks")

# Execute distribution
execution_results = await distributor.execute_distribution(distribution_plan)
```

#### Key Methods
```python
class TaskDistributor:
    def create_distribution_plan(self, tasks: List[TaskStar], devices: List[Device]) -> DistributionPlan
    async def execute_distribution(self, plan: DistributionPlan) -> DistributionResult
    def optimize_distribution(self, current_plan: DistributionPlan) -> DistributionPlan
    async def rebalance_tasks(self, threshold: float = 0.8) -> bool
    def get_distribution_metrics(self) -> DistributionMetrics
    def set_distribution_strategy(self, strategy: DistributionStrategy)
    def update_device_weights(self, device_weights: Dict[str, float])
```

### ResultAggregator

Collects and processes results from distributed task execution.

#### Aggregation Features
- **Result Collection**: Gather results from multiple devices
- **Data Validation**: Validate result integrity and consistency
- **Conflict Resolution**: Handle conflicting results from redundant execution
- **Performance Analysis**: Analyze execution performance across devices
- **Result Transformation**: Transform and normalize results

#### Usage Example
```python
from ufo.galaxy.client import ResultAggregator

# Initialize result aggregator
aggregator = ResultAggregator(
    enable_result_validation=True,
    conflict_resolution_strategy="majority_vote",
    enable_performance_analysis=True
)

# Collect results from distributed execution
execution_results = await client.execute_constellation(constellation)

# Aggregate and process results
aggregated_result = aggregator.aggregate_results(execution_results)

print(f"Total tasks executed: {aggregated_result.total_tasks}")
print(f"Successful tasks: {aggregated_result.successful_tasks}")
print(f"Failed tasks: {aggregated_result.failed_tasks}")
print(f"Average execution time: {aggregated_result.avg_execution_time}")

# Analyze performance by device
performance_analysis = aggregator.analyze_device_performance(execution_results)
for device_id, metrics in performance_analysis.items():
    print(f"Device {device_id}:")
    print(f"  Tasks completed: {metrics.tasks_completed}")
    print(f"  Average task time: {metrics.avg_task_time}")
    print(f"  Success rate: {metrics.success_rate}")
```

## 🖥️ Device Abstractions

### BaseDevice

Abstract base class for all device implementations.

```python
from abc import ABC, abstractmethod
from ufo.galaxy.client.devices import BaseDevice

class BaseDevice(ABC):
    def __init__(self, device_id: str, device_name: str):
        self.device_id = device_id
        self.device_name = device_name
        self.status = DeviceStatus.OFFLINE
        self.capabilities = []
        self.resource_usage = ResourceUsage()
        self.connection_info = {}
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to device"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to device"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: TaskStar) -> TaskResult:
        """Execute task on device"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get device capabilities"""
        pass
    
    @abstractmethod
    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage"""
        pass
```

### Desktop Device Implementation

Implementation for desktop/laptop devices.

```python
from ufo.galaxy.client.devices import DesktopDevice

class DesktopDevice(BaseDevice):
    def __init__(self, device_id: str, device_name: str, platform: str):
        super().__init__(device_id, device_name)
        self.platform = platform  # "windows", "macos", "linux"
        self.capabilities = self._detect_capabilities()
    
    def _detect_capabilities(self) -> List[str]:
        """Detect desktop-specific capabilities"""
        capabilities = ["file_operations", "gui_automation", "process_management"]
        
        # Platform-specific capabilities
        if self.platform == "windows":
            capabilities.extend(["powershell", "wmi", "registry"])
        elif self.platform == "macos":
            capabilities.extend(["applescript", "unix_tools"])
        elif self.platform == "linux":
            capabilities.extend(["bash", "unix_tools", "package_managers"])
        
        # Detect installed software
        if self._has_python():
            capabilities.append("python_execution")
        if self._has_docker():
            capabilities.append("containerization")
        
        return capabilities
    
    async def execute_task(self, task: TaskStar) -> TaskResult:
        """Execute task on desktop device"""
        try:
            if task.task_type == TaskType.FILE_OPERATION:
                return await self._execute_file_operation(task)
            elif task.task_type == TaskType.WEB_AUTOMATION:
                return await self._execute_web_automation(task)
            elif task.task_type == TaskType.DATA_PROCESSING:
                return await self._execute_data_processing(task)
            else:
                return await self._execute_generic_task(task)
        except Exception as e:
            return TaskResult(success=False, error=str(e))
```

### Mobile Device Implementation

Implementation for mobile devices (Android/iOS).

```python
from ufo.galaxy.client.devices import MobileDevice

class MobileDevice(BaseDevice):
    def __init__(self, device_id: str, device_name: str, platform: str):
        super().__init__(device_id, device_name)
        self.platform = platform  # "android", "ios"
        self.capabilities = self._detect_mobile_capabilities()
    
    def _detect_mobile_capabilities(self) -> List[str]:
        """Detect mobile-specific capabilities"""
        capabilities = ["app_automation", "touch_interaction", "camera", "sensors"]
        
        if self.platform == "android":
            capabilities.extend(["adb", "intent_handling", "package_management"])
        elif self.platform == "ios":
            capabilities.extend(["xcuitest", "shortcuts", "siri_integration"])
        
        return capabilities
    
    async def execute_task(self, task: TaskStar) -> TaskResult:
        """Execute task on mobile device"""
        if task.task_type == TaskType.APP_AUTOMATION:
            return await self._execute_app_automation(task)
        elif task.task_type == TaskType.DATA_COLLECTION:
            return await self._execute_data_collection(task)
        else:
            return TaskResult(
                success=False, 
                error=f"Task type {task.task_type} not supported on mobile"
            )
```

## 🌐 Multi-Device Coordination

### Device Communication

Communication protocols for device coordination.

```python
from ufo.galaxy.client import DeviceCommunicator

class DeviceCommunicator:
    def __init__(self):
        self.communication_protocols = {
            "http": HTTPCommunicator(),
            "websocket": WebSocketCommunicator(),
            "grpc": GRPCCommunicator(),
            "bluetooth": BluetoothCommunicator()
        }
    
    async def send_task(self, device: Device, task: TaskStar) -> bool:
        """Send task to device for execution"""
        protocol = self._select_protocol(device)
        return await protocol.send_task(device, task)
    
    async def receive_result(self, device: Device) -> TaskResult:
        """Receive task result from device"""
        protocol = self._select_protocol(device)
        return await protocol.receive_result(device)
    
    def _select_protocol(self, device: Device) -> CommunicationProtocol:
        """Select optimal communication protocol for device"""
        if device.supports_protocol("grpc"):
            return self.communication_protocols["grpc"]
        elif device.supports_protocol("websocket"):
            return self.communication_protocols["websocket"]
        else:
            return self.communication_protocols["http"]
```

### Synchronization and Coordination

Mechanisms for coordinating execution across devices.

```python
from ufo.galaxy.client import ExecutionCoordinator

class ExecutionCoordinator:
    def __init__(self):
        self.synchronization_points = {}
        self.execution_barriers = {}
        self.device_status = {}
    
    async def coordinate_execution(self, 
                                 constellation: TaskConstellation,
                                 devices: List[Device]) -> ExecutionResult:
        """Coordinate constellation execution across devices"""
        
        # Create execution plan
        execution_plan = self._create_execution_plan(constellation, devices)
        
        # Setup synchronization points
        self._setup_synchronization_points(execution_plan)
        
        # Execute with coordination
        return await self._execute_with_coordination(execution_plan)
    
    async def wait_for_synchronization_point(self, point_id: str) -> bool:
        """Wait for all devices to reach synchronization point"""
        barrier = self.execution_barriers.get(point_id)
        if barrier:
            await barrier.wait()
            return True
        return False
    
    def signal_synchronization_point(self, device_id: str, point_id: str):
        """Signal that device has reached synchronization point"""
        barrier = self.execution_barriers.get(point_id)
        if barrier:
            barrier.signal_device_ready(device_id)
```

## 📊 Performance and Monitoring

### Performance Optimization

Optimization strategies for multi-device execution.

```python
from ufo.galaxy.client import PerformanceOptimizer

class PerformanceOptimizer:
    def __init__(self):
        self.performance_history = {}
        self.optimization_strategies = [
            "load_balancing",
            "capability_matching",
            "network_optimization",
            "caching"
        ]
    
    def optimize_task_assignment(self, 
                               tasks: List[TaskStar],
                               devices: List[Device]) -> OptimizationPlan:
        """Optimize task assignment for maximum performance"""
        
        # Analyze historical performance
        performance_data = self._analyze_performance_history()
        
        # Generate optimization plan
        plan = OptimizationPlan()
        
        for task in tasks:
            best_device = self._find_optimal_device(task, devices, performance_data)
            plan.add_assignment(task, best_device)
        
        return plan
    
    def _find_optimal_device(self, 
                           task: TaskStar,
                           devices: List[Device],
                           performance_data: Dict) -> Device:
        """Find optimal device for task execution"""
        
        scores = {}
        for device in devices:
            score = self._calculate_device_score(task, device, performance_data)
            scores[device.device_id] = score
        
        best_device_id = max(scores, key=scores.get)
        return next(d for d in devices if d.device_id == best_device_id)
```

### Real-time Monitoring

Monitor execution across devices in real-time.

```python
from ufo.galaxy.client import ExecutionMonitor

class ExecutionMonitor:
    def __init__(self):
        self.monitoring_enabled = True
        self.metrics_collectors = {}
        self.alert_thresholds = {}
    
    async def start_monitoring(self, execution_id: str, devices: List[Device]):
        """Start monitoring execution across devices"""
        
        for device in devices:
            collector = self._create_metrics_collector(device)
            self.metrics_collectors[device.device_id] = collector
            await collector.start_collection()
    
    def get_real_time_metrics(self) -> Dict[str, DeviceMetrics]:
        """Get real-time metrics from all devices"""
        metrics = {}
        for device_id, collector in self.metrics_collectors.items():
            metrics[device_id] = collector.get_current_metrics()
        return metrics
    
    def check_performance_alerts(self) -> List[PerformanceAlert]:
        """Check for performance issues and generate alerts"""
        alerts = []
        
        for device_id, collector in self.metrics_collectors.items():
            metrics = collector.get_current_metrics()
            
            if metrics.cpu_usage > self.alert_thresholds.get("cpu", 90):
                alerts.append(PerformanceAlert(
                    device_id=device_id,
                    alert_type="high_cpu",
                    value=metrics.cpu_usage
                ))
            
            if metrics.memory_usage > self.alert_thresholds.get("memory", 85):
                alerts.append(PerformanceAlert(
                    device_id=device_id,
                    alert_type="high_memory",
                    value=metrics.memory_usage
                ))
        
        return alerts
```

## 🔧 Configuration

### Client Configuration

```python
client_config = {
    "discovery": {
        "auto_discovery": True,
        "discovery_methods": ["network_scan", "bluetooth", "usb"],
        "discovery_timeout_seconds": 30,
        "max_discovered_devices": 20
    },
    "connection": {
        "max_concurrent_connections": 10,
        "connection_timeout_seconds": 15,
        "retry_attempts": 3,
        "preferred_protocols": ["grpc", "websocket", "http"]
    },
    "distribution": {
        "strategy": "hybrid",
        "load_balancing": True,
        "capability_weight": 0.4,
        "load_weight": 0.3,
        "proximity_weight": 0.2,
        "cost_weight": 0.1
    },
    "monitoring": {
        "enable_real_time_monitoring": True,
        "metrics_collection_interval": 5,
        "performance_alerts": True,
        "alert_thresholds": {
            "cpu": 90,
            "memory": 85,
            "network": 95
        }
    }
}
```

### Device Configuration

```python
device_configs = {
    "desktop": {
        "max_concurrent_tasks": 5,
        "resource_limits": {
            "cpu_percentage": 80,
            "memory_mb": 8192
        },
        "capabilities": {
            "python_execution": True,
            "gui_automation": True,
            "file_operations": True
        }
    },
    "mobile": {
        "max_concurrent_tasks": 2,
        "resource_limits": {
            "cpu_percentage": 60,
            "memory_mb": 2048
        },
        "capabilities": {
            "app_automation": True,
            "camera": True,
            "sensors": True
        }
    }
}
```

## 🧪 Testing

### Client Testing

```python
from tests.galaxy.client import ClientTestHarness

# Comprehensive client testing
test_harness = ClientTestHarness()

# Test device discovery
discovery_tests = test_harness.test_device_discovery([
    "network_discovery",
    "bluetooth_discovery",
    "usb_discovery"
])

# Test task distribution
distribution_tests = test_harness.test_task_distribution([
    "capability_based_distribution",
    "load_based_distribution",
    "hybrid_distribution"
])

# Test execution coordination
coordination_tests = test_harness.test_execution_coordination([
    "parallel_execution",
    "synchronized_execution",
    "fault_tolerant_execution"
])
```

### Mock Devices

```python
from tests.galaxy.mocks import MockDevice, MockDeviceManager

# Create mock devices for testing
mock_desktop = MockDevice(
    device_id="mock_desktop_1",
    device_type=DeviceType.DESKTOP,
    capabilities=["python", "gui_automation"]
)

mock_mobile = MockDevice(
    device_id="mock_mobile_1",
    device_type=DeviceType.MOBILE,
    capabilities=["app_automation", "camera"]
)

# Mock device manager
mock_device_manager = MockDeviceManager()
mock_device_manager.add_mock_device(mock_desktop)
mock_device_manager.add_mock_device(mock_mobile)

# Test with mock devices
client = ConstellationClient(device_manager=mock_device_manager)
result = await client.execute_constellation(test_constellation)
```

## 🚀 Getting Started

### Basic Client Usage

```python
from ufo.galaxy.client import ConstellationClient
from ufo.galaxy.constellation import TaskConstellation

# Initialize client
client = ConstellationClient()

# Discover devices
devices = await client.discover_devices()
print(f"Found {len(devices)} devices")

# Create simple constellation
constellation = TaskConstellation(name="Simple Workflow")
# Add tasks to constellation...

# Execute across devices
result = await client.execute_constellation(constellation)
print(f"Execution success: {result.success}")
```

### Advanced Client Usage

```python
from ufo.galaxy.client import (
    ConstellationClient, DeviceManager, 
    TaskDistributor, DistributionStrategy
)

# Setup advanced client with custom configuration
device_manager = DeviceManager(
    discovery_methods=["network_scan", "bluetooth"],
    health_monitoring_interval=30
)

task_distributor = TaskDistributor(
    strategy=DistributionStrategy.HYBRID,
    load_balancing=True
)

client = ConstellationClient(
    device_manager=device_manager,
    task_distributor=task_distributor,
    enable_real_time_monitoring=True
)

# Execute with advanced features
await client.discover_devices()
execution_result = await client.execute_constellation(
    constellation,
    execution_config={
        "enable_fault_tolerance": True,
        "max_retries": 3,
        "enable_load_balancing": True
    }
)
```

## 🔗 Integration

The client module coordinates with all Galaxy components:

- **[Agents](../agents/README.md)**: Receive constellations for device execution
- **[Constellation](../constellation/README.md)**: Execute task DAGs across devices
- **[Session](../session/README.md)**: Integrate with session lifecycle management
- **[Core](../core/README.md)**: Use events and interfaces for communication
- **[Visualization](../visualization/README.md)**: Provide execution monitoring data

---

*Seamless multi-device orchestration that brings Galaxy workflows to life* 📡
