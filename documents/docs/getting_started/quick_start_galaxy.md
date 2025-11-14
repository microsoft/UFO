# Quick Start Guide - UFO³ Galaxy

Welcome to **UFO³ Galaxy** – the Multi-Device AgentOS! This guide will help you orchestrate complex cross-platform workflows across multiple devices in just a few steps.

**What is UFO³ Galaxy?**

UFO³ Galaxy is a multi-tier orchestration framework that coordinates distributed agents across Windows and Linux devices. It enables complex workflows that span multiple machines, combining desktop automation, server operations, and heterogeneous device capabilities into unified task execution.

---

## 🛠️ Step 1: Installation

### Requirements

- **Python** >= 3.10
- **Windows OS** >= 10 (for Windows agents)
- **Linux** (for Linux agents)
- **Git** (for cloning the repository)
- **Network connectivity** between all devices

### Installation Steps

```powershell
# [Optional] Create conda environment
conda create -n ufo python=3.10
conda activate ufo

# Clone the repository
git clone https://github.com/microsoft/UFO.git
cd UFO

# Install dependencies
pip install -r requirements.txt
```

> **💡 Tip:** If you want to use Qwen as your LLM, uncomment the related libraries in `requirements.txt` before installing.

---

## ⚙️ Step 2: Configure ConstellationAgent LLM

UFO³ Galaxy uses a **ConstellationAgent** that orchestrates all device agents. You need to configure its LLM settings.

### Configure Constellation Agent

```powershell
# Copy template to create constellation agent config
copy config\galaxy\agent.yaml.template config\galaxy\agent.yaml
notepad config\galaxy\agent.yaml   # Edit your LLM API credentials
```

**Configuration File Location:**
```
config/galaxy/
├── agent.yaml.template    # Template - COPY THIS
├── agent.yaml             # Your config with API keys (DO NOT commit)
└── devices.yaml           # Device pool configuration (Step 4)
```

### LLM Configuration Examples

#### Azure OpenAI Configuration

**Edit `config/galaxy/agent.yaml`:**

```yaml
CONSTELLATION_AGENT:
  REASONING_MODEL: false
  API_TYPE: "aoai"
  API_BASE: "https://YOUR_RESOURCE.openai.azure.com"
  API_KEY: "YOUR_AOAI_KEY"
  API_VERSION: "2024-02-15-preview"
  API_MODEL: "gpt-4o"
  API_DEPLOYMENT_ID: "YOUR_DEPLOYMENT_ID"
```

> **ℹ️ More LLM Options:** Galaxy supports various LLM providers including Qwen, Gemini, Claude, DeepSeek, and more. See the [Model Configuration Guide](../configuration/models/overview.md) for complete details.

---
  
  # Prompt configurations (use defaults)
  CONSTELLATION_CREATION_PROMPT: "galaxy/prompts/constellation/share/constellation_creation.yaml"
  CONSTELLATION_EDITING_PROMPT: "galaxy/prompts/constellation/share/constellation_editing.yaml"
  CONSTELLATION_CREATION_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_creation_example.yaml"
  CONSTELLATION_EDITING_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_editing_example.yaml"
```

#### OpenAI Configuration

```yaml
CONSTELLATION_AGENT:
  REASONING_MODEL: false
  API_TYPE: "openai"
  API_BASE: "https://api.openai.com/v1/chat/completions"
  API_KEY: "sk-YOUR_KEY_HERE"
  API_VERSION: "2025-02-01-preview"
  API_MODEL: "gpt-4o"
  
  # Prompt configurations (use defaults)
  CONSTELLATION_CREATION_PROMPT: "galaxy/prompts/constellation/share/constellation_creation.yaml"
  CONSTELLATION_EDITING_PROMPT: "galaxy/prompts/constellation/share/constellation_editing.yaml"
  CONSTELLATION_CREATION_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_creation_example.yaml"
  CONSTELLATION_EDITING_EXAMPLE_PROMPT: "galaxy/prompts/constellation/examples/constellation_editing_example.yaml"
```

!!!info "More LLM Options"
    Galaxy supports various LLM providers including **Qwen**, **Gemini**, **Claude**, **DeepSeek**, and more. See the **[Model Configuration Guide](../configuration/models/overview.md)** for complete details.

---

## 🖥️ Step 3: Set Up Device Agents

Galaxy orchestrates **device agents** that execute tasks on individual machines. You need to start the appropriate device agents based on your needs.

### Supported Device Agents

| Device Agent | Platform | Documentation | Use Cases |
|--------------|----------|---------------|-----------|
| **WindowsAgent (UFO²)** | Windows 10/11 | [UFO² as Galaxy Device](../ufo2/as_galaxy_device.md) | Desktop automation, Office apps, GUI operations |
| **LinuxAgent** | Linux | [Linux as Galaxy Device](../linux/as_galaxy_device.md) | Server management, CLI operations, log analysis |
| **MobileAgent** | Android | [Mobile as Galaxy Device](../mobile/as_galaxy_device.md) | Mobile app automation, UI testing, device control |

> **💡 Choose Your Devices:** You can use any combination of Windows, Linux, and Mobile agents. Galaxy will intelligently route tasks based on device capabilities.

### Quick Setup Overview

For each device agent you want to use, you need to:

1. **Start the Device Agent Server** (manages tasks)
2. **Start the Device Agent Client** (executes commands)
3. **Start MCP Services** (provides automation tools, if needed)

**Detailed Setup Instructions:**

- **For Windows devices (UFO²):** See [UFO² as Galaxy Device](../ufo2/as_galaxy_device.md) for complete step-by-step instructions.
- **For Linux devices:** See [Linux as Galaxy Device](../linux/as_galaxy_device.md) for complete step-by-step instructions.
- **For Mobile devices:** See [Mobile as Galaxy Device](../mobile/as_galaxy_device.md) for complete step-by-step instructions.

### Example: Quick Windows Device Setup

**On your Windows machine:**

```powershell
# Terminal 1: Start UFO² Server
python -m ufo.server.app --port 5000

# Terminal 2: Start UFO² Client (connect to server)
python -m ufo.client.client `
  --ws `
  --ws-server ws://localhost:5000/ws `
  --client-id windows_device_1 `
  --platform windows
```

> **💡 Important:** Always include `--platform windows` for Windows devices and `--platform linux` for Linux devices!

### Example: Quick Linux Device Setup

**On your Linux machine:**

```bash
# Terminal 1: Start Device Agent Server
python -m ufo.server.app --port 5001

# Terminal 2: Start Linux Client (connect to server)
python -m ufo.client.client \
  --ws \
  --ws-server ws://localhost:5001/ws \
  --client-id linux_device_1 \
  --platform linux

# Terminal 3: Start HTTP MCP Server (for Linux tools)
python -m ufo.client.mcp.http_servers.linux_mcp_server
```

> **💡 Note:** For detailed Mobile Agent setup with ADB and Android device configuration, see [Mobile Quick Start](quick_start_mobile.md).

---

## 🔌 Step 4: Configure Device Pool

After starting your device agents, register them in Galaxy's device pool configuration.

### Option 1: Add Devices via Configuration File

### Edit Device Configuration

```powershell
notepad config\galaxy\devices.yaml
```

### Example Device Pool Configuration

```yaml
# Device Configuration for Galaxy
# Each device agent must be registered here

devices:
  # Windows Device (UFO²)
  - device_id: "windows_device_1"              # Must match --client-id
    server_url: "ws://localhost:5000/ws"       # Must match server WebSocket URL
    os: "windows"
    capabilities:
      - "desktop_automation"
      - "office_applications"
      - "excel"
      - "word"
      - "outlook"
      - "email"
      - "web_browsing"
    metadata:
      os: "windows"
      version: "11"
      performance: "high"
      installed_apps:
        - "Microsoft Excel"
        - "Microsoft Word"
        - "Microsoft Outlook"
        - "Google Chrome"
      description: "Primary Windows desktop for office automation"
    auto_connect: true
    max_retries: 5

  # Linux Device
  - device_id: "linux_device_1"                # Must match --client-id
    server_url: "ws://localhost:5001/ws"       # Must match server WebSocket URL
    os: "linux"
    capabilities:
      - "server_management"
      - "log_analysis"
      - "file_operations"
      - "database_operations"
    metadata:
      os: "linux"
      performance: "medium"
      logs_file_path: "/var/log/myapp/app.log"
      dev_path: "/home/user/projects/"
      warning_log_pattern: "WARN"
      error_log_pattern: "ERROR|FATAL"
      description: "Development server for backend operations"
    auto_connect: true
    max_retries: 5

  # Mobile Device (Android)
  - device_id: "mobile_phone_1"                # Must match --client-id
    server_url: "ws://localhost:5001/ws"       # Must match server WebSocket URL
    os: "mobile"
    capabilities:
      - "mobile"
      - "android"
      - "ui_automation"
      - "messaging"
      - "camera"
      - "location"
    metadata:
      os: "mobile"
      device_type: "phone"
      android_version: "13"
      screen_size: "1080x2400"
      installed_apps:
        - "com.android.chrome"
        - "com.google.android.apps.maps"
        - "com.whatsapp"
      description: "Android phone for mobile automation and testing"
    auto_connect: true
    max_retries: 5
```

> **⚠️ Critical:** IDs and URLs must match exactly:
> 
> - `device_id` must exactly match the `--client-id` flag
> - `server_url` must exactly match the server WebSocket URL
> - Otherwise, Galaxy cannot control the device!

**Complete Configuration Guide:** For detailed information about all configuration options, capabilities, and metadata, see [Galaxy Devices Configuration](../configuration/system/galaxy_devices.md).

### Option 2: Add Devices via WebUI (When Using --webui Mode)

If you start Galaxy with the `--webui` flag (see Step 5), you can add new device agents directly through the web interface without editing configuration files.

**Steps to Add Device via WebUI:**

1. **Launch Galaxy with WebUI** (as shown in Step 5):
   ```powershell
   python -m galaxy --webui
   ```

2. **Click the "+" button** in the top-right corner of the Device Agent panel (left sidebar)

3. **Fill in the device information** in the Add Device Modal:

<div align="center">
  <img src="../img/add_device.png" alt="Add Device Modal" width="70%">
  <p><em>➕ Add Device Modal - Register new device agents through the WebUI</em></p>
</div>

**Required Fields:**
- **Device ID**: Unique identifier (must match `--client-id` in device agent)
- **Server URL**: WebSocket endpoint (e.g., `ws://localhost:5000/ws`)
- **Operating System**: Select Windows, Linux, macOS, or enter custom OS
- **Capabilities**: Add at least one capability (e.g., `excel`, `outlook`, `log_analysis`)

**Optional Fields:**
- **Auto-connect**: Enable to automatically connect after registration (default: enabled)
- **Max Retries**: Maximum connection attempts (default: 5)
- **Metadata**: Add custom key-value pairs (e.g., `region: us-east-1`)

**Benefits of WebUI Device Management:**
- ✅ No need to manually edit YAML files
- ✅ Real-time validation of device ID uniqueness
- ✅ Automatic connection after registration
- ✅ Immediate visual feedback on device status
- ✅ Form validation prevents configuration errors

**After Adding:**
The device will be:
1. Saved to `config/galaxy/devices.yaml` automatically
2. Registered with Galaxy's Device Manager
3. Connected automatically (if auto-connect is enabled)
4. Displayed in the Device Agent panel with real-time status

> **💡 Tip:** You can add devices while Galaxy is running! No need to restart the server.

---

## 🎉 Step 5: Start UFO³ Galaxy

With all device agents running and configured, you can now launch Galaxy!

### Pre-Launch Checklist

Before starting Galaxy, ensure:

1. ✅ All Device Agent Servers are running
2. ✅ All Device Agent Clients are connected
3. ✅ MCP Services are running (for Linux devices)
4. ✅ LLM configured in `config/galaxy/agent.yaml`
5. ✅ Devices configured in `config/galaxy/devices.yaml`
6. ✅ Network connectivity between all components

### 🎨 Launch Galaxy - WebUI Mode (Recommended)

Start Galaxy with an interactive web interface for real-time constellation visualization and monitoring:

```powershell
# Assume you are in the cloned UFO folder
python -m galaxy --webui
```

This will start the Galaxy server with WebUI and automatically open your browser to the interactive interface:

<div align="center">
  <img src="../img/webui.png" alt="UFO³ Galaxy WebUI Interface" width="90%">
  <p><em>🎨 Galaxy WebUI - Interactive constellation visualization and chat interface</em></p>
</div>

**WebUI Features:**

- 🗣️ **Chat Interface**: Submit requests and interact with ConstellationAgent in real-time
- 📊 **Live DAG Visualization**: Watch task constellation formation and execution
- 🎯 **Task Status Tracking**: Monitor each TaskStar's progress and completion
- 🔄 **Dynamic Updates**: See constellation evolution as tasks complete
- 📱 **Responsive Design**: Works on desktop and tablet devices

**Default URL:** `http://localhost:8000` (automatically finds next available port if 8000 is occupied)

---

### 💬 Launch Galaxy - Interactive Terminal Mode

Start Galaxy in interactive mode where you can enter requests dynamically:

```powershell
# Assume you are in the cloned UFO folder
python -m galaxy --interactive
```

**Expected Output:**

```
🌌 Welcome to UFO³ Galaxy Framework
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Multi-Device AI Orchestration System

📡 Initializing Galaxy...
✅ ConstellationAgent initialized
✅ Connected to device: windows_device_1 (windows)
✅ Connected to device: linux_device_1 (linux)

🌟 Galaxy Ready - 2 devices online

Please enter your request 🛸:
```

---

### ⚡ Launch Galaxy - Direct Request Mode

Invoke Galaxy with a specific request directly:

```powershell
python -m galaxy --request "Your task description here"
```

**Example:**

```powershell
python -m galaxy --request "Generate a sales report from the database and create an Excel dashboard"
```

---

### 🎬 Launch Galaxy - Demo Mode

Run Galaxy in demo mode to see example workflows:

```powershell
python -m galaxy --demo
```

---

## 🎯 Step 6: Try Your First Multi-Device Workflow

### Example 1: Simple Cross-Platform Task

**User Request:**
> "Check the server logs for errors and email me a summary"

**Galaxy orchestrates:**

1. **Linux Device**: Analyze server logs for error patterns
2. **Windows Device**: Open Outlook, create email with log summary
3. **Windows Device**: Send email

**How to run:**

```powershell
python -m galaxy --request "Check the server logs for errors and email me a summary"
```

### Example 2: Data Processing Pipeline

**User Request:**
> "Export sales data from the database, create an Excel report with charts, and email it to the team"

**Galaxy orchestrates:**

1. **Linux Device**: Query database, export CSV
2. **Windows Device**: Open Excel, import CSV, create charts
3. **Windows Device**: Open Outlook, attach Excel file, send email

**How to run:**

```powershell
python -m galaxy --request "Export sales data from the database, create an Excel report with charts, and email it to the team"
```

### Example 3: Multi-Server Monitoring

**User Request:**
> "Check all servers for disk usage and alert if any are above 80%"

**Galaxy orchestrates:**

1. **Linux Device 1**: Check disk usage on server 1
2. **Linux Device 2**: Check disk usage on server 2
3. **Galaxy**: Aggregate results, check thresholds
4. **Windows Device**: Send alert email if needed

---

## 📔 Step 7: Understanding Device Routing

Galaxy uses **capability-based routing** to intelligently assign tasks to appropriate devices.

### How Galaxy Selects Devices

| Factor | Description | Example |
|--------|-------------|---------|
| **Capabilities** | Matches task requirements | `"excel"` → Windows device with Excel |
| **OS Requirement** | Platform-specific tasks | Linux commands → Linux device |
| **Metadata** | Device-specific context | Email task → device with Outlook |
| **Status** | Online and healthy devices only | Skips offline devices |

### Example Task Decomposition

**User Request:**
> "Prepare monthly reports and distribute to team"

**Galaxy Decomposition:**

```yaml
Subtask 1:
  Description: "Extract monthly data from database"
  Target Device: linux_device_1
  Reason: Has "database_operations" capability

Subtask 2:
  Description: "Create Excel report with visualizations"
  Target Device: windows_device_1
  Reason: Has "excel" capability

Subtask 3:
  Description: "Email reports to distribution list"
  Target Device: windows_device_1
  Reason: Has "email" and "outlook" capabilities
```

---

## 🔄 Step 8: Execution Logs

Galaxy automatically saves execution logs, task graphs, and device traces for debugging and analysis.

**Log Location:**

```
./logs/<session_name>/
```

**Log Contents:**

| File/Folder | Description |
|-------------|-------------|
| `constellation/` | DAG visualization and task decomposition |
| `device_logs/` | Individual device execution logs |
| `screenshots/` | Screenshots from Windows devices (if enabled) |
| `task_results/` | Task execution results |
| `request_response.log` | Complete LLM request/response logs |

> **Analyzing Logs:** Use the logs to debug task routing, identify bottlenecks, replay execution flow, and analyze orchestration decisions.

---

## 🔧 Advanced Configuration

### Custom Session Name

```powershell
python -m galaxy --request "Your task" --session-name "my_project"
```

### Custom Output Directory

```powershell
python -m galaxy --request "Your task" --output-dir "./custom_results"
```

### Debug Mode

```powershell
python -m galaxy --interactive --log-level DEBUG
```

### Limit Maximum Rounds

```powershell
python -m galaxy --interactive --max-rounds 20
```

---

## ❓ Troubleshooting

### Issue 1: Device Not Appearing in Galaxy

**Error:** Device not found in configuration

```log
ERROR - Device 'windows_device_1' not found in configuration
```

**Solutions:**

1. Verify `devices.yaml` configuration:
   ```powershell
   notepad config\galaxy\devices.yaml
   ```

2. Check device ID matches:
   - In `devices.yaml`: `device_id: "windows_device_1"`
   - In client command: `--client-id windows_device_1`

3. Check server URL matches:
   - In `devices.yaml`: `server_url: "ws://localhost:5000/ws"`
   - In client command: `--ws-server ws://localhost:5000/ws`

### Issue 2: Device Agent Not Connecting

**Error:** Connection refused

```log
ERROR - [WS] Failed to connect to ws://localhost:5000/ws
Connection refused
```

**Solutions:**

1. Verify server is running:
   ```powershell
   curl http://localhost:5000/api/health
   ```

2. Check port number is correct:
   - Server: `--port 5000`
   - Client: `ws://localhost:5000/ws`

3. Ensure platform flag is set:
   ```powershell
   # For Windows devices
   --platform windows
   
   # For Linux devices
   --platform linux
   ```

### Issue 3: Galaxy Cannot Find Constellation Agent Config

**Error:** Configuration file not found

```log
ERROR - Cannot find config/galaxy/agent.yaml
```

**Solution:**
```powershell
# Copy template to create configuration file
copy config\galaxy\agent.yaml.template config\galaxy\agent.yaml

# Edit with your LLM credentials
notepad config\galaxy\agent.yaml
```

### Issue 4: Task Not Routed to Expected Device

**Issue:** Wrong device selected for task

**Diagnosis:** Check device capabilities in `devices.yaml`:

```yaml
capabilities:
  - "desktop_automation"
  - "office_applications"
  - "excel"  # Required for Excel tasks
  - "outlook"  # Required for email tasks
```

**Solution:** Add appropriate capabilities to your device configuration.

---

## 📚 Additional Resources

### Core Documentation

**Architecture & Concepts:**

- [Galaxy Overview](../galaxy/overview.md) - System architecture and design principles
- [Constellation Orchestrator](../galaxy/constellation_orchestrator/overview.md) - Task orchestration and DAG management
- [Agent Interaction Protocol (AIP)](../aip/overview.md) - Communication substrate

### Device Agent Setup

**Device Agent Guides:**

- [UFO² as Galaxy Device](../ufo2/as_galaxy_device.md) - Complete Windows device setup
- [Linux as Galaxy Device](../linux/as_galaxy_device.md) - Complete Linux device setup
- [Mobile as Galaxy Device](../mobile/as_galaxy_device.md) - Complete Android device setup
- [UFO² Overview](../ufo2/overview.md) - Windows desktop automation capabilities
- [Linux Agent Overview](../linux/overview.md) - Linux server automation capabilities
- [Mobile Agent Overview](../mobile/overview.md) - Android mobile automation capabilities

### Configuration

**Configuration Guides:**

- [Galaxy Devices Configuration](../configuration/system/galaxy_devices.md) - Complete device pool configuration
- [Galaxy Constellation Configuration](../configuration/system/galaxy_constellation.md) - Runtime settings
- [Agents Configuration](../configuration/system/agents_config.md) - LLM settings for all agents
- [Model Configuration](../configuration/models/overview.md) - Supported LLM providers

### Advanced Features

**Advanced Topics:**

- [Task Constellation](../galaxy/constellation/task_constellation.md) - DAG-based task planning
- [Constellation Orchestrator](../galaxy/constellation_orchestrator/overview.md) - Multi-device orchestration
- [Device Registry](../galaxy/agent_registration/device_registry.md) - Device management
- [Agent Profiles](../galaxy/agent_registration/agent_profile.md) - Multi-source profiling

---

## ❓ Getting Help

- 📖 **Documentation**: [https://microsoft.github.io/UFO/](https://microsoft.github.io/UFO/)
- 🐛 **GitHub Issues**: [https://github.com/microsoft/UFO/issues](https://github.com/microsoft/UFO/issues) (preferred)
- 📧 **Email**: [ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com)

---

## 🎯 Next Steps

Now that Galaxy is set up, explore these guides to unlock its full potential:

1. **[Add More Devices](../configuration/system/galaxy_devices.md)** - Expand your device pool
2. **[Configure Capabilities](../configuration/system/galaxy_devices.md)** - Optimize task routing
3. **[Constellation Agent](../galaxy/constellation_agent/overview.md)** - Deep dive into orchestration agent
4. **[Advanced Orchestration](../galaxy/constellation_orchestrator/overview.md)** - Deep dive into DAG planning

Happy orchestrating with UFO³ Galaxy! 🌌🚀
