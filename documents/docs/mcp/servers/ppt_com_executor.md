# PowerPointCOMExecutor Server

## Overview

**PowerPointCOMExecutor** provides Microsoft PowerPoint automation via COM API for efficient presentation manipulation.

**Server Type:** Action  
**Deployment:** Local (in-process)  
**Agent:** AppAgent  
**Target Application:** Microsoft PowerPoint (`POWERPNT.EXE`)  
**LLM-Selectable:** ✅ Yes

## Server Information

| Property | Value |
|----------|-------|
| **Namespace** | `PowerPointCOMExecutor` |
| **Platform** | Windows |
| **Requires** | Microsoft PowerPoint (COM interface) |
| **Tool Type** | `action` |

## Tools

### set_background_color

Set the background color for one or more slides in the presentation.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `color` | `str` | ✅ Yes | - | Hex color code (RGB format, e.g., `"FFFFFF"`) |
| `slide_index` | `List[int]` | No | `None` | List of slide indices (1-based). `None` = all slides |

#### Returns

`str` - Success/failure message

#### Example

```python
# Set white background for slide 1
await computer.run_actions([
    MCPToolCall(
        tool_key="action::set_background_color",
        tool_name="set_background_color",
        parameters={
            "color": "FFFFFF",
            "slide_index": [1]
        }
    )
])

# Set blue background for slides 1, 3, 5
await computer.run_actions([
    MCPToolCall(
        tool_key="action::set_background_color",
        tool_name="set_background_color",
        parameters={
            "color": "0000FF",
            "slide_index": [1, 3, 5]
        }
    )
])

# Set red background for ALL slides
await computer.run_actions([
    MCPToolCall(
        tool_key="action::set_background_color",
        tool_name="set_background_color",
        parameters={
            "color": "FF0000",
            "slide_index": None  # All slides
        }
    )
])
```

#### Color Format

Use 6-character hex RGB codes (without `#`):

| Color | Hex Code |
|-------|----------|
| White | `FFFFFF` |
| Black | `000000` |
| Red | `FF0000` |
| Green | `00FF00` |
| Blue | `0000FF` |
| Yellow | `FFFF00` |
| Gray | `808080` |

---

### save_as

Save or export PowerPoint presentation to specified format.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_dir` | `str` | No | `""` | Directory path |
| `file_name` | `str` | No | `""` | Filename without extension |
| `file_ext` | `str` | No | `""` | Extension (default: `.pptx`) |
| `current_slide_only` | `bool` | No | `False` | For image formats: save only current slide or all slides |

#### Supported Extensions

**Presentation Formats**:
- `.pptx` - PowerPoint presentation (default)
- `.ppt` - PowerPoint 97-2003
- `.pdf` - PDF format

**Image Formats** (controlled by `current_slide_only`):
- `.jpg`, `.jpeg` - JPEG image
- `.png` - PNG image
- `.gif` - GIF image
- `.bmp` - Bitmap image
- `.tiff` - TIFF image

#### Returns

`str` - Success/failure message

#### Example

```python
# Save as PPTX
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        tool_name="save_as",
        parameters={
            "file_dir": "C:\\Presentations",
            "file_name": "Q4_Report",
            "file_ext": ".pptx"
        }
    )
])

# Export as PDF
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        tool_name="save_as",
        parameters={
            "file_ext": ".pdf"
        }
    )
])

# Save current slide as PNG
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        tool_name="save_as",
        parameters={
            "file_name": "slide_1",
            "file_ext": ".png",
            "current_slide_only": True
        }
    )
])

# Export all slides as PNG images (creates directory)
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        tool_name="save_as",
        parameters={
            "file_dir": "C:\\Exports\\Slides",
            "file_ext": ".png",
            "current_slide_only": False  # Saves all slides
        }
    )
])
```

#### Image Export Behavior

| `current_slide_only` | Behavior |
|----------------------|----------|
| `True` | Single image file of current slide |
| `False` | Directory containing multiple image files (one per slide) |

## Configuration

```yaml
AppAgent:
  POWERPNT.EXE:
    action:
      - namespace: AppUIExecutor
        type: local
      - namespace: PowerPointCOMExecutor
        type: local
        reset: true  # Recommended
```

## Best Practices

### 1. Bulk Background Setting

```python
# ✅ Good: Set multiple slides at once
await computer.run_actions([
    MCPToolCall(
        tool_key="action::set_background_color",
        parameters={"color": "FFFFFF", "slide_index": [1, 2, 3, 4, 5]}
    )
])

# ❌ Bad: One call per slide
for i in range(1, 6):
    await computer.run_actions([
        MCPToolCall(
            tool_key="action::set_background_color",
            parameters={"color": "FFFFFF", "slide_index": [i]}
        )
    ])
```

### 2. Use save_as for Exports

```python
# ✅ Good: Fast one-command export
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        parameters={"file_ext": ".pdf"}
    )
])

# ❌ Bad: Manual UI navigation
await computer.run_actions([
    MCPToolCall(tool_key="action::keyboard_input", parameters={"keys": "{VK_MENU}f"})  # Alt+F
])
# ... navigate File menu ...
```

### 3. Verify Hex Colors

```python
def validate_hex_color(color: str) -> bool:
    """Validate hex color format"""
    return bool(re.match(r'^[0-9A-Fa-f]{6}$', color))

color = "FFFFFF"
if validate_hex_color(color):
    await computer.run_actions([
        MCPToolCall(
            tool_key="action::set_background_color",
            parameters={"color": color, "slide_index": [1]}
        )
    ])
```

## Use Cases

### Presentation Branding

```python
# Apply company color scheme
brand_color = "003366"  # Company blue

# Set all slides to brand background
await computer.run_actions([
    MCPToolCall(
        tool_key="action::set_background_color",
        tool_name="set_background_color",
        parameters={
            "color": brand_color,
            "slide_index": None  # All slides
        }
    )
])

# Save as PDF for distribution
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        tool_name="save_as",
        parameters={
            "file_dir": "C:\\Distribution",
            "file_name": "Company_Presentation",
            "file_ext": ".pdf"
        }
    )
])
```

### Slide Export for Documentation

```python
# Export each slide as PNG for documentation
await computer.run_actions([
    MCPToolCall(
        tool_key="action::save_as",
        tool_name="save_as",
        parameters={
            "file_dir": "C:\\Docs\\Images",
            "file_name": "presentation_slides",
            "file_ext": ".png",
            "current_slide_only": False  # Export all
        }
    )
])
```

## Limitations

- **Limited tool set**: Only 2 tools (background color and save)
- **No content creation**: Cannot add text, shapes, or images via COM (use UI automation)
- **No slide management**: Cannot add/delete/reorder slides (use UI automation)

**Tip:** Combine with **AppUIExecutor** for full PowerPoint automation:
- **PowerPointCOMExecutor**: Background colors, export
- **AppUIExecutor**: Add slides, insert text, shapes, animations

## Related Documentation

- [WordCOMExecutor](./word_com_executor.md) - Word COM automation
- [ExcelCOMExecutor](./excel_com_executor.md) - Excel COM automation
- [AppUIExecutor](./app_ui_executor.md) - UI-based PowerPoint automation
