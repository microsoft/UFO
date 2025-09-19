# Constellation v2 Client

## Overview

The Constellation v2 Client provides a comprehensive solution for managing and orchestrating tasks across multiple UFO WebSocket servers. This implementation supports device registration, connection management, task distribution, and parallel execution across heterogeneous environments.

## Architecture

### Core Components

1. **ConstellationClient** - High-level orchestration interface
2. **ConstellationDeviceManager** - Device registration and connection management  
3. **ConstellationConfig** - Configuration loading and management

### Key Features

- **Multi-Device Registration**: Register and manage multiple UFO WebSocket servers
- **Local Client ID Mapping**: Support for multiple local clients per device
- **Device Info Retrieval**: Automatic device capability and metadata discovery
- **Task Distribution**: Intelligent task routing based on device capabilities
- **Parallel Execution**: Concurrent task execution across devices
- **Flexible Configuration**: File, CLI, and environment variable support
- **Event-Driven Architecture**: Hooks for connection, disconnection, and task completion
- **Robust Error Handling**: Automatic reconnection and error recovery

## Quick Start

### 1. Configuration Setup

Create a configuration file `constellation_config.json`:

```json
{
  "constellation_id": "my_constellation",
  "heartbeat_interval": 30.0,
  "reconnect_delay": 5.0,
  "max_concurrent_tasks": 8,
  "devices": [
    {
      "device_id": "windows_workstation",
      "server_url": "ws://192.168.1.100:8765",
      "local_client_ids": ["client_1", "client_2"],
      "capabilities": ["screenshot", "text_input", "app_control"],
      "metadata": {
        "os": "Windows",
        "location": "Office"
      },
      "auto_connect": true
    },
    {
      "device_id": "linux_server", 
      "server_url": "ws://192.168.1.101:8765",
      "local_client_ids": ["server_client"],
      "capabilities": ["terminal", "file_ops", "automation"],
      "metadata": {
        "os": "Linux",
        "role": "Server"
      },
      "auto_connect": true
    }
  ]
}
```

### 2. Basic Usage

```python
import asyncio
from ufo.constellation_v2.client import create_constellation_client

async def main():
    # Create and initialize client
    client = await create_constellation_client(
        config_file="constellation_config.json"
    )
    
    try:
        # Execute a simple task
        result = await client.execute_task("take a screenshot")
        print(f"Task result: {result}")
        
        # Execute task on specific device
        result = await client.execute_task(
            "open notepad",
            device_id="windows_workstation"
        )
        
        # Execute multiple tasks in parallel
        tasks = [
            {"request": "list files in Documents", "device_id": "windows_workstation"},
            {"request": "check disk usage", "device_id": "linux_server"}
        ]
        results = await client.execute_tasks_parallel(tasks)
        
        # Check device status
        status = client.get_device_status()
        print(f"Device status: {status}")
        
    finally:
        await client.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Manual Device Registration

```python
import asyncio
from ufo.constellation_v2.client import ConstellationClient

async def main():
    client = ConstellationClient(constellation_id="manual_constellation")
    
    # Register device manually
    success = await client.register_device(
        device_id="manual_device",
        server_url="ws://localhost:8765",
        local_client_ids=["client_1", "client_2"],
        capabilities=["automation", "screenshot"],
        metadata={"environment": "test"}
    )
    
    if success:
        print("Device registered successfully!")
        
        # Execute task
        result = await client.execute_task(
            "perform automation task",
            device_id="manual_device"
        )
        print(f"Result: {result}")
    
    await client.shutdown()

asyncio.run(main())
```

## Advanced Features

### Task Callbacks

```python
async def task_completion_callback(task_id, device_id, result):
    print(f"Task {task_id} completed on {device_id}: {result}")

# Execute task with callback
result = await client.execute_task(
    "long running task",
    callback=task_completion_callback
)
```

### Device Selection by Capabilities

```python
# Execute task on device with specific capabilities
result = await client.execute_task(
    "take screenshot",
    capabilities_required=["screenshot", "image_processing"]
)
```

### Parallel Task Execution

```python
# Execute multiple tasks with concurrency control
tasks = [
    {"request": "task 1", "device_id": "device1"},
    {"request": "task 2", "device_id": "device2"},
    {"request": "task 3"}  # Auto-select device
]

results = await client.execute_tasks_parallel(
    tasks, 
    max_concurrent=4
)
```

## Configuration Options

### ConstellationConfig Parameters

- `constellation_id`: Unique identifier for this constellation
- `heartbeat_interval`: Heartbeat interval in seconds (default: 30.0)
- `reconnect_delay`: Delay between reconnection attempts in seconds (default: 5.0)
- `max_concurrent_tasks`: Maximum concurrent tasks (default: 4)
- `devices`: List of device configurations

### DeviceConfig Parameters

- `device_id`: Unique device identifier
- `server_url`: UFO WebSocket server URL
- `local_client_ids`: List of local client IDs on the device
- `capabilities`: List of device capabilities
- `metadata`: Additional device metadata
- `auto_connect`: Whether to auto-connect on initialization (default: true)

## API Reference

### ConstellationClient

#### Core Methods

- `initialize()` - Initialize client and register devices
- `execute_task(request, device_id=None, ...)` - Execute single task
- `execute_tasks_parallel(tasks, max_concurrent=None)` - Execute multiple tasks
- `register_device(device_id, server_url, ...)` - Register device manually
- `get_device_status(device_id=None)` - Get device status
- `get_constellation_info()` - Get constellation information
- `shutdown()` - Shutdown client and disconnect devices

#### Event Handling

The client supports event handlers for:
- Device connection/disconnection
- Task completion
- Error handling

### ConstellationDeviceManager

#### Core Methods

- `register_device(device_id, server_url, ...)` - Register and connect device
- `assign_task_to_device(task_id, device_id, ...)` - Assign task to device
- `get_connected_devices()` - Get list of connected devices
- `get_device_info(device_id)` - Get device information
- `disconnect_device(device_id)` - Disconnect specific device

## Testing

Run the integration tests to verify functionality:

```bash
cd ufo/constellation_v2/client
python test_integration.py
```

The tests cover:
- Device registration and connection
- Configuration loading from files
- Task execution workflow
- Error handling and recovery

## Error Handling

The client implements comprehensive error handling:

- **Connection Failures**: Automatic reconnection with exponential backoff
- **Task Failures**: Error propagation and cleanup
- **Configuration Errors**: Validation and helpful error messages
- **WebSocket Errors**: Connection recovery and message retry

## Logging

Enable detailed logging for debugging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Integration with UFO

The Constellation v2 Client integrates seamlessly with UFO WebSocket servers:

1. **Server Registration**: Each UFO server runs on different devices
2. **Client ID Management**: Local client IDs are mapped and managed automatically
3. **Task Distribution**: Tasks are routed to appropriate devices based on capabilities
4. **Result Aggregation**: Results from multiple devices are collected and returned

## Performance Considerations

- Use appropriate `max_concurrent_tasks` settings based on device capabilities
- Configure `heartbeat_interval` based on network reliability
- Monitor device status regularly for optimal task distribution
- Use capability-based device selection for efficient resource utilization

## Troubleshooting

### Common Issues

1. **Connection Timeouts**: Check network connectivity and UFO server status
2. **Registration Failures**: Verify server URLs and local client IDs
3. **Task Execution Errors**: Check device capabilities and task compatibility
4. **Configuration Issues**: Validate JSON format and required fields

### Debug Mode

Enable debug logging to trace execution:

```python
import logging
logging.getLogger('ufo.constellation_v2').setLevel(logging.DEBUG)
```

## Future Enhancements

- Load balancing algorithms for device selection
- Advanced task scheduling and priority management
- Device health monitoring and metrics collection
- Integration with monitoring and alerting systems
- Support for device groups and hierarchical organization
