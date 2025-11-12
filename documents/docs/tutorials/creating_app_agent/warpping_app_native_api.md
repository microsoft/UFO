# Wrapping Application Native APIs as MCP Action Servers

UFO² uses **MCP (Model Context Protocol) servers** to expose application native APIs to the AppAgent. This document shows you how to create custom MCP action servers that wrap your application's COM APIs, REST APIs, or other programmable interfaces.

## Overview

While AppAgent can automate applications through UI controls, providing **native API tools** via MCP servers offers significant advantages:

| Automation Method | Speed | Reliability | Use Case |
|-------------------|-------|-------------|----------|
| **UI Automation** | Slower | Prone to UI changes | Visual elements, dialogs, menus |
| **Native API** | ~10x faster | Deterministic | Data manipulation, batch operations |

!!! tip "Hybrid Automation"
    AppAgent combines both approaches - the LLM intelligently selects **GUI tools** (from UIExecutor) or **API tools** (from your custom MCP server) based on the task requirements.

## Prerequisites

Before creating a native API MCP server:

1. **Understand MCP Servers**: Read [Creating MCP Servers Tutorial](../creating_mcp_servers.md)
2. **Know Your API**: Familiarize yourself with your application's COM API, REST API, or SDK
3. **Review Examples**: Study existing servers in `ufo/client/mcp/local_servers/`

## Step-by-Step Guide

### Step 1: Create Your MCP Server File

Create a new Python file in `ufo/client/mcp/local_servers/` for your application's MCP server:

```python
# File: ufo/client/mcp/local_servers/your_app_executor.py

from typing import Annotated, Optional
from fastmcp import FastMCP
from pydantic import Field
from ufo.client.mcp.mcp_registry import MCPRegistry
from ufo.automator.puppeteer import AppPuppeteer
from ufo.automator.action_execution import ActionExecutor
from ufo.agents.processors.schemas.actions import ActionCommandInfo


@MCPRegistry.register_factory_decorator("YourAppExecutor")
def create_your_app_executor(process_name: str, *args, **kwargs) -> FastMCP:
    """
    Create MCP server for YourApp COM API automation.
    
    :param process_name: Process name for UI automation context.
    :return: FastMCP instance with YourApp tools.
    """
    
    # Initialize puppeteer for UI context
    puppeteer = AppPuppeteer(
        process_name=process_name,
        app_root_name="YOURAPP.EXE",  # Your app's executable name
    )
    
    # Create COM API receiver
    puppeteer.receiver_manager.create_api_receiver(
        app_root_name="YOURAPP.EXE",
        process_name=process_name,
    )
    
    executor = ActionExecutor()
    
    def _execute_action(action: ActionCommandInfo) -> dict:
        """Execute action via puppeteer."""
        return executor.execute(action, puppeteer, control_dict={})
    
    # Create FastMCP instance
    mcp = FastMCP("YourApp COM Executor MCP Server")
    
    # Define tools below...
    
    return mcp
```

### Step 2: Define Tool Methods with @mcp.tool()

Add tool methods to your MCP server using the `@mcp.tool()` decorator. Each tool wraps a native API call:

```python
    @mcp.tool()
    def insert_data_table(
        data: Annotated[
            list[list[str]], 
            Field(description="2D array of table data. Example: [['Name', 'Age'], ['Alice', '25']]")
        ],
        start_row: Annotated[
            int, 
            Field(description="Starting row index (1-based).")
        ] = 1,
        start_col: Annotated[
            int, 
            Field(description="Starting column index (1-based).")
        ] = 1,
    ) -> Annotated[str, Field(description="Result message.")]:
        """
        Insert a data table into the application at the specified position.
        Use this for bulk data insertion instead of manual cell-by-cell input.
        
        Example usage:
        - Insert CSV data: insert_data_table(data=csv_data, start_row=1, start_col=1)
        - Add header and rows: insert_data_table(data=[['ID', 'Name'], ['1', 'Alice'], ['2', 'Bob']])
        """
        action = ActionCommandInfo(
            function="insert_table",
            arguments={
                "data": data,
                "start_row": start_row,
                "start_col": start_col,
            },
        )
        return _execute_action(action)
    
    @mcp.tool()
    def format_range(
        start_cell: Annotated[
            str, 
            Field(description="Starting cell address (e.g., 'A1').")
        ],
        end_cell: Annotated[
            str, 
            Field(description="Ending cell address (e.g., 'B10').")
        ],
        font_bold: Annotated[
            Optional[bool], 
            Field(description="Make font bold?")
        ] = None,
        font_size: Annotated[
            Optional[int], 
            Field(description="Font size in points.")
        ] = None,
        background_color: Annotated[
            Optional[str], 
            Field(description="Background color (hex code like '#FF0000' for red).")
        ] = None,
    ) -> Annotated[str, Field(description="Formatting result.")]:
        """
        Apply formatting to a cell range in the application.
        Much faster than clicking format buttons multiple times.
        
        Example:
        - Bold header: format_range(start_cell='A1', end_cell='E1', font_bold=True)
        - Highlight cells: format_range(start_cell='A2', end_cell='A10', background_color='#FFFF00')
        """
        action = ActionCommandInfo(
            function="format_cells",
            arguments={
                "start_cell": start_cell,
                "end_cell": end_cell,
                "font_bold": font_bold,
                "font_size": font_size,
                "background_color": background_color,
            },
        )
        return _execute_action(action)
    
    @mcp.tool()
    def save_as_pdf(
        output_path: Annotated[
            str, 
            Field(description="Full path for the PDF file (e.g., 'C:/Users/Documents/report.pdf').")
        ],
    ) -> Annotated[str, Field(description="Save result message.")]:
        """
        Export the current document as a PDF file.
        One-click operation - much faster than File > Save As > PDF > Navigate > Save.
        
        Example: save_as_pdf(output_path='C:/Reports/monthly_report.pdf')
        """
        action = ActionCommandInfo(
            function="save_as",
            arguments={
                "file_path": output_path,
                "file_format": "pdf",
            },
        )
        return _execute_action(action)
```

!!!tip "Tool Design Best Practices"
    - **Clear docstrings**: Explain what the tool does, when to use it, and provide examples
    - **Descriptive parameters**: Use `Annotated` with `Field(description=...)`for all parameters
    - **Error handling**: Return descriptive error messages when operations fail
    - **Comprehensive coverage**: Wrap common operations that benefit from API speed

### Step 3: Implement the Underlying API Receiver

The receiver class executes the actual COM API calls. Create it in `ufo/automator/app_apis/`:

```python
# File: ufo/automator/app_apis/your_app/your_app_client.py

import win32com.client
from typing import Dict, Any, List, Optional
from ufo.automator.app_apis.basic import WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic


class YourAppCOMReceiver(WinCOMReceiverBasic):
    """
    COM API receiver for YourApp automation.
    """
    
    _command_registry: Dict[str, type[CommandBasic]] = {}
    
    def __init__(self, app_root_name: str, process_name: str, clsid: str) -> None:
        """
        Initialize the YourApp COM client.
        :param app_root_name: Application root name.
        :param process_name: Process name.
        :param clsid: COM object CLSID.
        """
        super().__init__(app_root_name, process_name, clsid)
    
    def insert_table_data(
        self, 
        data: List[List[str]], 
        start_row: int = 1, 
        start_col: int = 1
    ) -> str:
        """
        Insert table data using COM API.
        :param data: 2D array of table data.
        :param start_row: Starting row (1-based).
        :param start_col: Starting column (1-based).
        :return: Result message.
        """
        try:
            # Access the active document/workbook via COM
            doc = self.com_object.ActiveDocument  # Or ActiveWorkbook for Excel
            
            # Insert data row by row
            for i, row in enumerate(data):
                for j, cell_value in enumerate(row):
                    # Example: Set cell value
                    cell = doc.Tables(1).Cell(start_row + i, start_col + j)
                    cell.Range.Text = str(cell_value)
            
            return f"Successfully inserted {len(data)} rows of data"
        except Exception as e:
            return f"Error inserting table: {str(e)}"
    
    def format_cells(
        self,
        start_cell: str,
        end_cell: str,
        font_bold: Optional[bool] = None,
        font_size: Optional[int] = None,
        background_color: Optional[str] = None,
    ) -> str:
        """
        Format cell range using COM API.
        """
        try:
            doc = self.com_object.ActiveDocument
            range_obj = doc.Range(start_cell, end_cell)
            
            if font_bold is not None:
                range_obj.Font.Bold = font_bold
            if font_size is not None:
                range_obj.Font.Size = font_size
            if background_color is not None:
                # Convert hex to RGB and apply
                range_obj.Shading.BackgroundPatternColor = self._hex_to_rgb(background_color)
            
            return f"Successfully formatted range {start_cell}:{end_cell}"
        except Exception as e:
            return f"Error formatting cells: {str(e)}"
    
    def save_document_as(self, file_path: str, file_format: str) -> str:
        """
        Save document in specified format.
        """
        try:
            doc = self.com_object.ActiveDocument
            
            # Map format string to COM constant
            format_map = {
                "pdf": 17,  # wdFormatPDF
                "docx": 16,  # wdFormatXMLDocument
                # Add more formats as needed
            }
            
            format_code = format_map.get(file_format.lower(), 16)
            doc.SaveAs2(file_path, FileFormat=format_code)
            
            return f"Successfully saved document to {file_path}"
        except Exception as e:
            return f"Error saving document: {str(e)}"
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> int:
        """Convert hex color to RGB integer for COM."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return r + (g << 8) + (b << 16)
```

### Step 4: Create Command Classes

Define command classes that bridge the MCP tools to the receiver methods:

```python
# In the same file: ufo/automator/app_apis/your_app/your_app_client.py

@YourAppCOMReceiver.register
class InsertTableCommand(CommandBasic):
    """Command to insert table data."""
    
    def execute(self) -> Dict[str, Any]:
        """Execute table insertion."""
        return self.receiver.insert_table_data(
            data=self.params.get("data", []),
            start_row=self.params.get("start_row", 1),
            start_col=self.params.get("start_col", 1),
        )


@YourAppCOMReceiver.register
class FormatCellsCommand(CommandBasic):
    """Command to format cell range."""
    
    def execute(self) -> Dict[str, Any]:
        """Execute cell formatting."""
        return self.receiver.format_cells(
            start_cell=self.params.get("start_cell"),
            end_cell=self.params.get("end_cell"),
            font_bold=self.params.get("font_bold"),
            font_size=self.params.get("font_size"),
            background_color=self.params.get("background_color"),
        )


@YourAppCOMReceiver.register
class SaveAsCommand(CommandBasic):
    """Command to save document."""
    
    def execute(self) -> Dict[str, Any]:
        """Execute document save."""
        return self.receiver.save_document_as(
            file_path=self.params.get("file_path"),
            file_format=self.params.get("file_format", "pdf"),
        )
```

!!!note "Command Registration"
    Use `@YourAppCOMReceiver.register` decorator to register each command class with the receiver.

### Step 5: Register Your Receiver in the Factory

Add your receiver to the COM receiver factory in `ufo/automator/app_apis/factory.py`:

```python
def __com_client_mapper(self, app_root_name: str) -> Type[WinCOMReceiverBasic]:
    """Map application to its COM receiver class."""
    mapping = {
        "WINWORD.EXE": WordWinCOMReceiver,
        "EXCEL.EXE": ExcelWinCOMReceiver,
        "POWERPNT.EXE": PowerPointWinCOMReceiver,
        "YOURAPP.EXE": YourAppCOMReceiver,  # Add your app here
    }
    return mapping.get(app_root_name)

def __app_root_mappping(self, app_root_name: str) -> Optional[str]:
    """Map application to its COM CLSID."""
    mapping = {
        "WINWORD.EXE": "Word.Application",
        "EXCEL.EXE": "Excel.Application",
        "POWERPNT.EXE": "PowerPoint.Application",
        "YOURAPP.EXE": "YourApp.Application",  # Add your CLSID here
    }
    return mapping.get(app_root_name)
```

### Step 6: Register the MCP Server in mcp.yaml

Configure the MCP server for your application in `config/ufo/mcp.yaml`:

```yaml
AppAgent:
  YOURAPP.EXE:
    data_collection:
      - namespace: UICollector
        type: local
        reset: false
    action:
      - namespace: AppUIExecutor  # Generic UI automation
        type: local
        reset: false
      - namespace: YourAppExecutor  # Your custom COM API tools
        type: local
        reset: true  # Reset COM state when switching documents
      - namespace: CommandLineExecutor  # Shell commands
        type: local
        reset: false
```

!!!tip "Why `reset: true`?"
    Set `reset: true` for COM-based MCP servers to prevent state leakage when switching between documents or application instances.

### Step 7: Test Your MCP Server

Test your server in isolation before integration:

```python
# File: test_your_app_server.py

import asyncio
from fastmcp.client import Client
from ufo.client.mcp.local_servers.your_app_executor import create_your_app_executor


async def test_server():
    """Test YourApp MCP server."""
    process_name = "your_app_process"
    server = create_your_app_executor(process_name)
    
    async with Client(server) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # Test insert_data_table
        result = await client.call_tool(
            "insert_data_table",
            arguments={
                "data": [["Name", "Age"], ["Alice", "25"], ["Bob", "30"]],
                "start_row": 1,
                "start_col": 1,
            }
        )
        print(f"Insert result: {result.data}")
        
        # Test format_range
        result = await client.call_tool(
            "format_range",
            arguments={
                "start_cell": "A1",
                "end_cell": "B1",
                "font_bold": True,
                "font_size": 14,
            }
        )
        print(f"Format result: {result.data}")


if __name__ == "__main__":
    asyncio.run(test_server())
```

## Complete Example: Excel COM Executor

See the complete implementation in UFO²'s codebase:

- **MCP Server**: `ufo/client/mcp/local_servers/excel_wincom_mcp_server.py`
- **COM Receiver**: `ufo/automator/app_apis/excel/excel_client.py`
- **Configuration**: `config/ufo/mcp.yaml` (under `AppAgent.EXCEL.EXE`)

Key features:
- `insert_table`: Bulk data insertion
- `format_cells`: Cell formatting (fonts, colors, borders)
- `create_chart`: Chart generation
- `apply_formula`: Formula application
- `save_as`: Export to PDF/CSV

## Legacy Approach: API Prompt Files (Deprecated)

!!!warning "Deprecated: API Prompt Files"
    The old approach of creating `api.yaml` prompt files and configuring `APP_API_PROMPT_ADDRESS` is **deprecated**. The new MCP architecture provides:
    
    - ✅ **Better tool discovery**: Tools are automatically introspected from MCP servers
    - ✅ **Type safety**: Pydantic models ensure parameter validation
    - ✅ **Cleaner code**: No manual prompt file maintenance
    - ✅ **Better testing**: Direct server testing with FastMCP Client
    
    If you're migrating from the old system, see [Creating MCP Servers Tutorial](../creating_mcp_servers.md).

## Best Practices

### 1. Comprehensive Docstrings

```python
@mcp.tool()
def insert_data_table(...) -> ...:
    """
    Insert a data table into the application at the specified position.
    Use this for bulk data insertion instead of manual cell-by-cell input.
    
    When to use:
    - Inserting CSV/Excel data
    - Creating tables from lists
    - Bulk data population
    
    Example usage:
    - Insert CSV data: insert_data_table(data=csv_data, start_row=1, start_col=1)
    - Add header and rows: insert_data_table(data=[['ID', 'Name'], ['1', 'Alice']])
    """
```

### 2. Error Handling

```python
def insert_table_data(self, data: List[List[str]], ...) -> str:
    """Insert table data using COM API."""
    try:
        # Validate input
        if not data or not data[0]:
            return "Error: Empty data table provided"
        
        # Execute COM operation
        doc = self.com_object.ActiveDocument
        # ... insert logic ...
        
        return f"Successfully inserted {len(data)} rows"
    except Exception as e:
        return f"Error inserting table: {str(e)}"
```

### 3. Parameter Validation

```python
@mcp.tool()
def format_range(
    start_cell: Annotated[
        str, 
        Field(
            description="Starting cell address (e.g., 'A1'). Must be valid Excel notation.",
            pattern=r"^[A-Z]+[0-9]+$"  # Regex validation
        )
    ],
    ...
) -> ...:
    """Format cell range."""
```

### 4. Fallback to UI Automation

Design your API tools to complement (not replace) UI automation:

```python
@mcp.tool()
def apply_table_style(style_name: str) -> str:
    """
    Apply a predefined table style.
    
    Note: For custom styling, use format_range() or UI automation
    via AppUIExecutor::click_input() on the Design tab.
    """
```

## Troubleshooting

### Issue: COM Object Not Found

**Symptom**: `pywintypes.com_error: (-2147221005, 'Invalid class string', None, None)`

**Solution**:
1. Verify the CLSID is correct for your application
2. Ensure the application is installed and registered
3. Check if the application supports COM automation

### Issue: Permission Denied

**Symptom**: `com_error: (-2147352567, 'Exception occurred.', ...)`

**Solution**:
- Run UFO² with administrator privileges
- Check application security settings
- Verify COM permissions in `dcomcnfg`

### Issue: Tools Not Appearing in LLM Prompt

**Symptom**: AppAgent doesn't use your API tools

**Solution**:
1. Verify MCP server is registered in `mcp.yaml`
2. Check namespace matches: `@MCPRegistry.register_factory_decorator("YourAppExecutor")`
3. Ensure server is under `action:` (not `data_collection:`)
4. Test server independently with FastMCP Client

## Related Documentation

**Core Tutorials:**

- **[Creating MCP Servers Tutorial](../creating_mcp_servers.md)** - Complete MCP server development guide
- [Overview: Enhancing AppAgent Capabilities](./overview.md) - Learn about all enhancement approaches
- [Help Document Provision](./help_document_provision.md) - Provide knowledge through documentation
- [User Demonstrations Provision](./demonstration_provision.md) - Teach through examples

**MCP Documentation:**

- [MCP Configuration](../../mcp/configuration.md) - Registering MCP servers
- [MCP Overview](../../mcp/overview.md) - Understanding MCP architecture
- [WordCOMExecutor](../../mcp/servers/word_com_executor.md) - Reference implementation
- [ExcelCOMExecutor](../../mcp/servers/excel_com_executor.md) - Reference implementation

**Advanced Features:**

- [Hybrid GUI–API Actions](../../ufo2/core_features/hybrid_actions.md) - How AppAgent chooses tools
- [Knowledge Substrate Overview](../../ufo2/core_features/knowledge_substrate/overview.md) - Understanding the RAG architecture

---

By following this guide, you've successfully wrapped your application's native API as an MCP action server, enabling the AppAgent to perform fast, reliable automation through direct API calls!
