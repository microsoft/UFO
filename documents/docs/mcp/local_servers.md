# Local MCP Servers

Local MCP servers run in-process with the UFO² agent, providing fast and efficient access to tools without network overhead. They are the most common server type for built-in functionality.

**For remote HTTP servers** (BashExecutor, HardwareExecutor, MobileExecutor), see [Remote Servers](./remote_servers.md).

## Overview

UFO² includes several built-in local MCP servers organized by functionality. This page provides a quick reference - click each server name for complete documentation.

| Server | Type | Description | Full Documentation |
|--------|------|-------------|-------------------|
| **UICollector** | Data Collection | Windows UI observation | **[→ Full Docs](servers/ui_collector.md)** |
| **HostUIExecutor** | Action | Desktop-level UI automation | **[→ Full Docs](servers/host_ui_executor.md)** |
| **AppUIExecutor** | Action | Application-level UI automation | **[→ Full Docs](servers/app_ui_executor.md)** |
| **CommandLineExecutor** | Action | Shell command execution | **[→ Full Docs](servers/command_line_executor.md)** |
| **WordCOMExecutor** | Action | Microsoft Word COM API | **[→ Full Docs](servers/word_com_executor.md)** |
| **ExcelCOMExecutor** | Action | Microsoft Excel COM API | **[→ Full Docs](servers/excel_com_executor.md)** |
| **PowerPointCOMExecutor** | Action | Microsoft PowerPoint COM API | **[→ Full Docs](servers/ppt_com_executor.md)** |
| **PDFReaderExecutor** | Action | PDF text extraction | **[→ Full Docs](servers/pdf_reader_executor.md)** |
| **ConstellationEditor** | Action | Multi-device task orchestration | **[→ Full Docs](servers/constellation_editor.md)** |

---

## Server Summaries

### UICollector

**Type**: Data Collection (read-only, automatically invoked)  
**Platform**: Windows  
**Tools**: 8 tools for screenshots, window lists, control info, and annotations

**[→ See complete UICollector documentation](servers/ui_collector.md)** for all tool details, parameters, return values, and examples.

---

### HostUIExecutor

**Type**: Action (LLM-selectable, state-modifying)  
**Platform**: Windows  
**Agent**: HostAgent  
**Tool**: `select_application_window` - Window selection and focus management

**[→ See complete HostUIExecutor documentation](servers/host_ui_executor.md)** for tool specifications and workflow examples.

---

### AppUIExecutor

**Type**: Action (LLM-selectable, GUI automation)  
**Platform**: Windows  
**Agent**: AppAgent  
**Tools**: 9 tools for clicks, typing, scrolling, and UI interaction

**[→ See complete AppUIExecutor documentation](servers/app_ui_executor.md)** for all automation tools and usage patterns.

---

### CommandLineExecutor

**Type**: Action (LLM-selectable, shell execution)  
**Platform**: Cross-platform  
**Agent**: HostAgent, AppAgent  
**Tool**: `run_shell` - Execute shell commands

**[→ See complete CommandLineExecutor documentation](servers/command_line_executor.md)** for security guidelines and examples.

---

### WordCOMExecutor

**Type**: Action (LLM-selectable, Word COM API)  
**Platform**: Windows  
**Agent**: AppAgent (WINWORD.EXE only)  
**Tools**: 6 tools for Word document automation

**[→ See complete WordCOMExecutor documentation](servers/word_com_executor.md)** for all Word automation tools.

---

### ExcelCOMExecutor

**Type**: Action (LLM-selectable, Excel COM API)  
**Platform**: Windows  
**Agent**: AppAgent (EXCEL.EXE only)  
**Tools**: 6 tools for Excel automation

**[→ See complete ExcelCOMExecutor documentation](servers/excel_com_executor.md)** for all Excel manipulation tools.

---

### PowerPointCOMExecutor

**Type**: Action (LLM-selectable, PowerPoint COM API)  
**Platform**: Windows  
**Agent**: AppAgent (POWERPNT.EXE only)  
**Tools**: 2 tools for PowerPoint automation

**[→ See complete PowerPointCOMExecutor documentation](servers/ppt_com_executor.md)** for PowerPoint tools and examples.

---

### PDFReaderExecutor

**Type**: Action (LLM-selectable, PDF text extraction)  
**Platform**: Windows  
**Agent**: AppAgent (explorer.exe)  
**Tools**: 3 tools for PDF text extraction with human simulation

**[→ See complete PDFReaderExecutor documentation](servers/pdf_reader_executor.md)** for PDF extraction tools and workflows.

---

### ConstellationEditor

**Type**: Action (LLM-selectable, multi-device orchestration)  
**Platform**: Cross-platform  
**Agent**: ConstellationAgent  
**Tools**: 7 tools for task and dependency management

**[→ See complete ConstellationEditor documentation](servers/constellation_editor.md)** for multi-device workflow tools.

---

## Configuration

All local servers are configured in `config/ufo/mcp.yaml`. For detailed configuration options, see:

- [MCP Configuration Guide](./configuration.md) - Complete configuration reference
- Individual server documentation for server-specific configuration

**Example configuration:**

```yaml
AppAgent:
  WINWORD.EXE:
    data_collection:
      - namespace: UICollector
        type: local
        reset: false
    action:
      - namespace: AppUIExecutor  # GUI automation
        type: local
        reset: false
      - namespace: WordCOMExecutor  # API automation
        type: local
        reset: true  # Reset when switching documents
      - namespace: CommandLineExecutor
        type: local
        reset: false
```

## See Also

- [MCP Overview](./overview.md) - MCP architecture and concepts
- [Data Collection Servers](./data_collection.md) - Data collection overview
- [Action Servers](./action.md) - Action server overview
- [MCP Configuration](./configuration.md) - Configuration guide
- [Remote Servers](./remote_servers.md) - HTTP/Stdio deployment
- [Creating Custom MCP Servers Tutorial](../tutorials/creating_mcp_servers.md) - Learn to build your own servers
- [HostAgent Overview](../ufo2/host_agent/overview.md) - HostAgent architecture
- [AppAgent Overview](../ufo2/app_agent/overview.md) - AppAgent architecture
- [Hybrid Actions](../ufo2/core_features/hybrid_actions.md) - GUI + API dual-mode automation
