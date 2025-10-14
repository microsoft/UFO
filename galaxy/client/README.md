# Galaxy Client Module

The Client module provides device management and connection capabilities for the Galaxy Framework. It serves as a support component focused on device registration, connection management, and basic task execution through WebSocket communication with UFO servers.

## 📡 Overview

The Client module is designed as a **device management support component** for the Galaxy Framework. It handles device registration, WebSocket connections, heartbeat monitoring, and basic task execution. For complex DAG orchestration and multi-task workflows, the main `GalaxyClient` should be used instead.

### Key Capabilities
- **Device Registration**: Register and manage UFO WebSocket server connections
- **Connection Management**: Establish and maintain WebSocket connections with devices
- **Configuration Support**: Load device configurations from JSON/YAML files
- **Heartbeat Monitoring**: Monitor device health and connectivity
- **Basic Task Execution**: Execute simple tasks on connected devices

## 🏗️ Architecture

```
ufo/galaxy/client/
├── __init__.py                     # Module exports and version
├── constellation_client.py         # Main client interface for device management
├── device_manager.py              # Core device management coordinator
├── config_loader.py               # Configuration loading (JSON/YAML/CLI/env)
├── components/                     # Modular device management components
│   ├── __init__.py                # Component exports
│   ├── types.py                   # Type definitions and enums
│   ├── device_registry.py         # Device registration and information
│   ├── connection_manager.py      # WebSocket connection management
│   ├── heartbeat_manager.py       # Device health monitoring
│   ├── event_manager.py           # Event handling and callbacks
│   └── message_processor.py       # Message routing and processing
└── orchestration/                 # Client orchestration components
    ├── __init__.py                # Orchestration exports
    ├── client_event_handler.py    # Event handling for client operations
    ├── status_manager.py          # Status reporting and management
    └── client_config_manager.py   # Configuration-based initialization
```

## 📱 Core Components

### ConstellationClient

The main client interface for device management and basic task execution. **This is primarily a device management support component** - for complex DAG orchestration, use the main `GalaxyClient` instead.

#### Key Responsibilities
- **Device Registration**: Register UFO WebSocket servers with configuration support
- **Connection Management**: Establish and maintain WebSocket connections
- **Configuration Loading**: Load device configurations from files, CLI, or environment
- **Status Monitoring**: Track device connectivity and health status
- **Basic Task Interface**: Execute simple tasks on connected devices

#### Usage Example
```python
from galaxy.client import ConstellationClient, ConstellationConfig

# Initialize from configuration file
config = ConstellationConfig.from_file("config/devices.json")
client = ConstellationClient(config=config)

# Initialize and connect to configured devices
results = await client.initialize()
print(f"Device registration results: {results}")

# Check connected devices
connected_devices = client.get_connected_devices()
print(f"Connected to {len(connected_devices)} devices: {connected_devices}")

# Get constellation info
info = client.get_constellation_info()
print(f"Constellation: {info['constellation_id']}")
print(f"Connected: {info['connected_devices']}/{info['total_devices']}")

# Add a new device dynamically
await client.add_device_to_config(
    device_id="new_laptop",
    server_url="ws://192.168.1.105:5000/ws",
    capabilities=["web_browsing", "file_management"],
    register_immediately=True
)
```

#### Key Methods
```python
class ConstellationClient:
    # Initialization and Configuration
    async def initialize(self) -> Dict[str, bool]
    async def register_device(self, device_id: str, server_url: str, ...) -> bool
    async def register_device_from_config(self, device_config: DeviceConfig) -> bool
    
    # Device Connection Management  
    async def connect_device(self, device_id: str) -> bool
    async def disconnect_device(self, device_id: str) -> bool
    async def connect_all_devices(self) -> Dict[str, bool]
    async def disconnect_all_devices(self) -> None
    
    # Status and Information
    def get_device_status(self, device_id: Optional[str] = None) -> Dict[str, Any]
    def get_connected_devices(self) -> List[str]
    def get_constellation_info(self) -> Dict[str, Any]
    
    # Configuration Management
    def validate_config(self, config: Optional[ConstellationConfig] = None) -> Dict[str, Any]
    def get_config_summary(self) -> Dict[str, Any]
    async def add_device_to_config(self, device_id: str, server_url: str, ...) -> bool
    
    # Lifecycle
    async def shutdown(self) -> None
```

### ConstellationDeviceManager

Core coordinator for device management using modular components. This class delegates responsibilities to focused components for clean separation of concerns.

#### Architecture Components
- **DeviceRegistry**: Device registration and information management
- **WebSocketConnectionManager**: WebSocket connection establishment and management
- **HeartbeatManager**: Device health monitoring through periodic heartbeats
- **EventManager**: Event handling and callback management
- **MessageProcessor**: Message routing and processing for WebSocket communication

#### Usage Example
```python
from galaxy.client.device_manager import ConstellationDeviceManager

# Initialize device manager
device_manager = ConstellationDeviceManager(
    constellation_id="my_constellation",
    heartbeat_interval=30.0,
    reconnect_delay=5.0
)

# Register a UFO WebSocket server device
success = await device_manager.register_device(
    device_id="windows_laptop",
    server_url="ws://192.168.1.100:5000/ws",
    capabilities=["web_browsing", "file_operations", "gui_automation"],
    metadata={"os": "windows", "location": "office"},
    auto_connect=True
)

# Execute a task on the device
result = await device_manager.assign_task_to_device(
    task_id="screenshot_task",
    device_id="windows_laptop", 
    task_description="take a screenshot of the desktop",
    task_data={"format": "png", "quality": "high"},
    timeout=60.0
)

# Monitor device status
device_info = device_manager.get_device_info("windows_laptop")
print(f"Device status: {device_info.status}")
print(f"Capabilities: {device_info.capabilities}")

# Register event handlers
def on_device_connected(device_id, device_info):
    print(f"Device {device_id} connected successfully")

device_manager.add_connection_handler(on_device_connected)
```

#### Key Methods
```python
class ConstellationDeviceManager:
    # Device Registration and Connection
    async def register_device(self, device_id: str, server_url: str, ...) -> bool
    async def connect_device(self, device_id: str) -> bool
    async def disconnect_device(self, device_id: str) -> None
    
    # Task Execution
    async def assign_task_to_device(self, task_id: str, device_id: str, ...) -> Dict[str, Any]
    async def execute_task_direct(self, task_id: str, device_id: str, ...) -> Dict[str, Any]
    
    # Event Handling
    def add_connection_handler(self, handler: Callable) -> None
    def add_disconnection_handler(self, handler: Callable) -> None
    def add_task_completion_handler(self, handler: Callable) -> None
    
    # Device Information
    def get_device_info(self, device_id: str) -> Optional[AgentProfile]
    def get_connected_devices(self) -> List[str]
    def get_device_capabilities(self, device_id: str) -> Dict[str, Any]
    def get_device_status(self, device_id: str) -> Dict[str, Any]
    def get_all_devices(self) -> Dict[str, AgentProfile]
    
    # Lifecycle
    async def shutdown(self) -> None
```

### ConstellationConfig

Configuration management system that supports loading device configurations from multiple sources including JSON files, YAML files, command line arguments, and environment variables.

#### Configuration Sources
- **JSON Files**: Load from JSON configuration files
- **YAML Files**: Load from YAML configuration files (requires PyYAML)
- **Command Line**: Parse device configurations from CLI arguments
- **Environment Variables**: Load from environment variables
- **Programmatic**: Create configurations in code

#### Usage Example
```python
from galaxy.client import ConstellationConfig, DeviceConfig

# Load from configuration file
config = ConstellationConfig.from_file("config/constellation.json")
print(f"Loaded {len(config.devices)} devices from config")

# Create configuration programmatically
config = ConstellationConfig(
    constellation_id="my_constellation",
    heartbeat_interval=30.0,
    max_concurrent_tasks=8
)

# Add devices to configuration
config.add_device(
    device_id="laptop_001", 
    server_url="ws://192.168.1.100:5000/ws",
    capabilities=["web_browsing", "file_operations"],
    metadata={"os": "windows", "location": "office"}
)

# Save configuration
config.to_file("config/saved_constellation.json")

# Validate configuration
validation = config.validate_config()
if not validation["valid"]:
    print(f"Configuration errors: {validation['errors']}")
```

#### Configuration Structure
```python
@dataclass
class DeviceConfig:
    device_id: str
    server_url: str
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    auto_connect: bool = True
    max_retries: int = 5

@dataclass 
class ConstellationConfig:
    constellation_id: str = "constellation_orchestrator"
    heartbeat_interval: float = 30.0
    reconnect_delay: float = 5.0
    max_concurrent_tasks: int = 10
    devices: List[DeviceConfig] = field(default_factory=list)
```

## � Modular Components

The device manager delegates responsibilities to focused components for clean separation of concerns:

### Device Registry
Manages device registration, information storage, and status tracking.

```python
from galaxy.client.components import DeviceRegistry, DeviceStatus

registry = DeviceRegistry()

# Register a device
device_info = registry.register_device(
    device_id="laptop_001",
    server_url="ws://192.168.1.100:5000/ws", 
    capabilities=["web_browsing", "file_operations"],
    metadata={"os": "windows"}
)

# Check registration and status
is_registered = registry.is_device_registered("laptop_001")
device = registry.get_device("laptop_001")
connected_devices = registry.get_connected_devices()
```

### WebSocket Connection Manager
Handles WebSocket connections to UFO servers.

```python
from galaxy.client.components import WebSocketConnectionManager

connection_manager = WebSocketConnectionManager(constellation_id="my_constellation")

# Connect to device
websocket = await connection_manager.connect_to_device(device_info)

# Send task to device
task_request = TaskRequest(
    task_id="screenshot_001",
    device_id="laptop_001", 
    request="take a screenshot",
    timeout=60.0
)
result = await connection_manager.send_task_to_device("laptop_001", task_request)
```

### Heartbeat Manager
Monitors device health through periodic heartbeat messages.

```python
from galaxy.client.components import HeartbeatManager

heartbeat_manager = HeartbeatManager(
    connection_manager=connection_manager,
    device_registry=registry,
    heartbeat_interval=30.0
)

# Start heartbeat for a device
heartbeat_manager.start_heartbeat("laptop_001")

# Check if device is responsive
is_responsive = heartbeat_manager.is_device_responsive("laptop_001")
```

### Event Manager
Handles event callbacks and notifications.

```python
from galaxy.client.components import EventManager

event_manager = EventManager()

# Register event handlers
def on_device_connected(device_id, device_info):
    print(f"Device {device_id} connected successfully")

def on_task_completed(device_id, task_id, result):
    print(f"Task {task_id} completed on {device_id}")

event_manager.add_connection_handler(on_device_connected)
event_manager.add_task_completion_handler(on_task_completed)
```

### Message Processor
Routes and processes WebSocket messages.

```python
from galaxy.client.components import MessageProcessor

message_processor = MessageProcessor(
    device_registry=registry,
    heartbeat_manager=heartbeat_manager,
    event_manager=event_manager
)

# Start message handling for a device
message_processor.start_message_handler(device_id="laptop_001", websocket=websocket)

# Stop message handling
message_processor.stop_message_handler("laptop_001")
```

## 📊 Types and Data Structures

The client module uses well-defined types for type safety and clear interfaces:

### Core Types

```python
from galaxy.client.components import DeviceStatus, AgentProfile, TaskRequest

# Device Status Enumeration
class DeviceStatus(Enum):
    OFFLINE = "offline"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"

# Device Information
@dataclass
class AgentProfile:
    device_id: str
    server_url: str
    status: DeviceStatus = DeviceStatus.OFFLINE
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_heartbeat: Optional[datetime] = None
    connection_attempts: int = 0
    max_retries: int = 5

# Task Request Structure
@dataclass
class TaskRequest:
    task_id: str
    device_id: str
    request: str
    task_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 300.0
```

### Event Handling

```python
from typing import Protocol

class DeviceEventHandler(Protocol):
    """Protocol for device event handlers"""
    
    async def on_device_connected(self, device_id: str, device_info: AgentProfile) -> None:
        """Called when a device connects"""
        ...
    
    async def on_device_disconnected(self, device_id: str) -> None:
        """Called when a device disconnects"""
        ...
    
    async def on_task_completed(self, device_id: str, task_id: str, result: Dict[str, Any]) -> None:
        """Called when a task completes"""
        ...
```

## 🔧 Configuration

### JSON Configuration File

```json
{
    "constellation_id": "main_constellation",
    "heartbeat_interval": 30.0,
    "reconnect_delay": 5.0,
    "max_concurrent_tasks": 10,
    "devices": [
        {
            "device_id": "laptop_001",
            "server_url": "ws://192.168.1.100:5000/ws",
            "capabilities": ["web_browsing", "file_operations", "gui_automation"],
            "metadata": {
                "os": "windows",
                "location": "office",
                "performance": "medium"
            },
            "auto_connect": true,
            "max_retries": 5
        },
        {
            "device_id": "workstation_002", 
            "server_url": "ws://192.168.1.101:5000/ws",
            "capabilities": ["software_development", "data_analysis", "heavy_compute"],
            "metadata": {
                "os": "windows",
                "location": "lab", 
                "performance": "high"
            },
            "auto_connect": true,
            "max_retries": 3
        }
    ]
}
```

### YAML Configuration File

```yaml
constellation_id: main_constellation
heartbeat_interval: 30.0
reconnect_delay: 5.0
max_concurrent_tasks: 10

devices:
  - device_id: laptop_001
    server_url: ws://192.168.1.100:5000/ws
    capabilities:
      - web_browsing
      - file_operations
      - gui_automation
    metadata:
      os: windows
      location: office
      performance: medium
    auto_connect: true
    max_retries: 5

  - device_id: workstation_002
    server_url: ws://192.168.1.101:5000/ws
    capabilities:
      - software_development
      - data_analysis
      - heavy_compute
    metadata:
      os: windows
      location: lab
      performance: high
    auto_connect: true
    max_retries: 3
```

### Command Line Configuration

```bash
# Create sample configuration
python -m ufo.galaxy.client.config_loader --create-sample-config config/sample.json

# Load from configuration file
python -m ufo.galaxy.client.config_loader --config config/constellation.json

# Add devices via command line
python -m ufo.galaxy.client.config_loader \
    --constellation-id "my_constellation" \
    --device laptop_001:ws://192.168.1.100:5000/ws \
    --device workstation_002:ws://192.168.1.101:5000/ws \
    --heartbeat-interval 30 \
    --max-concurrent-tasks 8
```

## 🧪 Testing and Development

### Unit Testing

The client module includes comprehensive unit tests for all components:

```python
import pytest
from galaxy.client import ConstellationClient, ConstellationConfig, DeviceConfig

@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization and device registration"""
    config = ConstellationConfig(constellation_id="test_constellation")
    config.add_device(
        device_id="test_device",
        server_url="ws://localhost:5000/ws",
        capabilities=["test_capability"]
    )
    
    client = ConstellationClient(config=config)
    assert client.config.constellation_id == "test_constellation"
    assert len(client.config.devices) == 1

@pytest.mark.asyncio  
async def test_device_manager_operations():
    """Test device manager core operations"""
    from galaxy.client.device_manager import ConstellationDeviceManager
    
    manager = ConstellationDeviceManager(constellation_id="test")
    
    # Test device registration
    success = await manager.register_device(
        device_id="test_device",
        server_url="ws://localhost:5000/ws",
        auto_connect=False
    )
    
    # Verify registration
    device_info = manager.get_device_info("test_device")
    assert device_info is not None
    assert device_info.device_id == "test_device"
```

### Configuration Testing

```python
def test_configuration_loading():
    """Test configuration loading from different sources"""
    
    # Test JSON loading
    config = ConstellationConfig.from_json("config/test_config.json")
    assert config.constellation_id is not None
    
    # Test programmatic configuration
    config = ConstellationConfig(constellation_id="test")
    config.add_device("device1", "ws://localhost:5000/ws")
    
    # Test validation
    validation = config.validate_config()
    assert validation["valid"] == True
```

## 🚀 Getting Started

### Basic Client Usage

```python
from galaxy.client import ConstellationClient, ConstellationConfig

# Method 1: Load from configuration file
config = ConstellationConfig.from_file("config/constellation.json")
client = ConstellationClient(config=config)

# Initialize and connect to devices
results = await client.initialize()
print(f"Device registration results: {results}")

# Check connected devices
connected_devices = client.get_connected_devices()
print(f"Connected to {len(connected_devices)} devices")

# Get status information
info = client.get_constellation_info()
print(f"Constellation: {info['constellation_id']}")
print(f"Connected: {info['connected_devices']}/{info['total_devices']}")
```

### Manual Device Management

```python
from galaxy.client import ConstellationClient

# Initialize client without configuration
client = ConstellationClient(constellation_id="manual_constellation")

# Register devices manually
await client.register_device(
    device_id="laptop_001",
    server_url="ws://192.168.1.100:5000/ws",
    capabilities=["web_browsing", "file_operations"],
    auto_connect=True
)

await client.register_device(
    device_id="workstation_002", 
    server_url="ws://192.168.1.101:5000/ws",
    capabilities=["software_development", "data_analysis"],
    auto_connect=True
)

# Connect to all devices
connection_results = await client.connect_all_devices()
print(f"Connection results: {connection_results}")
```

### Direct Device Manager Usage

```python
from galaxy.client.device_manager import ConstellationDeviceManager

# Initialize device manager directly
device_manager = ConstellationDeviceManager(
    constellation_id="direct_manager",
    heartbeat_interval=30.0
)

# Register and connect device
await device_manager.register_device(
    device_id="test_device",
    server_url="ws://localhost:5000/ws",
    capabilities=["gui_automation"],
    auto_connect=True
)

# Execute a simple task
result = await device_manager.assign_task_to_device(
    task_id="simple_task",
    device_id="test_device",
    task_description="take a screenshot",
    task_data={"format": "png"},
    timeout=60.0
)

print(f"Task result: {result}")
```

### Configuration Management

```python
from galaxy.client import ConstellationConfig

# Create sample configuration
ConstellationConfig.create_sample_config("config/sample.json")

# Load and modify configuration
config = ConstellationConfig.from_file("config/sample.json")
config.add_device(
    device_id="new_device",
    server_url="ws://192.168.1.105:5000/ws",
    capabilities=["custom_capability"]
)

# Save modified configuration
config.to_file("config/modified.json")

# Validate configuration
validation = config.validate_config()
if not validation["valid"]:
    print(f"Configuration errors: {validation['errors']}")
```

## 🔗 Integration with Galaxy Framework

The Client module serves as a **device management support component** within the broader Galaxy Framework:

### Role in Galaxy Architecture
- **Primary Purpose**: Device registration, connection management, and basic task execution
- **Integration Point**: Provides device connectivity for the main `GalaxyClient` system
- **Scope**: Handles WebSocket connections to UFO servers, not complex DAG orchestration

### Integration with Other Components

- **[Constellation](../constellation/README.md)**: Provides devices for task execution in DAG workflows
- **[Session](../session/README.md)**: Integrates with session lifecycle for device-aware workflows  
- **[Agents](../agents/README.md)**: Supports ConstellationAgent with device connectivity
- **[Core](../core/README.md)**: Uses core types, events, and interfaces
- **[Visualization](../visualization/README.md)**: Provides device status for monitoring dashboards

### Recommended Usage Pattern

For **simple device management**:
```python
from galaxy.client import ConstellationClient
client = ConstellationClient()
# Use for device registration and basic tasks
```

For **complex DAG workflows**:
```python
from galaxy import GalaxyClient  # Main framework entry point
galaxy = GalaxyClient()
# Use for full constellation orchestration
```

## 📝 Summary

The Galaxy Client module provides essential device management capabilities:

- ✅ **Device Registration**: Register UFO WebSocket servers with configuration support
- ✅ **Connection Management**: Establish and maintain WebSocket connections  
- ✅ **Configuration Loading**: Support for JSON, YAML, CLI, and environment configuration
- ✅ **Health Monitoring**: Heartbeat monitoring and reconnection handling
- ✅ **Modular Architecture**: Clean separation of concerns through focused components
- ✅ **Event System**: Callback support for device and task events
- ✅ **Basic Task Execution**: Simple task execution interface

**Important Note**: This module is designed as a support component. For full Galaxy Framework capabilities including AI agents, DAG orchestration, and complex workflows, use the main `GalaxyClient` from the root Galaxy package.

---

*Device management foundation for Galaxy's intelligent task orchestration* 📡
