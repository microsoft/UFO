# Action Servers

## Overview

**Action Servers** provide tools that modify system state by executing actions. These servers enable agents to interact with the environment, automate tasks, and implement decisions.

!!!success "LLM-Selectable Tools"
    **Action servers are the only servers whose tools can be selected by the LLM agent.** At each step, the agent chooses which action tool to execute based on the task and current context.
    
    - **LLM Decision**: Agent actively selects from available action tools
    - **Dynamic Selection**: Different action chosen at each step based on needs
    - **Tool Visibility**: All action tools are presented to the LLM in the prompt
    
    **[Data Collection Servers](./data_collection.md) are NOT LLM-selectable** - they are automatically invoked by the framework.

!!!warning "How Tool Metadata Becomes LLM Instructions"
    **Every action tool's implementation directly affects what the LLM sees and understands.** The UFO² framework automatically extracts:
    
    - **`Annotated` type hints**: Parameter types, constraints, and descriptions
    - **Docstrings**: Tool purpose, parameter explanations, return value descriptions
    - **Function signatures**: Parameter names, defaults, required vs. optional
    
    These are **automatically assembled into structured tool instructions** that appear in the LLM's prompt. The LLM uses these instructions to:
    
    1. **Understand** what each tool does
    2. **Select** the appropriate tool for each step
    3. **Call** the tool with correct parameters
    
    **Therefore, developers MUST write clear, comprehensive metadata:**
    
    ```python
    # ✅ GOOD: Clear metadata helps LLM understand and use the tool correctly
    @mcp.tool()
    def click_input(
        control_id: Annotated[str, "The unique ID of the control to click"],
        button: Annotated[Literal["left", "right"], "Mouse button to use"] = "left",
    ) -> Annotated[str, "Success message or error description"]:
        """
        Click on a UI control by its ID.
        
        Use this tool when you need to interact with buttons, links, or other 
        clickable elements. The control_id must be obtained from observation.
        
        Args:
            control_id: The numeric ID from the annotated screenshot
            button: Which mouse button to click (left for normal clicks, right for context menus)
        
        Returns:
            A success message if the click succeeded, or an error description if it failed.
            
        Example:
            click_input(control_id="5", button="left")  # Clicks button with ID 5
        """
        # Implementation...
    
    # ❌ BAD: Poor metadata confuses LLM, leads to incorrect tool usage
    @mcp.tool()
    def click_input(control_id, button="left"):
        """Click something."""
        # Implementation...
    ```
    
    **Impact on LLM Performance:**
    
    - **Good metadata** → LLM selects correct tool, provides valid parameters → High success rate
    - **Poor metadata** → LLM guesses tool usage, provides invalid parameters → High error rate, wasted API calls
    
    **Best Practices:**
    
    1. ✅ Use `Annotated[type, "description"]` for all parameters
    2. ✅ Write detailed docstrings explaining when and how to use the tool
    3. ✅ Include examples in docstrings showing typical usage
    4. ✅ Describe return values clearly
    5. ✅ Specify constraints (e.g., valid ranges, formats, dependencies)
    6. ❌ Don't leave parameters undocumented
    7. ❌ Don't write vague descriptions like "some value" or "the thing"
    
    **See individual server documentation for examples of well-documented tools.**

```
┌─────────────────────────────────────────────────────┐
│         Action Execution Flow (LLM-Driven)          │
└─────────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │  LLM Agent Decision       │
        │  (Selects Action Tool)    │
        └─────────────┬─────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌───────────────┐          ┌───────────────┐
│  Agent        │          │  MCP Server   │
│  Decision     │──────────│  Action Server│
│  "Click OK"   │  Choose  └───────────────┘
└───────────────┘   Tool           │
                                   ▼
                          ┌───────────────────┐
                          │   click()         │
                          │   type_text()     │
                          │   insert_table()  │
                          │   run_shell()     │
                          └───────────────────┘
                                   │
                                   ▼
                          ┌───────────────────┐
                          │  System Modified  │
                          │  ✅ Side Effects   │
                          └───────────────────┘
```

!!!warning "Side Effects"
    - **✅ Modifies State**: Can change system, files, UI
    - **⚠️ Not Idempotent**: Same action may have different results
    - **🔒 Use with Caution**: Always verify before executing
    - **📝 Audit Trail**: Log all actions for debugging
    - **🤖 LLM-Controlled**: Agent decides when and which action to execute

## Tool Type Identifier

All action tools use the tool type:

```python
tool_type = "action"
```

Tool keys follow the format:

```python
tool_key = "action::{tool_name}"

# Examples:
"action::click"
"action::type_text"
"action::run_shell"
```

## Built-in Action Servers

UFO² provides several built-in action servers for different automation scenarios. Below is a summary - click each server name for detailed documentation including all tools, parameters, and usage examples.

### UI Automation Servers

| Server | Agent | Description | Documentation |
|--------|-------|-------------|---------------|
| **[HostUIExecutor](servers/host_ui_executor.md)** | HostAgent | Window selection and desktop-level UI automation | [Full Details →](servers/host_ui_executor.md) |
| **[AppUIExecutor](servers/app_ui_executor.md)** | AppAgent | Application-level UI automation (clicks, typing, scrolling) | [Full Details →](servers/app_ui_executor.md) |

### Command Execution Servers

| Server | Platform | Description | Documentation |
|--------|----------|-------------|---------------|
| **[CommandLineExecutor](servers/command_line_executor.md)** | Windows | Execute shell commands and launch applications | [Full Details →](servers/command_line_executor.md) |
| **[BashExecutor](servers/bash_executor.md)** | Linux | Execute Linux commands via HTTP server | [Full Details →](servers/bash_executor.md) |

### Office Automation Servers (COM API)

| Server | Application | Description | Documentation |
|--------|-------------|-------------|---------------|
| **[WordCOMExecutor](servers/word_com_executor.md)** | Microsoft Word | Word document automation (insert table, format text, etc.) | [Full Details →](servers/word_com_executor.md) |
| **[ExcelCOMExecutor](servers/excel_com_executor.md)** | Microsoft Excel | Excel automation (insert data, create charts, etc.) | [Full Details →](servers/excel_com_executor.md) |
| **[PowerPointCOMExecutor](servers/ppt_com_executor.md)** | Microsoft PowerPoint | PowerPoint automation (slides, formatting, etc.) | [Full Details →](servers/ppt_com_executor.md) |

### Specialized Servers

| Server | Purpose | Description | Documentation |
|--------|---------|-------------|---------------|
| **[PDFReaderExecutor](servers/pdf_reader_executor.md)** | PDF Processing | Extract text from PDFs with human simulation | [Full Details →](servers/pdf_reader_executor.md) |
| **[ConstellationEditor](servers/constellation_editor.md)** | Multi-Device | Create and manage multi-device task workflows | [Full Details →](servers/constellation_editor.md) |
| **[HardwareExecutor](servers/hardware_executor.md)** | Hardware Control | Control Arduino, robot arms, test fixtures, mobile devices | [Full Details →](servers/hardware_executor.md) |

!!!tip "Quick Reference"
    Each server documentation page includes:
    
    - 📋 **Complete tool reference** with all parameters and return values
    - 💡 **Code examples** showing actual usage patterns
    - ⚙️ **Configuration examples** for different scenarios
    - ✅ **Best practices** with do's and don'ts
    - 🎯 **Use cases** with complete workflows

## Configuration Examples

Action servers are configured in `config/ufo/mcp.yaml`. Each server's documentation provides detailed configuration examples.

### Basic Configuration

```yaml
HostAgent:
  default:
    action:
      - namespace: HostUIExecutor
        type: local
        reset: false
      - namespace: CommandLineExecutor
        type: local
        reset: false
```

### App-Specific Configuration

```yaml
AppAgent:
  # Default configuration for all apps
  default:
    action:
      - namespace: AppUIExecutor
        type: local
        reset: false
  
  # Word-specific configuration
  WINWORD.EXE:
    action:
      - namespace: AppUIExecutor
        type: local
        reset: false
      - namespace: WordCOMExecutor
        type: local
        reset: true  # Reset when switching documents
  
  # Excel-specific configuration
  EXCEL.EXE:
    action:
      - namespace: AppUIExecutor
        type: local
        reset: false
      - namespace: ExcelCOMExecutor
        type: local
        reset: true  # Reset when switching workbooks
```

### Multi-Platform Configuration

```yaml
# Windows agent
HostAgent:
  default:
    action:
      - namespace: HostUIExecutor
        type: local
      - namespace: CommandLineExecutor
        type: local

# Linux agent
LinuxAgent:
  default:
    action:
      - namespace: BashExecutor
        type: http
        host: "192.168.1.100"
        port: 8010
        path: "/mcp"
```

For complete configuration details, see:

- [MCP Configuration Guide](configuration.md) - Complete configuration reference
- Individual server documentation for server-specific configuration options

## Best Practices

### General Principles

#### 1. Verify Before Acting

Always observe before executing actions:

```python
# ✅ Good: Verify target exists
control_info = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::get_control_info", ...)
])

if control_info[0].data and control_info[0].data["is_enabled"]:
    await computer.run_actions([
        MCPToolCall(tool_key="action::click", ...)
    ])
```

#### 2. Handle Action Failures

Actions can fail for many reasons - always implement error handling and retries.

#### 3. Validate Inputs

Never execute unsanitized commands, especially with `run_shell` and similar tools.

#### 4. Wait for Action Completion

Some actions need time to complete - add appropriate delays after launching applications or triggering UI changes.

For detailed best practices including code examples, error handling patterns, and common pitfalls, see the individual server documentation:

- [HostUIExecutor Best Practices](servers/host_ui_executor.md)
- [AppUIExecutor Best Practices](servers/app_ui_executor.md)
- [CommandLineExecutor Best Practices](servers/command_line_executor.md)
- [WordCOMExecutor Best Practices](servers/word_com_executor.md)
- [ExcelCOMExecutor Best Practices](servers/excel_com_executor.md)
- [PowerPointCOMExecutor Best Practices](servers/ppt_com_executor.md)
- [PDFReaderExecutor Best Practices](servers/pdf_reader_executor.md)
- [ConstellationEditor Best Practices](servers/constellation_editor.md)
- [HardwareExecutor Best Practices](servers/hardware_executor.md)
- [BashExecutor Best Practices](servers/bash_executor.md)

## Common Use Cases

For complete use case examples with detailed workflows, see the individual server documentation:

### UI Automation

- **Form Filling**: [AppUIExecutor](servers/app_ui_executor.md)
- **Window Management**: [HostUIExecutor](servers/host_ui_executor.md)

### Document Automation

- **Word Processing**: [WordCOMExecutor](servers/word_com_executor.md)
- **Excel Data Processing**: [ExcelCOMExecutor](servers/excel_com_executor.md)
- **PowerPoint Generation**: [PowerPointCOMExecutor](servers/ppt_com_executor.md)
- **PDF Extraction**: [PDFReaderExecutor](servers/pdf_reader_executor.md)

### System Automation

- **Application Launching**: [CommandLineExecutor](servers/command_line_executor.md)
- **Linux Command Execution**: [BashExecutor](servers/bash_executor.md)

### Multi-Device Workflows

- **Task Distribution**: [ConstellationEditor](servers/constellation_editor.md)
- **Hardware Control**: [HardwareExecutor](servers/hardware_executor.md)

## Error Handling

Action servers implement robust error handling with timeouts and retries. For detailed error handling patterns specific to each server, see:

- [HostUIExecutor](servers/host_ui_executor.md)
- [AppUIExecutor](servers/app_ui_executor.md)
- [CommandLineExecutor](servers/command_line_executor.md)
- [BashExecutor](servers/bash_executor.md)
- And other server-specific documentation

### General Timeout Handling

Actions are executed with a timeout (default: 6000 seconds):

```python
try:
    result = await computer.run_actions([
        MCPToolCall(tool_key="action::run_shell", ...)
    ])
except asyncio.TimeoutError:
    logger.error("Action timed out after 6000 seconds")
    # Cleanup or retry logic...
```

### General Retry Pattern

```python
async def retry_action(action: MCPToolCall, max_retries: int = 3):
    """Retry an action with exponential backoff."""
    for attempt in range(max_retries):
        try:
            result = await computer.run_actions([action])
            if not result[0].is_error:
                return result[0]
            logger.warning(f"Attempt {attempt + 1} failed: {result[0].content}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Exception on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    raise ValueError(f"Action failed after {max_retries} attempts")
```

## Integration with Data Collection

Actions should be paired with data collection for verification:

```python
# Pattern: Observe → Act → Verify

# 1. Observe: Capture initial state
before_screenshot = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::take_screenshot", ...)
])

# 2. Act: Execute action
action_result = await computer.run_actions([
    MCPToolCall(tool_key="action::click", ...)
])

# 3. Verify: Check result
await asyncio.sleep(1)  # Wait for UI update
after_screenshot = await computer.run_actions([
    MCPToolCall(tool_key="data_collection::take_screenshot", ...)
])
```

For more details, see:

- [Data Collection Servers](data_collection.md) - Observation tools
- [UICollector Documentation](servers/ui_collector.md) - Complete data collection reference

## Related Documentation

- [Data Collection Servers](data_collection.md) - Observation tools
- [Configuration Guide](configuration.md) - Configure action servers
- [Local Servers](local_servers.md) - Built-in action servers overview
- [Remote Servers](remote_servers.md) - HTTP deployment for actions
- [Computer](../client/computer.md) - Action execution layer
- [MCP Overview](overview.md) - High-level MCP architecture

!!!danger "Safety Reminder"
    Action servers can **modify system state**. Always:
    
    1. ✅ **Validate inputs** before execution
    2. ✅ **Verify targets** exist and are accessible
    3. ✅ **Log all actions** for audit trail
    4. ✅ **Handle failures** gracefully with retries
    5. ✅ **Test in safe environment** before production use
