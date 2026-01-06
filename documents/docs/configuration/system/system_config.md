# System Configuration (system.yaml)

Configure UFO²'s runtime behavior, execution limits, control backends, logging, and operational parameters. This file controls how UFO² interacts with the Windows environment.

## Overview

The `system.yaml` file defines runtime settings that control UFO²'s behavior during task execution. Unlike `agents.yaml` (which configures LLMs), this file configures **how** UFO² operates on Windows.

**File Location**: `config/ufo/system.yaml`

**Note:** Unlike `agents.yaml`, the `system.yaml` file is **already present** in the repository with sensible defaults. You can use it as-is or customize it for your needs.

## Quick Configuration

### Default Configuration (Works Out of Box)

```yaml
# Most users can use default settings
MAX_STEP: 50
MAX_ROUND: 1
CONTROL_BACKEND: ["uia"]
USE_MCP: True
PRINT_LOG: False
```

### Recommended for Development

```yaml
# More verbose logging for debugging
MAX_STEP: 50
MAX_ROUND: 1
PRINT_LOG: True
LOG_LEVEL: "DEBUG"
CONTROL_BACKEND: ["uia"]
```

### Recommended for Production

```yaml
# Optimized for reliability
MAX_STEP: 100
MAX_ROUND: 3
CONTROL_BACKEND: ["uia"]
USE_MCP: True
SAFE_GUARD: True
LOG_TO_MARKDOWN: True
```

## Configuration Categories

The `system.yaml` file is organized into logical sections:

| Category | Purpose | Key Fields |
|----------|---------|------------|
| **[LLM Parameters](#llm-parameters)** | API call settings | `MAX_TOKENS`, `TEMPERATURE`, `TIMEOUT` |
| **[Execution Limits](#execution-limits)** | Task boundaries | `MAX_STEP`, `MAX_ROUND`, `SLEEP_TIME` |
| **[Control Backend](#control-backend)** | UI detection methods | `CONTROL_BACKEND`, `IOU_THRESHOLD` |
| **[Action Configuration](#action-configuration)** | Interaction behavior | `CLICK_API`, `INPUT_TEXT_API`, `MAXIMIZE_WINDOW` |
| **[Logging](#logging)** | Output and debugging | `PRINT_LOG`, `LOG_LEVEL`, `LOG_XML` |
| **[MCP Settings](#mcp-settings)** | Tool server integration | `USE_MCP`, `MCP_SERVERS_CONFIG` |
| **[Safety](#safety)** | Security controls | `SAFE_GUARD`, `CONTROL_LIST` |
| **[Control Filtering](#control-filtering)** | UI element filtering | `CONTROL_FILTER_TYPE`, `CONTROL_FILTER_TOP_K` |

## LLM Parameters

These settings control how UFO² communicates with LLM APIs.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `MAX_TOKENS` | Integer | `2000` | Maximum tokens for LLM response |
| `MAX_RETRY` | Integer | `20` | Maximum retries for failed API calls |
| `TEMPERATURE` | Float | `0.0` | Sampling temperature (0.0 = deterministic, 1.0 = creative) |
| `TOP_P` | Float | `0.0` | Nucleus sampling threshold |
| `TIMEOUT` | Integer | `60` | API call timeout (seconds) |

### Example

```yaml
# Conservative settings (recommended)
MAX_TOKENS: 2000
MAX_RETRY: 20
TEMPERATURE: 0.0  # Deterministic
TOP_P: 0.0
TIMEOUT: 60

# Creative settings (experimental)
# MAX_TOKENS: 4000
# TEMPERATURE: 0.7  # More creative
# TOP_P: 0.9
```

**When to Adjust:**

- **Increase MAX_TOKENS** if responses are getting cut off
- **Increase TEMPERATURE** if you want more varied responses (not recommended)
- **Keep at 0.0** for consistent, repeatable automation
- **Increase TIMEOUT** for slow API connections

## Execution Limits

Control how long and how many attempts UFO² makes for tasks.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `MAX_STEP` | Integer | `50` | Maximum steps per task |
| `MAX_ROUND` | Integer | `1` | Maximum rounds per task (retries from start) |
| `SLEEP_TIME` | Integer | `1` | Wait time between steps (seconds) |
| `RECTANGLE_TIME` | Integer | `1` | Duration to show visual highlights (seconds) |

### Example

```yaml
# Default settings
MAX_STEP: 50
MAX_ROUND: 1
SLEEP_TIME: 1
RECTANGLE_TIME: 1

# For complex tasks
# MAX_STEP: 100
# MAX_ROUND: 3

# For faster execution (risky)
# SLEEP_TIME: 0
```

**Note on Step vs Round:**

- **STEP**: Individual action (click, type, etc.)
- **ROUND**: Complete task attempt from start

Example: If `MAX_ROUND: 3`, UFO² will retry the entire task up to 3 times if it fails.

## Control Backend

Configure how UFO² detects and interacts with UI elements.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CONTROL_BACKEND` | List[String] | `["uia"]` | UI detection backends to use |
| `IOU_THRESHOLD_FOR_MERGE` | Float | `0.1` | IoU threshold for merging overlapping controls |

### Available Backends

| Backend | Description | Pros | Cons |
|---------|-------------|------|------|
| `"uia"` | UI Automation | Fast, reliable, Windows native | May miss some controls |
| `"omniparser"` | Vision-based | Finds visual-only elements | Requires GPU, slow |

**Note:** `win32` backend is no longer supported.

### Example

```yaml
# Recommended: Use UIA (default)
CONTROL_BACKEND: ["uia"]
IOU_THRESHOLD_FOR_MERGE: 0.1

# With vision-based parsing (slow)
# CONTROL_BACKEND: ["uia", "omniparser"]
```

**Best Practice:** Use `["uia"]` as the default backend. Add `"omniparser"` only if you need vision-based control detection.

## Action Configuration

Configure how UFO² performs actions on UI elements.

### Core Action Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ACTION_SEQUENCE` | Boolean | `False` | Enable multi-action sequences in one step |
| `SHOW_VISUAL_OUTLINE_ON_SCREEN` | Boolean | `False` | Show visual highlights during execution |
| `MAXIMIZE_WINDOW` | Boolean | `False` | Maximize application windows before actions |
| `JSON_PARSING_RETRY` | Integer | `3` | Retries for parsing LLM JSON responses |

### Click Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CLICK_API` | String | `"click_input"` | Click method to use |
| `AFTER_CLICK_WAIT` | Integer | `0` | Wait time after clicking (seconds) |

### Input Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `INPUT_TEXT_API` | String | `"type_keys"` | Text input method |
| `INPUT_TEXT_ENTER` | Boolean | `False` | Press Enter after typing |
| `INPUT_TEXT_INTER_KEY_PAUSE` | Float | `0.05` | Pause between keystrokes (seconds) |

### Example

```yaml
# Recommended settings
ACTION_SEQUENCE: True  # Enable multi-action for speed
SHOW_VISUAL_OUTLINE_ON_SCREEN: False
MAXIMIZE_WINDOW: False
JSON_PARSING_RETRY: 3

CLICK_API: "click_input"
AFTER_CLICK_WAIT: 0

INPUT_TEXT_API: "type_keys"
INPUT_TEXT_ENTER: False
INPUT_TEXT_INTER_KEY_PAUSE: 0.05

# For visual debugging
# SHOW_VISUAL_OUTLINE_ON_SCREEN: True

# If clicks are too fast
# AFTER_CLICK_WAIT: 1

# For automation that needs Enter key
# INPUT_TEXT_ENTER: True
```

!!!info "Input Methods"
    - **`type_keys`**: Simulates keyboard (slower, more realistic)
    - **`set_text`**: Direct text insertion (faster, may not trigger events)

---

## Logging

Control UFO²'s logging output and debugging information.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `PRINT_LOG` | Boolean | `False` | Print logs to console |
| `LOG_LEVEL` | String | `"DEBUG"` | Logging verbosity level |
| `LOG_TO_MARKDOWN` | Boolean | `True` | Save logs as Markdown files |
| `LOG_XML` | Boolean | `False` | Log UI tree XML at each step |
| `CONCAT_SCREENSHOT` | Boolean | `False` | Concatenate control screenshots |
| `INCLUDE_LAST_SCREENSHOT` | Boolean | `True` | Include previous screenshot in context |
| `SCREENSHOT_TO_MEMORY` | Boolean | `True` | Load screenshots into memory |
| `REQUEST_TIMEOUT` | Integer | `250` | Request timeout for vision models |

### Log Levels

| Level | Usage | When to Use |
|-------|-------|-------------|
| `"DEBUG"` | Detailed debugging info | Development, troubleshooting |
| `"INFO"` | General information | Normal operation |
| `"WARNING"` | Warning messages | Production |
| `"ERROR"` | Errors only | Production (minimal logs) |

### Example

```yaml
# Development settings
PRINT_LOG: True
LOG_LEVEL: "DEBUG"
LOG_TO_MARKDOWN: True
LOG_XML: True  # Useful for debugging UI detection

# Production settings
# PRINT_LOG: False
# LOG_LEVEL: "WARNING"
# LOG_TO_MARKDOWN: True
# LOG_XML: False

# Memory optimization
# SCREENSHOT_TO_MEMORY: False
```

!!!tip "Log Files Location"
    Logs are saved to `logs/<timestamp>/` directory.

---

## MCP Settings

Configure Model Context Protocol (MCP) tool servers.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `USE_MCP` | Boolean | `True` | Enable MCP tool integration |
| `MCP_SERVERS_CONFIG` | String | `"config/ufo/mcp.yaml"` | Path to MCP servers config |
| `MCP_PREFERRED_APPS` | List[String] | `[]` | Apps that prefer MCP over UI automation |
| `MCP_FALLBACK_TO_UI` | Boolean | `True` | Fall back to UI if MCP fails |
| `MCP_INSTRUCTIONS_PATH` | String | `"ufo/config/mcp_instructions"` | MCP instruction templates path |
| `MCP_TOOL_TIMEOUT` | Integer | `30` | MCP tool execution timeout (seconds) |
| `MCP_LOG_EXECUTION` | Boolean | `False` | Log detailed MCP execution |

### Example

```yaml
# Recommended settings
USE_MCP: True
MCP_SERVERS_CONFIG: "config/ufo/mcp.yaml"
MCP_FALLBACK_TO_UI: True
MCP_TOOL_TIMEOUT: 30
MCP_LOG_EXECUTION: False

# Prefer MCP for VS Code and Terminal
MCP_PREFERRED_APPS:
  - "Code.exe"
  - "WindowsTerminal.exe"

# Debugging MCP issues
# MCP_LOG_EXECUTION: True
# MCP_TOOL_TIMEOUT: 60
```

!!!info "What is MCP?"
    MCP (Model Context Protocol) provides programmatic APIs for applications, offering more reliable automation than UI-based control.
    
    See [MCP Configuration](mcp_reference.md) for details.

---

## Safety

Security and safety controls to prevent dangerous operations.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `SAFE_GUARD` | Boolean | `False` | Enable safety checks |
| `CONTROL_LIST` | List[String] | See below | Allowed UI control types |

### Default CONTROL_LIST

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

### Example

```yaml
# Enable safety for production
SAFE_GUARD: True
CONTROL_LIST:
  - "Button"
  - "Edit"
  - "TabItem"
  # Add only safe control types

# Disable for full automation (risky)
# SAFE_GUARD: False
```

!!!danger "Safety Warning"
    When `SAFE_GUARD: True`, UFO² will only interact with control types in `CONTROL_LIST`. This prevents accidental dangerous operations but may limit functionality.

---

## Control Filtering

Advanced UI element filtering using semantic and icon similarity.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CONTROL_FILTER_TYPE` | List[String] | `[]` | Filter types to enable |
| `CONTROL_FILTER_TOP_K_PLAN` | Integer | `2` | Top K plans to consider |
| `CONTROL_FILTER_TOP_K_SEMANTIC` | Integer | `15` | Top K controls by text similarity |
| `CONTROL_FILTER_TOP_K_ICON` | Integer | `15` | Top K controls by icon similarity |
| `CONTROL_FILTER_MODEL_SEMANTIC_NAME` | String | `"all-MiniLM-L6-v2"` | Semantic embedding model |
| `CONTROL_FILTER_MODEL_ICON_NAME` | String | `"clip-ViT-B-32"` | Icon embedding model |

### Filter Types

| Type | Description | Use Case |
|------|-------------|----------|
| `"TEXT"` | Text-based filtering | Filter by control labels |
| `"SEMANTIC"` | Semantic similarity | Find similar controls by meaning |
| `"ICON"` | Icon similarity | Find controls by icon appearance |

### Example

```yaml
# Disable filtering (use all controls)
CONTROL_FILTER_TYPE: []

# Enable semantic filtering (recommended)
CONTROL_FILTER_TYPE: ["SEMANTIC"]
CONTROL_FILTER_TOP_K_SEMANTIC: 15
CONTROL_FILTER_MODEL_SEMANTIC_NAME: "all-MiniLM-L6-v2"

# Enable all filtering (most selective)
# CONTROL_FILTER_TYPE: ["TEXT", "SEMANTIC", "ICON"]
# CONTROL_FILTER_TOP_K_SEMANTIC: 20
# CONTROL_FILTER_TOP_K_ICON: 20
```

!!!warning "Performance Impact"
    - Filtering reduces the number of controls sent to LLM (faster, cheaper)
    - But may filter out the target control (less reliable)
    - Start without filtering, add if you have too many controls

---

## API Usage Configuration

Configure native API usage for Office applications.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `USE_APIS` | Boolean | `True` | Enable COM API usage for Office applications |
| `API_PROMPT` | String | `"ufo/prompts/share/base/api.yaml"` | API prompt template |
| `APP_API_PROMPT_ADDRESS` | Dict | See below | App-specific API prompts |

### Default APP_API_PROMPT_ADDRESS

```yaml
APP_API_PROMPT_ADDRESS:
  "WINWORD.EXE": "ufo/prompts/apps/word/api.yaml"
  "EXCEL.EXE": "ufo/prompts/apps/excel/api.yaml"
  "msedge.exe": "ufo/prompts/apps/web/api.yaml"
  "chrome.exe": "ufo/prompts/apps/web/api.yaml"
  "POWERPNT.EXE": "ufo/prompts/apps/powerpoint/api.yaml"
```

### Example

```yaml
# Enable API usage (recommended for Office)
USE_APIS: True
API_PROMPT: "ufo/prompts/share/base/api.yaml"
APP_API_PROMPT_ADDRESS:
  "WINWORD.EXE": "ufo/prompts/apps/word/api.yaml"
  "EXCEL.EXE": "ufo/prompts/apps/excel/api.yaml"

# Disable for pure UI automation
# USE_APIS: False
```

!!!tip "When to Use APIs"
    COM APIs are faster and more reliable for Office applications. Keep `USE_APIS: True` for best results with Word, Excel, PowerPoint.

---

## Complete Example Configuration

Here's a complete, production-ready `system.yaml`:

```yaml
# LLM Parameters
MAX_TOKENS: 2000
MAX_RETRY: 20
TEMPERATURE: 0.0
TOP_P: 0.0
TIMEOUT: 60

# Execution Limits
MAX_STEP: 100
MAX_ROUND: 3
SLEEP_TIME: 1
RECTANGLE_TIME: 1

# Control Backend
CONTROL_BACKEND: ["uia"]
IOU_THRESHOLD_FOR_MERGE: 0.1

# Action Configuration
ACTION_SEQUENCE: True
SHOW_VISUAL_OUTLINE_ON_SCREEN: False
MAXIMIZE_WINDOW: False
JSON_PARSING_RETRY: 3

CLICK_API: "click_input"
AFTER_CLICK_WAIT: 0

INPUT_TEXT_API: "type_keys"
INPUT_TEXT_ENTER: False
INPUT_TEXT_INTER_KEY_PAUSE: 0.05

# Logging
PRINT_LOG: False
LOG_LEVEL: "INFO"
LOG_TO_MARKDOWN: True
LOG_XML: False
CONCAT_SCREENSHOT: False
INCLUDE_LAST_SCREENSHOT: True
SCREENSHOT_TO_MEMORY: True
REQUEST_TIMEOUT: 250

# MCP Settings
USE_MCP: True
MCP_SERVERS_CONFIG: "config/ufo/mcp.yaml"
MCP_PREFERRED_APPS:
  - "Code.exe"
  - "WindowsTerminal.exe"
MCP_FALLBACK_TO_UI: True
MCP_TOOL_TIMEOUT: 30
MCP_LOG_EXECUTION: False

# Safety
SAFE_GUARD: True
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

# API Usage
USE_APIS: True
API_PROMPT: "ufo/prompts/share/base/api.yaml"
APP_API_PROMPT_ADDRESS:
  "WINWORD.EXE": "ufo/prompts/apps/word/api.yaml"
  "EXCEL.EXE": "ufo/prompts/apps/excel/api.yaml"
  "msedge.exe": "ufo/prompts/apps/web/api.yaml"

# Control Filtering (disabled by default)
CONTROL_FILTER_TYPE: []
CONTROL_FILTER_TOP_K_PLAN: 2
CONTROL_FILTER_TOP_K_SEMANTIC: 15
CONTROL_FILTER_TOP_K_ICON: 15
CONTROL_FILTER_MODEL_SEMANTIC_NAME: "all-MiniLM-L6-v2"
CONTROL_FILTER_MODEL_ICON_NAME: "clip-ViT-B-32"
```

---

## Programmatic Access

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# Access system settings
max_step = config.system.max_step
log_level = config.system.log_level
control_backends = config.system.control_backend

# Check MCP settings
if config.system.use_mcp:
    mcp_config_path = config.system.mcp_servers_config
    print(f"MCP enabled, config: {mcp_config_path}")

# Modify at runtime (not recommended)
# config.system.max_step = 200
```

---

## Troubleshooting

### Issue 1: Tasks Failing After X Steps

!!!bug "Error Message"
    ```
    Task stopped: Maximum steps (50) reached
    ```
    
    **Solution**: Increase `MAX_STEP`
    ```yaml
    MAX_STEP: 100  # or higher
    ```

### Issue 2: Controls Not Detected

**Symptom:** UFO² can't find UI elements

**Solutions:**
1. Try enabling omniparser for vision-based detection:
   ```yaml
   CONTROL_BACKEND: ["uia", "omniparser"]
   ```
2. Disable filtering:
   ```yaml
   CONTROL_FILTER_TYPE: []
   ```

### Issue 3: Actions Too Fast

**Symptom:** Actions execute before UI is ready

**Solution:** Add delays
```yaml
SLEEP_TIME: 2
AFTER_CLICK_WAIT: 1
```

### Issue 4: Logs Too Verbose

**Symptom:** Too much console output

**Solution:** Reduce logging
```yaml
    PRINT_LOG: False
    LOG_LEVEL: "WARNING"
    ```

---

## Performance Tuning

### For Speed

```yaml
MAX_STEP: 50
SLEEP_TIME: 0
CONTROL_BACKEND: ["uia"]
CONTROL_FILTER_TYPE: ["SEMANTIC"]  # Reduce LLM input
ACTION_SEQUENCE: True  # Multi-action in one step
```

### For Reliability

```yaml
MAX_STEP: 100
MAX_ROUND: 3
SLEEP_TIME: 2
AFTER_CLICK_WAIT: 1
CONTROL_BACKEND: ["uia"]
CONTROL_FILTER_TYPE: []  # Don't filter out controls
```

### For Debugging

```yaml
PRINT_LOG: True
LOG_LEVEL: "DEBUG"
LOG_XML: True
SHOW_VISUAL_OUTLINE_ON_SCREEN: True
MCP_LOG_EXECUTION: True
```

---

## Related Documentation

- **[Agent Configuration](agents_config.md)** - LLM and API settings
- **[MCP Configuration](mcp_reference.md)** - Tool server configuration
- **[RAG Configuration](rag_config.md)** - Knowledge retrieval

## Summary

**Key Takeaways:**

✅ **Default settings work** - Start with defaults, adjust as needed  
✅ **Increase MAX_STEP** for complex tasks  
✅ **Use ["uia"]** for control detection  
✅ **Enable ACTION_SEQUENCE** for faster execution  
✅ **Adjust logging** based on dev vs production  
✅ **Enable MCP** for better Office automation

**Fine-tune system settings for optimal performance!** ⚙️
