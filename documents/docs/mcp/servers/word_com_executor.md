# WordCOMExecutor Server

## Overview

**WordCOMExecutor** provides Microsoft Word automation via COM API for efficient document manipulation beyond UI automation.

**Server Type:** Action  
**Deployment:** Local (in-process)  
**Agent:** AppAgent  
**Target Application:** Microsoft Word (`WINWORD.EXE`)  
**LLM-Selectable:** ✅ Yes

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `WordCOMExecutor` |
| **Server Name** | `UFO UI AppAgent Action MCP Server` |
| **Platform** | Windows |
| **Requires** | Microsoft Word (COM interface) |
| **Tool Type** | `action` |

## Tools Summary

| Tool Name | Description |
|-----------|-------------|
| `insert_table` | Insert table into document |
| `select_text` | Select specific text |
| `select_table` | Select table by index |
| `select_paragraph` | Select paragraph range |
| `save_as` | Save/export document |
| `set_font` | Set font properties for selected text |

## Tool Details

### insert_table

Insert a table into the Word document at the current cursor position.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `rows` | `int` | ✅ Yes | Number of rows in the table |
| `columns` | `int` | ✅ Yes | Number of columns in the table |

#### Returns

`str` - Result message

#### Example

```python
# Insert 3x4 table
await computer.run_actions([
    MCPToolCall(
        tool_key="action::insert_table",
        tool_name="insert_table",
        parameters={"rows": 3, "columns": 4}
    )
])
```

---

### select_text

Select exact text in the document for further operations (formatting, deletion, etc.).

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | `str` | ✅ Yes | Exact text to select |

#### Returns

`str` - Selected text if successful, or "text not found" message

#### Example

```python
# Select specific text
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_text",
        tool_name="select_text",
        parameters={"text": "Annual Report 2024"}
    )
])

# Then format it
await computer.run_actions([
    MCPToolCall(
        tool_key="action::set_font",
        tool_name="set_font",
        parameters={"font_name": "Arial", "font_size": 18}
    )
])
```

---

### select_table

Select a table in the document by its index (1-based).

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `number` | `int` | ✅ Yes | Table index (1-based) |

#### Returns

`str` - Success message or "out of range" message

#### Example

```python
# Select first table
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_table",
        tool_name="select_table",
        parameters={"number": 1}
    )
])
```

---

### select_paragraph

Select a range of paragraphs in the document.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_index` | `int` | ✅ Yes | - | Start paragraph index |
| `end_index` | `int` | ✅ Yes | - | End paragraph index (`-1` = end of document) |
| `non_empty` | `bool` | No | `True` | Select only non-empty paragraphs |

#### Returns

`str` - Result message

#### Example

```python
# Select paragraphs 1-5 (non-empty only)
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_paragraph",
        tool_name="select_paragraph",
        parameters={
            "start_index": 1,
            "end_index": 5,
            "non_empty": True
        }
    )
])

# Select from paragraph 10 to end
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_paragraph",
        tool_name="select_paragraph",
        parameters={"start_index": 10, "end_index": -1}
    )
])
```

---

### save_as

Save or export Word document to specified format. **Fastest way to save documents.**

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_dir` | `str` | No | `""` | Directory path (empty = current directory) |
| `file_name` | `str` | No | `""` | Filename without extension (empty = current name) |
| `file_ext` | `str` | No | `""` | File extension (empty = `.pdf`) |

#### Supported Extensions

- `.pdf` - PDF format (default)
- `.docx` - Word document
- `.txt` - Plain text
- `.html` - HTML format
- `.rtf` - Rich Text Format

#### Returns

`str` - Success/failure message

#### Example

```python
# Save as PDF in current directory
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        tool_name="save_as",
        parameters={
            "file_dir": "",
            "file_name": "",
            "file_ext": ""  # Defaults to .pdf
        }
    )
])

# Save as DOCX with specific name and path
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        tool_name="save_as",
        parameters={
            "file_dir": "C:\\Documents\\Reports",
            "file_name": "Q4_Report_2024",
            "file_ext": ".docx"
        }
    )
])
```

---

### set_font

Set font properties for currently selected text.

!!!warning "Selection Required"
    Text must be selected first using `select_text`, `select_paragraph`, or manual selection.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `font_name` | `str` | No | `None` | Font name (e.g., "Arial", "Times New Roman", "宋体") |
| `font_size` | `int` | No | `None` | Font size in points |

#### Returns

`str` - Font change confirmation or "no text selected" message

#### Example

```python
# Select text first
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_text",
        parameters={"text": "Important Notice"}
    )
])

# Set font to Arial 16pt
await computer.run_actions([
    MCPToolCall(
        tool_key="action::set_font",
        tool_name="set_font",
        parameters={"font_name": "Arial", "font_size": 16}
    )
])

# Change only size
await computer.run_actions([
    MCPToolCall(
        tool_key="action::set_font",
        tool_name="set_font",
        parameters={"font_size": 20}  # Keep current font name
    )
])
```

## Configuration

```yaml
AppAgent:
  # Word-specific configuration
  WINWORD.EXE:
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: WordCOMExecutor  # Add COM automation
        type: local
        reset: true  # Reset COM state when switching documents
```

### Configuration Options

| Option | Value | Description |
|--------|-------|-------------|
| `reset` | `true` | **Recommended**: Reset COM state between documents to prevent data leakage |
| `reset` | `false` | Keep COM state across documents (faster but risky) |

## Best Practices

### 1. Use COM for Bulk Operations

```python
# ✅ Good: Fast COM API
await computer.run_actions([
    MCPToolCall(tool_key="action::insert_table", parameters={"rows": 10, "columns": 5})
])

# ❌ Bad: Slow UI automation
for i in range(10):
    await computer.run_actions([
        MCPToolCall(tool_key="action::click_input", ...)  # Click Insert Table
    ])
```

### 2. Prefer save_as Over Manual Saving

```python
# ✅ Good: One command
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        parameters={"file_dir": "C:\\Reports", "file_name": "report", "file_ext": ".pdf"}
    )
])

# ❌ Bad: Multiple UI steps
await computer.run_actions([
    MCPToolCall(tool_key="action::keyboard_input", parameters={"keys": "{VK_CONTROL}s"})
])
# ... then navigate save dialog ...
```

### 3. Select Before Formatting

```python
# ✅ Good: Select then format
await computer.run_actions([
    MCPToolCall(tool_key="action::select_text", parameters={"text": "Title"})
])
await computer.run_actions([
    MCPToolCall(tool_key="action::set_font", parameters={"font_size": 24})
])

# ❌ Bad: Format without selection
await computer.run_actions([
    MCPToolCall(tool_key="action::set_font", parameters={"font_size": 24})
])  # Fails: "no text selected"
```

## Use Cases

### Document Report Generation

```python
# 1. Select title
await computer.run_actions([
    MCPToolCall(tool_key="action::select_paragraph", parameters={"start_index": 1, "end_index": 1})
])

# 2. Format title
await computer.run_actions([
    MCPToolCall(tool_key="action::set_font", parameters={"font_name": "Arial", "font_size": 20})
])

# 3. Insert data table
await computer.run_actions([
    MCPToolCall(tool_key="action::insert_table", parameters={"rows": 5, "columns": 3})
])

# 4. Save as PDF
await computer.run_actions([
    MCPToolCall(tool_key="action::save_as", parameters={"file_ext": ".pdf"})
])
```

## Related Documentation

- [ExcelCOMExecutor](./excel_com_executor.md) - Excel COM automation
- [PowerPointCOMExecutor](./ppt_com_executor.md) - PowerPoint COM automation
- [AppUIExecutor](./app_ui_executor.md) - UI-based Word automation
- [Action Servers](../action.md) - Action server concepts
