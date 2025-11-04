# UFO³ Galaxy: Multi-Device Orchestration Framework

<p align="center">
  <em>A Novel Framework for Orchestrating Intelligent Agents Across Heterogeneous Devices and Platforms</em>
</p>

---

## 🌌 Overview

**UFO³ Galaxy** is a groundbreaking multi-device orchestration framework that extends single-device agent capabilities to coordinate workflows across heterogeneous platforms. Built on the **Constellation** metaphor, Galaxy decomposes complex user requests into executable DAG (Directed Acyclic Graph) workflows that intelligently distribute tasks to capable devices.

### 🎯 Core Innovation

Galaxy introduces three fundamental innovations for multi-device agent orchestration:

1. **🌟 Constellation Framework** - Task decomposition into DAG-based workflows with dependency management
2. **🎯 ConstellationAgent** - Intelligent task planning and dynamic device assignment via LLM-powered reasoning
3. **⚡ Dynamic Orchestration** - Real-time monitoring, adaptive execution, and automatic fault recovery

### 🔬 Research Foundation

Galaxy is based on the research presented in:
> **UFO³: Weaving the Digital Agent Galaxy**  
> Zhang, Chaoyun et al., 2025  
> arXiv preprint arXiv:[TBD]

**Key Contributions:**
- First multi-device orchestration framework specifically designed for GUI agents
- Novel Constellation-based task planning for cross-platform workflows
- Dynamic device assignment through capability-based matching
- Event-driven architecture for real-time adaptation and monitoring

---

## 🏗️ Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Natural Language Request                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Layer 1: Planning & Orchestration              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          ConstellationAgent (Planning Agent)              │  │
│  │  • LLM-powered task decomposition                        │  │
│  │  • DAG structure generation                              │  │
│  │  • Device requirement analysis                           │  │
│  │  • Dynamic constellation editing                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         TaskConstellation (DAG Workflow)                  │  │
│  │  • TaskStar nodes (individual tasks)                     │  │
│  │  • TaskStarLine edges (dependencies)                     │  │
│  │  • Cycle detection & validation                          │  │
│  │  • Topological sorting                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Layer 2: Device Management & Assignment             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Device Pool Manager                               │  │
│  │  • Device registration & discovery                       │  │
│  │  • Capability tracking (OS, resources, status)           │  │
│  │  • Health monitoring & heartbeat                         │  │
│  │  • Load balancing                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      Task Assignment Engine                               │  │
│  │  • Capability-based matching                             │  │
│  │  • Resource availability check                           │  │
│  │  • Performance history analysis                          │  │
│  │  • Dynamic reassignment on failure                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 Layer 3: Device Execution                        │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Windows   │  │    Linux    │  │    macOS    │  ...       │
│  │  Device     │  │   Device    │  │   Device    │            │
│  │   Agent     │  │    Agent    │  │    Agent    │            │
│  │  (UFO²)     │  │   (Shell)   │  │   (Shell)   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         ↓                ↓                ↓                      │
│  Platform-specific task execution on actual devices             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│             Cross-Cutting: Monitoring & Events                   │
│                                                                  │
│  • TaskOrchestrator: Parallel execution coordination            │
│  • Event System: Real-time status propagation                   │
│  • Observer Pattern: Live monitoring & visualization            │
│  • Fault Recovery: Automatic error detection & retry            │
└─────────────────────────────────────────────────────────────────┘
```

### 🔑 Key Components

#### 1. **ConstellationAgent** (Planning Layer)
- **Purpose**: Transforms user requests into executable DAG workflows
- **Capabilities**:
  - Natural language understanding via LLM integration
  - Task decomposition with dependency analysis
  - Device requirement specification
  - Dynamic constellation modification based on execution results
- **Implementation**: Extends `BasicAgent` with constellation-specific reasoning

#### 2. **TaskConstellation** (Workflow Representation)
- **Purpose**: DAG container for multi-device workflows
- **Components**:
  - **TaskStar**: Individual task nodes with metadata (device type, priority, timeout)
  - **TaskStarLine**: Dependency edges with conditional logic
  - **State Machine**: Tracks constellation lifecycle (CREATED → READY → EXECUTING → COMPLETED/FAILED)
- **Features**:
  - Cycle detection and validation
  - Topological sorting for execution order
  - JSON serialization for persistence

#### 3. **Device Pool Manager** (Device Layer)
- **Purpose**: Manages heterogeneous device fleet
- **Responsibilities**:
  - Device registration and discovery
  - Capability tracking (OS type, available resources)
  - Health monitoring via heartbeat mechanism
  - Load balancing and resource optimization
- **Supported Platforms**: Windows, Linux, macOS, Android (planned), Web (planned)

#### 4. **TaskOrchestrator** (Execution Layer)
- **Purpose**: Coordinates parallel task execution
- **Features**:
  - Dependency-aware scheduling
  - Parallel execution of independent tasks
  - Cross-device data flow management
  - Real-time progress tracking
  - Automatic fault detection and recovery

#### 5. **Event System** (Monitoring)
- **Purpose**: Real-time communication and monitoring
- **Architecture**: Observer pattern with typed events
- **Event Types**:
  - Task events (created, started, completed, failed)
  - Constellation events (created, modified, executed)
  - Device events (registered, connected, disconnected)
  - Session events (round start/end, status updates)

---

## 🚀 Getting Started

### Prerequisites

- **Python**: >= 3.10
- **Operating Systems**: 
  - Windows 10/11 (for Windows device agents)
  - Linux (Ubuntu 20.04+, for Linux device agents)
- **LLM API Access**: OpenAI, Azure OpenAI, or compatible providers

### Installation

```powershell
# Clone the UFO³ repository
git clone https://github.com/microsoft/UFO.git
cd UFO

# Create and activate conda environment (recommended)
conda create -n ufo3 python=3.10
conda activate ufo3

# Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Configuration

UFO³ Galaxy requires configuration at three levels: **Constellation Agent**, **Device Agents**, and **Device Pool**.

### Step 1: Configure Constellation Agent

The ConstellationAgent orchestrates the entire workflow. Configure its LLM provider:

```powershell
# Copy configuration template
copy config\galaxy\agents.yaml.template config\galaxy\agents.yaml

# Edit configuration
notepad config\galaxy\agents.yaml
```

**Example Configuration (`config/galaxy/agents.yaml`):**

```yaml
# Constellation Agent Configuration
CONSTELLATION_AGENT:
  API_TYPE: "openai"  # or "aoai" for Azure OpenAI
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-your-openai-api-key"
  API_MODEL: "gpt-4o"
  API_VERSION: "2024-02-15-preview"  # For Azure OpenAI
  
  # Agent behavior settings
  TEMPERATURE: 0.7
  MAX_TOKENS: 4000
  TOP_P: 0.9
  
  # Constellation-specific settings
  MAX_TASKS_PER_CONSTELLATION: 20
  MAX_DEPENDENCIES: 50
  ENABLE_DYNAMIC_EDITING: true
  RETRY_ON_VALIDATION_FAILURE: true

# Optional: Advanced settings
PLANNING:
  ENABLE_PARALLEL_PLANNING: true
  DEVICE_ASSIGNMENT_STRATEGY: "capability_based"  # or "round_robin", "load_balanced"
  FAULT_TOLERANCE_MODE: "auto_retry"  # or "manual", "skip"
```

### Step 2: Configure Device Agents

Each device that will execute tasks needs an agent configuration.

#### Windows Device Agent (UFO²)

```powershell
# Copy Windows agent template
copy config\ufo\agents.yaml.template config\ufo\agents.yaml

# Edit configuration
notepad config\ufo\agents.yaml
```

**Example (`config/ufo/agents.yaml`):**

```yaml
# Windows Device Agent Configuration (UFO²)
HOST_AGENT:
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-your-openai-api-key"
  API_MODEL: "gpt-4o"
  VISUAL_MODE: true

APP_AGENT:
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-your-openai-api-key"
  API_MODEL: "gpt-4o"
  VISUAL_MODE: true

# Device agent server settings
DEVICE_AGENT:
  SERVER_HOST: "0.0.0.0"
  SERVER_PORT: 8001
  DEVICE_NAME: "windows-workstation-01"
  DEVICE_TYPE: "WINDOWS"
```

#### Linux Device Agent

```bash
# Copy Linux agent template
cp config/galaxy/linux_agent.yaml.template config/galaxy/linux_agent.yaml

# Edit configuration
nano config/galaxy/linux_agent.yaml
```

**Example (`config/galaxy/linux_agent.yaml`):**

```yaml
# Linux Device Agent Configuration
DEVICE_AGENT:
  SERVER_HOST: "0.0.0.0"
  SERVER_PORT: 8002
  DEVICE_NAME: "linux-server-01"
  DEVICE_TYPE: "LINUX"
  
  # Linux-specific settings
  SHELL: "/bin/bash"
  ENABLE_SUDO: false
  WORKING_DIRECTORY: "/home/user/workspace"
  
  # Resource limits
  MAX_CONCURRENT_TASKS: 5
  MAX_MEMORY_MB: 4096
  MAX_CPU_PERCENT: 80
```

### Step 3: Configure Device Pool

Define the available devices in the device pool configuration:

```powershell
# Copy device pool template
copy config\galaxy\devices.yaml.template config\galaxy\devices.yaml

# Edit configuration
notepad config\galaxy\devices.yaml
```

**Example (`config/galaxy/devices.yaml`):**

```yaml
# Device Pool Configuration
devices:
  # Windows device
  - device_id: "windows-01"
    device_name: "Windows Workstation"
    device_type: "WINDOWS"
    connection:
      host: "localhost"
      port: 8001
      protocol: "websocket"
    capabilities:
      os_type: "Windows"
      os_version: "11"
      applications:
        - "Microsoft Office"
        - "Visual Studio Code"
        - "Microsoft Edge"
      resources:
        cpu_cores: 8
        memory_gb: 16
        storage_gb: 512
    status: "active"
    priority: 1
    
  # Linux device
  - device_id: "linux-01"
    device_name: "Linux Server"
    device_type: "LINUX"
    connection:
      host: "192.168.1.100"
      port: 8002
      protocol: "websocket"
    capabilities:
      os_type: "Linux"
      os_version: "Ubuntu 22.04"
      shell: "/bin/bash"
      installed_packages:
        - "python3"
        - "docker"
        - "git"
      resources:
        cpu_cores: 16
        memory_gb: 64
        storage_gb: 1024
    status: "active"
    priority: 2

# Global device pool settings
pool_settings:
  heartbeat_interval_seconds: 30
  connection_timeout_seconds: 10
  max_reconnect_attempts: 3
  enable_auto_discovery: false
  load_balancing_strategy: "capability_based"
```

---

## 🎬 Starting UFO³ Galaxy

### Step-by-Step Launch Sequence

#### Step 1: Start Device Agent Servers

Each device agent must be running and listening for task requests.

**On Windows Device:**
```powershell
# Navigate to UFO directory
cd C:\path\to\UFO

# Activate environment
conda activate ufo3

# Start Windows device agent server
python -m galaxy.device_agent.windows_server --port 8001
```

**On Linux Device:**
```bash
# Navigate to UFO directory
cd /path/to/UFO

# Activate environment
conda activate ufo3

# Start Linux device agent server
python -m galaxy.device_agent.linux_server --port 8002
```

**Expected Output:**
```
[INFO] Windows Device Agent Server starting...
[INFO] Device ID: windows-01
[INFO] Listening on: ws://0.0.0.0:8001
[INFO] Waiting for connections from Galaxy orchestrator...
```

#### Step 2: Start Device Agent Clients

Device agent clients register with the Galaxy orchestrator and maintain the connection.

**Terminal 1 (Windows Device Client):**
```powershell
python -m galaxy.device_agent.client --device-id windows-01 --orchestrator-host localhost --orchestrator-port 9000
```

**Terminal 2 (Linux Device Client):**
```bash
python -m galaxy.device_agent.client --device-id linux-01 --orchestrator-host 192.168.1.50 --orchestrator-port 9000
```

**Expected Output:**
```
[INFO] Device Agent Client starting...
[INFO] Device ID: windows-01
[INFO] Connecting to orchestrator at ws://localhost:9000
[INFO] ✓ Connected successfully
[INFO] ✓ Device registered with orchestrator
[INFO] Status: Ready to receive tasks
```

#### Step 3: Launch Galaxy Orchestrator

With devices connected, start the Galaxy orchestrator with your request.

**Single Request Mode:**
```powershell
python -m galaxy --request "Extract sales data from Excel on Windows, process it on Linux server, and generate a report"
```

**Interactive Mode:**
```powershell
python -m galaxy --interactive
```

**Custom Configuration:**
```powershell
python -m galaxy \
  --request "Your task description" \
  --session-name "data_pipeline_v1" \
  --max-rounds 15 \
  --config config/galaxy/custom_config.yaml
```

---

## 📊 Example Workflows

### Example 1: Cross-Platform Data Processing

**Request:**
```
"Download sales data from SharePoint on Windows, process it with Python on Linux server, 
and create a visualization dashboard"
```

**Generated Constellation:**
```
TaskConstellation: "Multi-Platform Data Pipeline"
├─ Task 1: download_data (Windows)
│  └─ Device: windows-01
│  └─ Agent: UFO² Desktop Agent
│  └─ Action: Navigate SharePoint, download Excel file
│
├─ Task 2: process_data (Linux) [depends on Task 1]
│  └─ Device: linux-01
│  └─ Agent: Linux Shell Agent
│  └─ Action: Run Python script for data processing
│
└─ Task 3: create_dashboard (Linux) [depends on Task 2]
   └─ Device: linux-01
   └─ Agent: Linux Shell Agent
   └─ Action: Generate visualization with matplotlib
```

**Execution Flow:**
1. ConstellationAgent decomposes request into 3 tasks
2. Task 1 assigned to Windows device (UFO² agent)
3. UFO² navigates SharePoint, downloads file, transfers to Linux
4. Task 2 starts on Linux after Task 1 completes
5. Python processing runs on Linux server
6. Task 3 generates dashboard
7. Results aggregated and returned to user

### Example 2: Distributed Testing Pipeline

**Request:**
```
"Run unit tests on Windows, integration tests on Linux, 
and deploy to staging server if all tests pass"
```

**Generated Constellation:**
```
TaskConstellation: "Distributed Test & Deploy"
├─ Task 1: unit_tests (Windows)
│  └─ Parallel execution: No dependencies
│
├─ Task 2: integration_tests (Linux)
│  └─ Parallel execution: No dependencies
│
└─ Task 3: deploy_staging (Linux) [depends on Task 1 AND Task 2]
   └─ Condition: Both tests must pass
   └─ Action: Deploy to staging environment
```

**Parallel Execution:**
- Task 1 and Task 2 execute simultaneously
- Task 3 waits for both to complete successfully
- Automatic failure handling if either test fails

### Example 3: Document Processing Workflow

**Request:**
```
"Extract text from PDFs on Windows, translate with API on Linux, 
and format results in Word on Windows"
```

**Generated Constellation:**
```
TaskConstellation: "Document Processing Pipeline"
├─ Task 1: extract_text (Windows)
│  └─ Device: windows-01
│  └─ Extract text from multiple PDF files
│
├─ Task 2: translate_text (Linux) [depends on Task 1]
│  └─ Device: linux-01
│  └─ Call translation API for each document
│
└─ Task 3: format_document (Windows) [depends on Task 2]
   └─ Device: windows-01
   └─ Create formatted Word document with translations
```

---

## 🎯 Advanced Features

### 1. Dynamic Constellation Editing

Galaxy can modify task workflows during execution based on intermediate results.

**Example:**
```python
# Initial request
"Process data and create visualization"

# After processing, agent detects data quality issues
# ConstellationAgent dynamically adds cleaning task:

TaskConstellation (Modified):
├─ Task 1: load_data (completed)
├─ Task 2: clean_data (added dynamically)  # NEW
├─ Task 3: process_data [updated dependencies]
└─ Task 4: visualize
```

**Configuration:**
```yaml
CONSTELLATION_AGENT:
  ENABLE_DYNAMIC_EDITING: true
  MAX_EDIT_ROUNDS: 3
  AUTO_APPROVE_EDITS: false  # Require user confirmation
```

### 2. Fault Tolerance & Recovery

Galaxy automatically handles device failures and network issues.

**Failure Scenarios:**
- **Device Disconnection**: Automatically reassign task to another capable device
- **Task Timeout**: Retry with increased timeout or skip based on configuration
- **Task Failure**: Retry with same or different device, or propagate failure

**Configuration:**
```yaml
FAULT_TOLERANCE:
  MAX_RETRIES: 3
  RETRY_STRATEGY: "exponential_backoff"
  RETRY_DELAY_SECONDS: 5
  ENABLE_AUTO_REASSIGNMENT: true
  FAIL_FAST: false  # Continue other tasks if one fails
```

### 3. Cross-Device Data Transfer

Galaxy manages data flow between devices automatically.

**Transfer Methods:**
- **Direct Transfer**: Device-to-device via network share
- **Orchestrator Relay**: Through central Galaxy orchestrator
- **Cloud Storage**: Via temporary cloud storage (S3, Azure Blob)

**Configuration:**
```yaml
DATA_TRANSFER:
  METHOD: "orchestrator_relay"  # or "direct", "cloud"
  TEMP_STORAGE_PATH: "/tmp/galaxy_transfer"
  MAX_TRANSFER_SIZE_MB: 100
  ENABLE_COMPRESSION: true
  ENABLE_ENCRYPTION: true
```

### 4. Load Balancing

Distribute tasks intelligently across devices based on current load.

**Strategies:**
- **Capability-based**: Match task requirements to device capabilities
- **Round-robin**: Distribute evenly across all devices
- **Load-balanced**: Assign to least busy device
- **Performance-based**: Prefer devices with best historical performance

**Configuration:**
```yaml
LOAD_BALANCING:
  STRATEGY: "capability_based"
  CONSIDER_CURRENT_LOAD: true
  CONSIDER_PERFORMANCE_HISTORY: true
  RESERVE_CAPACITY_PERCENT: 20  # Keep 20% capacity reserved
```

### 5. Real-Time Monitoring & Visualization

Monitor constellation execution in real-time with rich terminal visualization.

**Features:**
- **DAG Topology View**: Visual representation of task dependencies
- **Task Status Grid**: Color-coded task execution status
- **Progress Tracking**: Real-time completion percentage
- **Event Stream**: Live feed of task and device events

**Enable Visualization:**
```python
from galaxy import GalaxyClient

client = GalaxyClient(
    session_name="monitored_workflow",
    enable_visualization=True,
    visualization_config={
        "show_dag": True,
        "show_progress": True,
        "show_events": True,
        "update_interval_seconds": 1
    }
)
```

---

## 📈 Performance & Scalability

### Parallel Execution Benefits

Galaxy leverages DAG-based parallel execution for significant speedup:

**Sequential Execution (Traditional):**
```
Task 1 → Task 2 → Task 3 → Task 4
Total Time: T1 + T2 + T3 + T4
```

**Parallel Execution (Galaxy):**
```
Task 1 ──┬──> Task 3 ──> Task 4
         └──> Task 2 ──┘
Total Time: T1 + max(T2, T3) + T4
```

**Performance Gains:**
- **2-3x speedup** for independent tasks
- **Improved resource utilization** across device fleet
- **Reduced end-to-end latency** for complex workflows

### Scalability

Galaxy scales horizontally by adding more devices:

- **Device Fleet**: Support for 100+ heterogeneous devices
- **Concurrent Tasks**: Execute 50+ tasks simultaneously
- **Task Throughput**: Process 1000+ tasks per hour
- **Network Overhead**: Minimal with efficient event system

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Device Connection Failed

**Symptom:** Device agent cannot connect to orchestrator

**Solutions:**
```bash
# Check device agent is running
netstat -an | grep 8001

# Verify orchestrator is listening
netstat -an | grep 9000

# Check firewall settings
# Windows: Allow inbound on port 8001
# Linux: sudo ufw allow 8001

# Test connection
telnet localhost 8001
```

#### 2. Task Assignment Failed

**Symptom:** "No capable device found for task"

**Solutions:**
1. Check device capabilities in `devices.yaml`
2. Ensure device is registered and online
3. Verify task requirements match device capabilities
4. Check device resource availability

```python
# Debug device capabilities
from galaxy.client import ConstellationDeviceManager

manager = ConstellationDeviceManager()
devices = manager.get_all_devices()
for device in devices:
    print(f"{device.name}: {device.capabilities}")
```

#### 3. Constellation Validation Error

**Symptom:** "Constellation validation failed: Cycle detected"

**Solutions:**
1. Review task dependencies for circular references
2. Use ConstellationEditor to visualize DAG
3. Enable debug logging for detailed error messages

```python
# Validate constellation
is_valid, errors = constellation.validate()
if not is_valid:
    for error in errors:
        print(f"Validation Error: {error}")
```

### Debug Mode

Enable verbose logging for troubleshooting:

```powershell
# Set environment variable
$env:GALAXY_LOG_LEVEL="DEBUG"

# Or pass as argument
python -m galaxy --request "task" --log-level DEBUG
```

**Log Locations:**
- Constellation logs: `logs/galaxy/constellation/`
- Device agent logs: `logs/galaxy/devices/`
- Orchestrator logs: `logs/galaxy/orchestrator/`

---

## 📚 API Reference

### Python API

#### GalaxyClient

Main entry point for programmatic usage:

```python
from galaxy import GalaxyClient

# Initialize client
client = GalaxyClient(
    session_name="my_workflow",
    use_mock_agent=False,
    max_rounds=10,
    enable_visualization=True
)

# Execute single request
result = await client.execute_request(
    "Process data across multiple devices"
)

# Interactive mode
await client.start_interactive_session()

# Access constellation
constellation = client.session.constellation
print(f"Total tasks: {len(constellation.tasks)}")
```

#### TaskConstellation

Programmatic DAG creation and manipulation:

```python
from galaxy.constellation import TaskConstellation, TaskStar, TaskStarLine
from galaxy.core.types import DeviceType, TaskPriority

# Create constellation
constellation = TaskConstellation(
    name="Custom Workflow",
    description="Programmatically created workflow"
)

# Add tasks
task1 = TaskStar(
    task_id="task_1",
    name="Data Collection",
    device_type=DeviceType.WINDOWS,
    priority=TaskPriority.HIGH
)
constellation.add_task(task1)

task2 = TaskStar(
    task_id="task_2",
    name="Data Processing",
    device_type=DeviceType.LINUX
)
constellation.add_task(task2)

# Add dependency
dependency = TaskStarLine(
    from_task_id="task_1",
    to_task_id="task_2"
)
constellation.add_dependency(dependency)

# Validate
is_valid, errors = constellation.validate()
```

### Command Line API

```bash
# Basic execution
python -m galaxy --request "TASK_DESCRIPTION"

# Options
--request TEXT              # Task request
--session-name TEXT         # Custom session name
--max-rounds INTEGER        # Max execution rounds (default: 10)
--interactive              # Interactive mode
--mock-agent               # Use mock agent for testing
--config PATH              # Custom config file
--log-level LEVEL          # Logging level (DEBUG/INFO/WARNING/ERROR)
--output-dir PATH          # Output directory for logs
--enable-visualization     # Enable real-time visualization
--device-config PATH       # Device pool configuration file
```

---

## 🧪 Testing

### Run Tests

```bash
# All Galaxy tests
python -m pytest tests/galaxy/

# Specific modules
python -m pytest tests/galaxy/constellation/
python -m pytest tests/galaxy/agents/

# With coverage
python -m pytest --cov=galaxy tests/galaxy/

# Integration tests (requires running devices)
python -m pytest tests/galaxy/integration/ --integration
```

### Mock Testing

Use mock components for testing without real devices:

```python
from galaxy import GalaxyClient

# Mock mode
client = GalaxyClient(
    use_mock_agent=True,
    use_mock_devices=True
)

# Execute without real LLM or devices
result = await client.execute_request("Test task")
```

---

## 🤝 Contributing

Contributions to UFO³ Galaxy are welcome! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

**Areas for Contribution:**
- New device agent implementations (Android, iOS, Web)
- Enhanced fault tolerance strategies
- Performance optimizations
- Documentation improvements
- Test coverage expansion

---

## 📄 License

Copyright (c) Microsoft Corporation. Licensed under the MIT License.

See [LICENSE](../LICENSE) for details.

---

## 📖 Citation

If you use UFO³ Galaxy in your research, please cite:

```bibtex
@article{zhang2025ufo3,
  title   = {{UFO³: Weaving the Digital Agent Galaxy}},
  author  = {Zhang, Chaoyun and [Authors TBD]},
  journal = {arXiv preprint arXiv:[TBD]},
  year    = {2025}
}
```

---

## 🌟 Related Documentation

- **[UFO² Desktop AgentOS](../ufo/README.md)** - Windows device agent documentation
- **[Constellation Framework](./constellation/README.md)** - DAG management details
- **[Device Agents](./device_agent/README.md)** - Device agent implementation guide
- **[Event System](./core/README.md#event-system)** - Event-driven architecture
- **[Visualization](./visualization/README.md)** - Monitoring and visualization

---

<p align="center">
  <em>UFO³ Galaxy - Orchestrating Intelligence Across the Digital Universe</em> 🌌
</p>
