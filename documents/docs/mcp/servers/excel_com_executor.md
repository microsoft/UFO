# ExcelCOMExecutor Server

## Overview

**ExcelCOMExecutor** provides Microsoft Excel automation via COM API for efficient spreadsheet manipulation.

**Server Type:** Action  
**Deployment:** Local (in-process)  
**Agent:** AppAgent  
**Target Application:** Microsoft Excel (`EXCEL.EXE`)  
**LLM-Selectable:** ✅ Yes

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `ExcelCOMExecutor` |
| **Platform** | Windows |
| **Requires** | Microsoft Excel (COM interface) |
| **Tool Type** | `action` |

## Tools Summary

| Tool Name | Description |
|-----------|-------------|
| `table2markdown` | Convert Excel sheet to Markdown table |
| `insert_excel_table` | Insert table data into sheet |
| `select_table_range` | Select cell range |
| `save_as` | Save/export workbook |
| `reorder_columns` | Reorder columns in sheet |
| `get_range_values` | Get values from cell range |

## Tool Details

### table2markdown

Convert an Excel sheet to Markdown format table.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sheet_name` | `str` or `int` | ✅ Yes | Sheet name or index (1-based) |

#### Returns

`str` - Markdown-formatted table

#### Example

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::table2markdown",
        tool_name="table2markdown",
        parameters={"sheet_name": "Sales Data"}
    )
])

# Output:
# | Product | Q1 | Q2 | Q3 | Q4 |
# |---------|----|----|----|----|
# | A       | 100| 150| 120| 180|
# | B       | 200| 180| 210| 190|
```

---

### insert_excel_table

Insert a table (2D list) into an Excel sheet at a specified position.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table` | `List[List[Any]]` | ✅ Yes | 2D list of values (strings/numbers) |
| `sheet_name` | `str` | ✅ Yes | Target sheet name |
| `start_row` | `int` | ✅ Yes | Start row (1-based) |
| `start_col` | `int` | ✅ Yes | Start column (1-based) |

#### Returns

`str` - Success message

#### Example

```python
# Define table data
data = [
    ["Name", "Age", "Gender"],
    ["Alice", 30, "Female"],
    ["Bob", 25, "Male"],
    ["Charlie", 35, "Male"]
]

# Insert at A1
await computer.run_actions([
    MCPToolCall(
        tool_key="action::insert_excel_table",
        tool_name="insert_excel_table",
        parameters={
            "table": data,
            "sheet_name": "Sheet1",
            "start_row": 1,
            "start_col": 1
        }
    )
])
```

---

### select_table_range

Select a range of cells in a sheet (faster than dragging).

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sheet_name` | `str` | ✅ Yes | Sheet name |
| `start_row` | `int` | ✅ Yes | Start row (1-based) |
| `start_col` | `int` | ✅ Yes | Start column (1=A, 2=B, etc.) |
| `end_row` | `int` | ✅ Yes | End row (`-1` = last row with content) |
| `end_col` | `int` | ✅ Yes | End column (`-1` = last column with content) |

#### Returns

`str` - Selection confirmation message

#### Example

```python
# Select A1:D10
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_table_range",
        tool_name="select_table_range",
        parameters={
            "sheet_name": "Sheet1",
            "start_row": 1,
            "start_col": 1,  # Column A
            "end_row": 10,
            "end_col": 4     # Column D
        }
    )
])

# Select all data (A1 to last used cell)
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_table_range",
        tool_name="select_table_range",
        parameters={
            "sheet_name": "Sheet1",
            "start_row": 1,
            "start_col": 1,
            "end_row": -1,   # Last row with data
            "end_col": -1    # Last column with data
        }
    )
])
```

---

### save_as

Save or export Excel workbook to specified format.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_dir` | `str` | No | `""` | Directory path |
| `file_name` | `str` | No | `""` | Filename without extension |
| `file_ext` | `str` | No | `""` | Extension (default: `.csv`) |

#### Supported Extensions

- `.csv` - CSV format (default)
- `.xlsx` - Excel workbook
- `.xls` - Excel 97-2003 format
- `.txt` - Tab-delimited text
- `.pdf` - PDF format

#### Example

```python
# Save as CSV
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        tool_name="save_as",
        parameters={
            "file_dir": "C:\\Data\\Exports",
            "file_name": "sales_report",
            "file_ext": ".csv"
        }
    )
])
```

---

### reorder_columns

Reorder columns in a sheet based on desired column name order.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sheet_name` | `str` | ✅ Yes | Sheet name |
| `desired_order` | `List[str]` | ✅ Yes | List of column names in new order |

#### Returns

`str` - Success/failure message

#### Example

```python
# Original columns: ["Name", "Age", "Email", "Phone"]
# Reorder to: ["Name", "Phone", "Email", "Age"]

await computer.run_actions([
    MCPToolCall(
        tool_key="action::reorder_columns",
        tool_name="reorder_columns",
        parameters={
            "sheet_name": "Contacts",
            "desired_order": ["Name", "Phone", "Email", "Age"]
        }
    )
])
```

---

### get_range_values

Get values from a specified cell range.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sheet_name` | `str` | ✅ Yes | Sheet name |
| `start_row` | `int` | ✅ Yes | Start row |
| `start_col` | `int` | ✅ Yes | Start column |
| `end_row` | `int` | ✅ Yes | End row |
| `end_col` | `int` | ✅ Yes | End column |

#### Returns

`List[List[Any]]` - 2D list of cell values

#### Example

```python
# Get A1:C3
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::get_range_values",
        tool_name="get_range_values",
        parameters={
            "sheet_name": "Sheet1",
            "start_row": 1,
            "start_col": 1,
            "end_row": 3,
            "end_col": 3
        }
    )
])

# Output: [["A1", "B1", "C1"], ["A2", "B2", "C2"], ["A3", "B3", "C3"]]
```

## Configuration

```yaml
AppAgent:
  EXCEL.EXE:
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: ExcelCOMExecutor
        type: local
        reset: true  # Recommended: prevent data leakage between workbooks
```

## Best Practices

### 1. Use Column Numbers for select_table_range

```python
# Column mapping: A=1, B=2, C=3, D=4, ...
# Select A1:D10
await computer.run_actions([
    MCPToolCall(
        tool_key="action::select_table_range",
        parameters={
            "sheet_name": "Sheet1",
            "start_row": 1,
            "start_col": 1,   # A
            "end_row": 10,
            "end_col": 4      # D
        }
    )
])
```

### 2. Insert Data Efficiently

```python
# ✅ Good: Insert entire table at once
data = [["Header1", "Header2"], ["Val1", "Val2"]]
await computer.run_actions([
    MCPToolCall(tool_key="action::insert_excel_table", parameters={
        "table": data, "sheet_name": "Sheet1", "start_row": 1, "start_col": 1
    })
])

# ❌ Bad: Insert cell by cell
for row in data:
    for col in row:
        # Multiple calls...
```

### 3. Save Frequently

```python
# After data insertion/manipulation
await computer.run_actions([
    MCPToolCall(tool_key="action::save_as", parameters={"file_ext": ".xlsx"})
])
```

## Use Cases

### Data Processing Workflow

```python
# 1. Get data
data = await computer.run_actions([
    MCPToolCall(tool_key="action::get_range_values", parameters={
        "sheet_name": "Raw Data", "start_row": 1, "start_col": 1,
        "end_row": -1, "end_col": -1
    })
])

# 2. Process data (Python)
processed = process_data(data[0].data)

# 3. Insert into new sheet
await computer.run_actions([
    MCPToolCall(tool_key="action::insert_excel_table", parameters={
        "table": processed, "sheet_name": "Processed", "start_row": 1, "start_col": 1
    })
])

# 4. Export as CSV
await computer.run_actions([
    MCPToolCall(tool_key="action::save_as", parameters={"file_ext": ".csv"})
])
```

## Related Documentation

- [WordCOMExecutor](./word_com_executor.md) - Word COM automation
- [PowerPointCOMExecutor](./ppt_com_executor.md) - PowerPoint COM automation
