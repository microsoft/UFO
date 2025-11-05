# Complete Field Reference

This comprehensive reference documents all configuration fields available in UFO2's configuration system, organized by domain.

!!!info "Field Reference Guide"
    This document provides detailed information about every configuration field, including types, defaults, and usage examples. Use the Quick Navigation to jump to specific sections.

## Quick Navigation

- [Agent Configurations](#agent-configurations) - LLM and agent-specific settings
- [System Configurations](#system-configurations) - Runtime and execution settings
- [RAG Configurations](#rag-configurations) - Knowledge retrieval settings
- [MCP Configurations](#mcp-configurations) - Model Context Protocol servers
- [Pricing Configurations](#pricing-configurations) - Cost tracking settings

## Configuration Files Overview

!!!note "Configuration File Structure"
    UFO2 organizes configurations into separate YAML files by domain for better maintainability.

| File | Purpose | Required | Contains |
|------|---------|----------|----------|
| `config/ufo/agents.yaml` | Agent LLM settings | ? Yes | HOST_AGENT, APP_AGENT, BACKUP_AGENT, EVALUATION_AGENT, OPERATOR |
| `config/ufo/system.yaml` | System runtime settings | ? Yes | Execution limits, logging, control backend, etc. |
| `config/ufo/rag.yaml` | RAG knowledge settings | Optional | Offline docs, online search, experience, demonstration |
| `config/ufo/mcp.yaml` | MCP server definitions | Optional | MCP server configurations |
| `config/ufo/prices.yaml` | Model pricing | Optional | Cost per 1K tokens for different models |
| `config/ufo/third_party.yaml` | Third-party integrations | Optional | Custom agent configurations |

---

## Agent Configurations

**File**: `config/ufo/agents.yaml`

Agent configurations define the LLM settings for different agents in UFO2. Each agent can be configured independently with different models, API endpoints, and parameters.

### Common Agent Fields

These fields are available for all agent types (`HOST_AGENT`, `APP_AGENT`, `BACKUP_AGENT`, `EVALUATION_AGENT`, `OPERATOR`).

#### Core Settings

!!!note "Essential Agent Configuration"
    These fields are required for all agent types to connect to LLM services.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `VISUAL_MODE` | Boolean | `True` | Whether to use visual mode (screenshot understanding) |
| `REASONING_MODEL` | Boolean | `False` | Whether the model is a reasoning model (OpenAI o1, o3, o4-mini) |
| `API_TYPE` | String | `"openai"` | API type: `"openai"`, `"aoai"`, `"azure_ad"`, `"gemini"`, `"claude"`, etc. |
| `API_BASE` | String | varies | API endpoint URL |
| `API_KEY` | String | `""` | API authentication key |
| `API_VERSION` | String | `"2025-02-01-preview"` | API version |
| `API_MODEL` | String | `"gpt-4o"` | Model name/identifier |

```yaml
    HOST_AGENT:
      VISUAL_MODE: True
      REASONING_MODEL: False
      API_TYPE: "openai"
      API_BASE: "https://api.openai.com/v1/chat/completions"
      API_KEY: "sk-YOUR_KEY_HERE"
      API_VERSION: "2025-02-01-preview"
      API_MODEL: "gpt-4o"
    ```

#### Azure OpenAI (AOAI) Additional Fields

!!!tip "Azure OpenAI Configuration"
    When using Azure OpenAI, you need to specify the deployment ID in addition to the standard fields.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `API_DEPLOYMENT_ID` | String | `""` | Azure OpenAI deployment identifier |

```yaml
    HOST_AGENT:
      API_TYPE: "aoai"
      API_BASE: "https://YOUR_RESOURCE.openai.azure.com"
      API_KEY: "YOUR_AOAI_KEY"
      API_VERSION: "2024-02-15-preview"
      API_MODEL: "gpt-4o"
      API_DEPLOYMENT_ID: "gpt-4o-deployment"
    ```

#### Azure AD Authentication Fields

!!!warning "Azure AD Authentication"
    For enterprise Azure environments using Active Directory authentication instead of API keys.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `AAD_TENANT_ID` | String | `None` | Azure AD tenant ID |
| `AAD_API_SCOPE` | String | `None` | Azure AD API scope |
| `AAD_API_SCOPE_BASE` | String | `None` | Azure AD scope base (format: `API://YOUR_SCOPE_BASE`) |

```yaml
    HOST_AGENT:
      API_TYPE: "azure_ad"
      AAD_TENANT_ID: "YOUR_TENANT_ID"
      AAD_API_SCOPE: "YOUR_SCOPE"
      AAD_API_SCOPE_BASE: "YOUR_SCOPE_BASE"
    ```

#### Prompt Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `PROMPT` | String | varies | Path to main prompt template |
| `EXAMPLE_PROMPT` | String | varies | Path to example prompt template |
| `EXAMPLE_PROMPT_AS` | String | varies | Path to action sequence example prompt (APP_AGENT only) |

**Example**:
```yaml
APP_AGENT:
  PROMPT: "ufo/prompts/share/base/app_agent.yaml"
  EXAMPLE_PROMPT: "ufo/prompts/examples/{mode}/app_agent_example.yaml"
  EXAMPLE_PROMPT_AS: "ufo/prompts/examples/{mode}/app_agent_example_as.yaml"
```

### Specific Agent Purposes

!!!info "Agent Roles in UFO2"
    Each agent type serves a specific purpose in the UFO2 workflow.

| Agent | Purpose | Typical Model |
|-------|---------|--------------|
| **HOST_AGENT** | Task planning and application coordination | GPT-4o, GPT-4 |
| **APP_AGENT** | Application-specific action execution | GPT-4o, GPT-4o-mini |
| **BACKUP_AGENT** | Fallback when primary agents fail | GPT-4-vision-preview |
| **EVALUATION_AGENT** | Task completion evaluation | GPT-4o |
| **OPERATOR** | CUA-based automation (OpenAI Operator) | operator-20250213 |

### Access Patterns

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# Type-safe access (recommended)
host_model = config.host_agent.api_model
app_visual = config.app_agent.visual_mode
backup_key = config.backup_agent.api_key

# Dict-style access (legacy)
host_model_old = config.HOST_AGENT.API_MODEL
app_visual_old = config.APP_AGENT.VISUAL_MODE
```

---

## System Configurations

**File**: `config/ufo/system.yaml`

System configurations control the runtime behavior, execution limits, logging, and various operational aspects of UFO2.

### LLM Parameters

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `MAX_TOKENS` | Integer | `2000` | Maximum token limit for response completion |
| `MAX_RETRY` | Integer | `20` | Maximum retry limit for response completion |
| `TEMPERATURE` | Float | `0.0` | Model temperature (0.0 = consistent, higher = creative) |
| `TOP_P` | Float | `0.0` | Model top_p (0.0 = conservative, higher = diverse) |
| `TIMEOUT` | Integer | `60` | API call timeout in seconds |

**Example**:
```yaml
MAX_TOKENS: 2000
MAX_RETRY: 20
TEMPERATURE: 0.0
TOP_P: 0.0
TIMEOUT: 60
```

### Control Backend

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CONTROL_BACKEND` | List[String] | `["uia"]` | Control detection backends: `"uia"`, `"win32"`, `"omniparser"` |
| `IOU_THRESHOLD_FOR_MERGE` | Float | `0.1` | IoU threshold for merging detected controls |

**Example**:
```yaml
CONTROL_BACKEND: ["uia", "win32"]
IOU_THRESHOLD_FOR_MERGE: 0.1
```

### Execution Limits

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `MAX_STEP` | Integer | `50` | Maximum steps for completing a user request |
| `MAX_ROUND` | Integer | `1` | Maximum rounds for completing a user request |
| `SLEEP_TIME` | Integer | `1` | Sleep time between steps (seconds) |
| `RECTANGLE_TIME` | Integer | `1` | Time to display rectangle annotations (seconds) |

**Example**:
```yaml
MAX_STEP: 50
MAX_ROUND: 1
SLEEP_TIME: 1
RECTANGLE_TIME: 1
```

### Action Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ACTION_SEQUENCE` | Boolean | `False` | Enable speculative multi-action execution |
| `SHOW_VISUAL_OUTLINE_ON_SCREEN` | Boolean | `False` | Show visual outlines on screen during execution |
| `MAXIMIZE_WINDOW` | Boolean | `False` | Maximize application window before actions |
| `JSON_PARSING_RETRY` | Integer | `3` | Retry times for JSON parsing |

**Example**:
```yaml
ACTION_SEQUENCE: True  # Enable multi-action
SHOW_VISUAL_OUTLINE_ON_SCREEN: False
MAXIMIZE_WINDOW: False
JSON_PARSING_RETRY: 3
```

### Control Actions

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CLICK_API` | String | `"click_input"` | Click API method |
| `AFTER_CLICK_WAIT` | Integer | `0` | Wait time after clicking (seconds) |
| `INPUT_TEXT_API` | String | `"type_keys"` | Input text API: `"type_keys"` or `"set_text"` |
| `INPUT_TEXT_ENTER` | Boolean | `False` | Press Enter after typing text |
| `INPUT_TEXT_INTER_KEY_PAUSE` | Float | `0.05` | Pause between key presses (seconds) |

**Example**:
```yaml
CLICK_API: "click_input"
AFTER_CLICK_WAIT: 0
INPUT_TEXT_API: "type_keys"
INPUT_TEXT_ENTER: False
INPUT_TEXT_INTER_KEY_PAUSE: 0.05
```

### Logging

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `PRINT_LOG` | Boolean | `False` | Print logs to console |
| `LOG_LEVEL` | String | `"DEBUG"` | Log level: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` |
| `LOG_TO_MARKDOWN` | Boolean | `True` | Save logs to Markdown files |
| `LOG_XML` | Boolean | `False` | Log UI tree XML at each step |
| `CONCAT_SCREENSHOT` | Boolean | `False` | Concatenate screenshots for control items |
| `INCLUDE_LAST_SCREENSHOT` | Boolean | `True` | Include last screenshot in observation |
| `SCREENSHOT_TO_MEMORY` | Boolean | `True` | Load screenshots to memory |
| `REQUEST_TIMEOUT` | Integer | `250` | Request timeout for GPT-V model |

**Example**:
```yaml
PRINT_LOG: False
LOG_LEVEL: "DEBUG"
LOG_TO_MARKDOWN: True
LOG_XML: False
INCLUDE_LAST_SCREENSHOT: True
```

### Safety

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `SAFE_GUARD` | Boolean | `False` | Enable safe guard to prevent sensitive operations |
| `CONTROL_LIST` | List[String] | See default | Allowed control types for interaction |

**Default CONTROL_LIST**:
```yaml
CONTROL_LIST:
  - "Button"
  - "Edit"
  - "TabItem"
  - "Document"
  - "ListItem"
  - "MenuItem"
  - "ScrollBar"
  - "TreeItem"
  - "Hyperlink"
  - "ComboBox"
  - "RadioButton"
  - "Spinner"
  - "CheckBox"
  - "Group"
  - "Text"
```

### API Usage

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `USE_APIS` | Boolean | `True` | Enable native API usage (Win32, WinCOM) |
| `API_PROMPT` | String | `"ufo/prompts/share/base/api.yaml"` | Path to API prompt template |
| `APP_API_PROMPT_ADDRESS` | Dict | See below | App-specific API prompt paths |

**Example**:
```yaml
USE_APIS: True
API_PROMPT: "ufo/prompts/share/base/api.yaml"
APP_API_PROMPT_ADDRESS:
  "WINWORD.EXE": "ufo/prompts/apps/word/api.yaml"
  "EXCEL.EXE": "ufo/prompts/apps/excel/api.yaml"
  "msedge.exe": "ufo/prompts/apps/web/api.yaml"
```

### MCP (Model Context Protocol)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `USE_MCP` | Boolean | `True` | Enable Model Context Protocol |
| `MCP_SERVERS_CONFIG` | String | `"config/ufo/mcp.yaml"` | Path to MCP servers configuration |
| `MCP_PREFERRED_APPS` | List[String] | `[]` | Applications that prefer MCP tools |
| `MCP_FALLBACK_TO_UI` | Boolean | `True` | Fall back to UI automation if MCP fails |
| `MCP_INSTRUCTIONS_PATH` | String | `"ufo/config/mcp_instructions"` | Path to MCP instruction templates |
| `MCP_TOOL_TIMEOUT` | Integer | `30` | MCP tool execution timeout (seconds) |
| `MCP_LOG_EXECUTION` | Boolean | `False` | Log MCP tool execution details |

**Example**:
```yaml
USE_MCP: True
MCP_SERVERS_CONFIG: "config/ufo/mcp.yaml"
MCP_PREFERRED_APPS: ["Code.exe", "WindowsTerminal.exe"]
MCP_FALLBACK_TO_UI: True
MCP_TOOL_TIMEOUT: 30
```

### Control Filtering

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CONTROL_FILTER_TYPE` | List[String] | `[]` | Control filter types: `"TEXT"`, `"SEMANTIC"`, `"ICON"` |
| `CONTROL_FILTER_TOP_K_PLAN` | Integer | `2` | Top K plans to filter controls for |
| `CONTROL_FILTER_TOP_K_SEMANTIC` | Integer | `15` | Top K controls by semantic similarity |
| `CONTROL_FILTER_TOP_K_ICON` | Integer | `15` | Top K controls by icon similarity |
| `CONTROL_FILTER_MODEL_SEMANTIC_NAME` | String | `"all-MiniLM-L6-v2"` | Semantic embedding model name |
| `CONTROL_FILTER_MODEL_ICON_NAME` | String | `"clip-ViT-B-32"` | Icon embedding model name |

**Example**:
```yaml
CONTROL_FILTER_TYPE: ["SEMANTIC", "ICON"]
CONTROL_FILTER_TOP_K_PLAN: 2
CONTROL_FILTER_TOP_K_SEMANTIC: 15
CONTROL_FILTER_MODEL_SEMANTIC_NAME: "all-MiniLM-L6-v2"
```

### Access Patterns

```python
config = get_ufo_config()

# Type-safe access (recommended)
max_step = config.system.max_step
log_level = config.system.log_level
use_mcp = config.system.use_mcp

# Dict-style access (legacy)
max_step_old = config["MAX_STEP"]
log_level_old = config["LOG_LEVEL"]
```

---

## RAG Configurations

**File**: `config/ufo/rag.yaml`

RAG (Retrieval-Augmented Generation) configurations control knowledge sources that enhance agent decision-making.

### Offline Documentation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `RAG_OFFLINE_DOCS` | Boolean | `False` | Enable offline documentation retrieval |
| `RAG_OFFLINE_DOCS_RETRIEVED_TOPK` | Integer | `1` | Top K retrieved offline documents |

### Online Search

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `RAG_ONLINE_SEARCH` | Boolean | `False` | Enable online Bing search |
| `BING_API_KEY` | String | `""` | Bing Search API key |
| `RAG_ONLINE_SEARCH_TOPK` | Integer | `5` | Top K search results to retrieve |
| `RAG_ONLINE_RETRIEVED_TOPK` | Integer | `5` | Top K retrieved search results |

### Experience Learning

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `RAG_EXPERIENCE` | Boolean | `False` | Enable experience learning from past executions |
| `RAG_EXPERIENCE_RETRIEVED_TOPK` | Integer | `5` | Top K retrieved experience records |
| `EXPERIENCE_SAVED_PATH` | String | Auto | Path to save experience data |
| `EXPERIENCE_PROMPT` | String | Auto | Experience prompt template path |

### Demonstration Learning

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `RAG_DEMONSTRATION` | Boolean | `False` | Enable learning from user demonstrations |
| `RAG_DEMONSTRATION_RETRIEVED_TOPK` | Integer | `5` | Top K retrieved demonstrations |
| `DEMONSTRATION_SAVED_PATH` | String | Auto | Path to save demonstration data |
| `DEMONSTRATION_PROMPT` | String | Auto | Demonstration prompt template path |

**Example**:
```yaml
# config/ufo/rag.yaml
RAG_OFFLINE_DOCS: False
RAG_OFFLINE_DOCS_RETRIEVED_TOPK: 1

RAG_ONLINE_SEARCH: True
BING_API_KEY: "YOUR_BING_API_KEY"
RAG_ONLINE_SEARCH_TOPK: 5
RAG_ONLINE_RETRIEVED_TOPK: 5

RAG_EXPERIENCE: True
RAG_EXPERIENCE_RETRIEVED_TOPK: 5

RAG_DEMONSTRATION: False
RAG_DEMONSTRATION_RETRIEVED_TOPK: 5
```

### Access Patterns

```python
config = get_ufo_config()

# Type-safe access (recommended)
offline_enabled = config.rag.offline_docs
experience_enabled = config.rag.experience
bing_key = config.rag.BING_API_KEY  # Dynamic field

# Dict-style access (legacy)
offline_old = config["RAG_OFFLINE_DOCS"]
experience_old = config["RAG_EXPERIENCE"]
```

---

## MCP Configurations

**File**: `config/ufo/mcp.yaml`

MCP (Model Context Protocol) configurations define the external tool servers that agents can use for data collection and action execution.

!!!info "MCP Server Configuration"
    MCP servers provide tools that extend agent capabilities. See the [MCP Configuration Reference](./mcp_reference.md) for complete documentation.

### Basic Structure

```yaml
HostAgent:
  default:
    data_collection:
      - namespace: UICollector
        type: local
    action:
      - namespace: HostUIExecutor
        type: local
      - namespace: CommandLineExecutor
        type: local

AppAgent:
  WINWORD.EXE:
    action:
      - namespace: WordCOMExecutor
        type: local
        reset: true
```

### Common MCP Server Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | String | ✅ Yes | Unique server identifier |
| `type` | String | ✅ Yes | Server type: `"local"`, `"http"`, `"stdio"` |
| `reset` | Boolean | No | Reset server state on context switch (default: `false`) |

### HTTP Server Additional Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `host` | String | ✅ Yes | Server hostname or IP |
| `port` | Integer | ✅ Yes | Server port number |
| `path` | String | ✅ Yes | HTTP endpoint path |

### Stdio Server Additional Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | String | ✅ Yes | Executable command |
| `start_args` | List[String] | No | Command-line arguments |
| `env` | Dict | No | Environment variables |
| `cwd` | String | No | Working directory |

For complete MCP configuration documentation, see:

- [MCP Configuration Reference](./mcp_reference.md) - Detailed MCP server configuration
- [MCP Overview](../../mcp/overview.md) - MCP architecture and concepts

---

## Pricing Configurations

**File**: `config/ufo/prices.yaml`

Pricing configurations define the cost per 1K tokens for different LLM models, used for cost tracking and reporting.

### Structure

```yaml
gpt-4o:
  prompt: 0.0025
  completion: 0.01
  
gpt-4o-mini:
  prompt: 0.00015
  completion: 0.0006
  
gpt-4-vision-preview:
  prompt: 0.01
  completion: 0.03
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | Float | Cost per 1K prompt tokens (USD) |
| `completion` | Float | Cost per 1K completion tokens (USD) |

### Common Models

| Model | Prompt ($/1K) | Completion ($/1K) |
|-------|---------------|-------------------|
| `gpt-4o` | $0.0025 | $0.01 |
| `gpt-4o-mini` | $0.00015 | $0.0006 |
| `gpt-4-turbo` | $0.01 | $0.03 |
| `gpt-4-vision-preview` | $0.01 | $0.03 |
| `gpt-3.5-turbo` | $0.0005 | $0.0015 |

### Access Patterns

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# Get pricing for a specific model
model_name = "gpt-4o"
if model_name in config.prices:
    prompt_cost = config.prices[model_name]["prompt"]
    completion_cost = config.prices[model_name]["completion"]
    print(f"{model_name}: ${prompt_cost}/1K prompt, ${completion_cost}/1K completion")
```

### Cost Tracking

UFO² automatically tracks costs during execution when pricing information is available:

```python
# Costs are tracked in session logs
total_cost = session.total_cost
prompt_tokens = session.total_prompt_tokens
completion_tokens = session.total_completion_tokens
```

---

## Next Sections

Continue to:
- **[MCP Configuration Reference](./mcp_reference.md)** - Model Context Protocol server configuration
- **[Migration Guide](./migration.md)** - Migrating from legacy configuration
- **[Extending Configuration](./extending.md)** - Adding custom configuration options
