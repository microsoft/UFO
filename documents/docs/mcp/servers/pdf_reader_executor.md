# PDFReaderExecutor Server

## Overview

**PDFReaderExecutor** provides PDF text extraction with optional human simulation capabilities.

**Server Type:** Action  
**Deployment:** Local (in-process)  
**Agent:** AppAgent, HostAgent  
**LLM-Selectable:** ✅ Yes

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `PDFReaderExecutor` |
| **Server Name** | `UFO PDF Reader MCP Server` |
| **Platform** | Cross-platform (Windows, Linux, macOS) |
| **Dependencies** | PyPDF2 |
| **Tool Type** | `action` |

## Tools

### extract_pdf_text

Extract text content from a single PDF file with optional human simulation.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pdf_path` | `str` | ✅ Yes | - | Full path to PDF file |
| `simulate_human` | `bool` | No | `True` | Simulate human-like document review |

#### Returns

`str` - Extracted text content with page markers

#### Human Simulation Behavior

When `simulate_human=True`:
1. Opens PDF with default application
2. Waits 2-5 seconds (random) to simulate reading
3. Extracts text with page-by-page delays (0.5-1.5 seconds)
4. Closes PDF file

When `simulate_human=False`:
- Direct text extraction (no delays)
- No application launching

#### Example

```python
# With human simulation (default)
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::extract_pdf_text",
        tool_name="extract_pdf_text",
        parameters={
            "pdf_path": "C:\\Documents\\report.pdf",
            "simulate_human": True
        }
    )
])

# Fast extraction (no simulation)
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::extract_pdf_text",
        tool_name="extract_pdf_text",
        parameters={
            "pdf_path": "C:\\Documents\\report.pdf",
            "simulate_human": False
        }
    )
])
```

#### Output Format

```
--- Page 1 ---
This is the content of page 1.

--- Page 2 ---
This is the content of page 2.

--- Page 3 ---
This is the content of page 3.
```

#### Error Handling

Returns error message string if:
- File not found: `"Error: PDF file not found at {path}"`
- Not a PDF: `"Error: File {path} is not a PDF file"`
- Read error: `"Error reading PDF {path}: {details}"`

---

### list_pdfs_in_directory

List all PDF files in a specified directory.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `directory_path` | `str` | ✅ Yes | Directory path to scan |

#### Returns

`List[str]` - List of PDF file paths (sorted)

#### Example

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::list_pdfs_in_directory",
        tool_name="list_pdfs_in_directory",
        parameters={"directory_path": "C:\\Documents\\Reports"}
    )
])

# Output: [
#     "C:\\Documents\\Reports\\Q1_Report.pdf",
#     "C:\\Documents\\Reports\\Q2_Report.pdf",
#     "C:\\Documents\\Reports\\Q3_Report.pdf"
# ]
```

#### Error Handling

Returns empty list `[]` if:
- Directory doesn't exist
- Path is not a directory
- No PDF files found

---

### extract_all_pdfs_text

Extract text from all PDF files in a directory with human simulation.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directory_path` | `str` | ✅ Yes | - | Directory containing PDFs |
| `simulate_human` | `bool` | No | `True` | Simulate human review for each PDF |

#### Returns

`Dict[str, str]` - Dictionary mapping filenames to extracted text

#### Human Simulation Behavior

When `simulate_human=True`:
- Brief pause between files (1-3 seconds random)
- Each PDF processed with human simulation
- Progress messages logged

#### Example

```python
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::extract_all_pdfs_text",
        tool_name="extract_all_pdfs_text",
        parameters={
            "directory_path": "C:\\Documents\\Reports",
            "simulate_human": True
        }
    )
])

# Output: {
#     "Q1_Report.pdf": "--- Page 1 ---\nQ1 Sales Report\n...",
#     "Q2_Report.pdf": "--- Page 1 ---\nQ2 Sales Report\n...",
#     "Q3_Report.pdf": "--- Page 1 ---\nQ3 Sales Report\n..."
# }
```

#### Error Handling

Returns dictionary with error key if:
- Directory not found: `{"error": "Directory not found: {path}"}`
- Not a directory: `{"error": "Path is not a directory: {path}"}`
- No PDFs found: `{"message": "No PDF files found in directory: {path}"}`

## Configuration

```yaml
AppAgent:
  default:
    action:
      - namespace: PDFReaderExecutor
        type: local

HostAgent:
  default:
    action:
      - namespace: PDFReaderExecutor
        type: local
```

## Best Practices

### 1. Disable Simulation for Batch Processing

```python
# ✅ Good: Fast batch processing
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::extract_all_pdfs_text",
        tool_name="extract_all_pdfs_text",
        parameters={
            "directory_path": "C:\\Documents",
            "simulate_human": False  # Faster
        }
    )
])

# ❌ Bad: Slow with simulation
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::extract_all_pdfs_text",
        tool_name="extract_all_pdfs_text",
        parameters={
            "directory_path": "C:\\Documents",
            "simulate_human": True  # 2-5 seconds per file
        }
    )
])
```

### 2. Verify Files Exist

```python
# List PDFs first
pdf_list = await computer.run_actions([
    MCPToolCall(
        tool_key="action::list_pdfs_in_directory",
        parameters={"directory_path": "C:\\Documents"}
    )
])

if pdf_list[0].data:
    # Extract from first PDF
    text = await computer.run_actions([
        MCPToolCall(
            tool_key="action::extract_pdf_text",
            parameters={
                "pdf_path": pdf_list[0].data[0],
                "simulate_human": False
            }
        )
    ])
else:
    logger.warning("No PDF files found")
```

### 3. Handle Large Documents

```python
# Extract text
result = await computer.run_actions([
    MCPToolCall(
        tool_key="action::extract_pdf_text",
        parameters={"pdf_path": "large_document.pdf", "simulate_human": False}
    )
])

text = result[0].data

# Process in chunks if needed
if len(text) > 100000:  # Large document
    chunks = [text[i:i+50000] for i in range(0, len(text), 50000)]
    for chunk in chunks:
        process_chunk(chunk)
```

## Use Cases

### Document Analysis Pipeline

```python
# 1. List all PDFs
pdfs = await computer.run_actions([
    MCPToolCall(
        tool_key="action::list_pdfs_in_directory",
        parameters={"directory_path": "C:\\Contracts"}
    )
])

# 2. Extract text from each
for pdf_path in pdfs[0].data:
    text = await computer.run_actions([
        MCPToolCall(
            tool_key="action::extract_pdf_text",
            parameters={"pdf_path": pdf_path, "simulate_human": False}
        )
    ])
    
    # 3. Analyze text
    analyze_contract(text[0].data)
```

### Batch Report Processing

```python
# Extract all reports at once
reports = await computer.run_actions([
    MCPToolCall(
        tool_key="action::extract_all_pdfs_text",
        tool_name="extract_all_pdfs_text",
        parameters={
            "directory_path": "C:\\Reports\\2024",
            "simulate_human": False
        }
    )
])

# Process all reports
for filename, content in reports[0].data.items():
    logger.info(f"Processing {filename}")
    # Extract data from content
    data = extract_report_data(content)
```

## Limitations

- **Text-only**: Cannot extract images or formatting
- **OCR not supported**: Scanned PDFs with no text layer will return empty
- **Table parsing**: Complex tables may not preserve structure
- **No modification**: Read-only operations (cannot edit PDFs)

## Performance

| Operation | simulate_human=True | simulate_human=False |
|-----------|---------------------|----------------------|
| Single PDF (10 pages) | ~10-20 seconds | ~1 second |
| Batch 10 PDFs | ~2-3 minutes | ~10 seconds |
| Large PDF (100 pages) | ~2-5 minutes | ~5-10 seconds |

## Related Documentation

- [Action Servers](../action.md) - Action server concepts
- [Local Servers](../local_servers.md) - Local deployment
