# Hybrid Control Detection

Hybrid control detection combines both UIA and OmniParser to provide comprehensive UI coverage. It merges standard Windows controls detected via UIA with visual elements detected through OmniParser, removing duplicates based on Intersection over Union (IoU) overlap.

![Hybrid Control Detection](../../../img/controls.png)

## How It Works

The hybrid detection process follows these steps:

```mermaid
graph LR
    A[Screenshot] --> B[UIA Detection]
    A --> C[OmniParser Detection]
    B --> D[UIA Controls<br/>Standard UI Elements]
    C --> E[Visual Controls<br/>Icons, Images, Custom UI]
    D --> F[Merge & Deduplicate<br/>IoU Threshold: 0.1]
    E --> F
    F --> G[Final Control List<br/>Annotated [1] to [N]]
    
    style D fill:#e3f2fd
    style E fill:#fff3e0
    style F fill:#e8f5e9
    style G fill:#f3e5f5
```

**Deduplication Algorithm:**

1. Keep all UIA-detected controls (main list)
2. For each OmniParser-detected control (additional list):
   - Calculate IoU with all UIA controls
   - If IoU > threshold (default 0.1), discard as duplicate
   - Otherwise, add to merged list
3. Result: Maximum coverage with minimal duplicates

## Benefits

- **Maximum Coverage**: Detects both standard and custom UI elements
- **No Gaps**: Visual detection fills in UIA blind spots
- **Efficiency**: Deduplication prevents redundant annotations
- **Flexibility**: Works across diverse application types

## Configuration

### Prerequisites

Before enabling hybrid detection, you must deploy and configure OmniParser. See [Visual Detection - Deployment](./visual_detection.md#deployment) for instructions.

### Enable Hybrid Mode

Configure both backends in `config/ufo/system.yaml`:

```yaml
# Enable hybrid detection
CONTROL_BACKEND: ["uia", "omniparser"]

# IoU threshold for merging (controls with IoU > threshold are considered duplicates)
IOU_THRESHOLD_FOR_MERGE: 0.1  # Default: 0.1

# OmniParser configuration
OMNIPARSER:
  ENDPOINT: "<YOUR_END_POINT>"
  BOX_THRESHOLD: 0.05
  IOU_THRESHOLD: 0.1
  USE_PADDLEOCR: True
  IMGSZ: 640
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `CONTROL_BACKEND` | List[str] | `["uia"]` | List of detection backends to use |
| `IOU_THRESHOLD_FOR_MERGE` | float | `0.1` | IoU threshold for duplicate detection (0.0-1.0) |

**Tuning Guidelines:**

- **Lower threshold (< 0.1)**: More aggressive deduplication, may miss some controls
- **Higher threshold (> 0.1)**: Keep more overlapping controls, may have duplicates
- **Recommended**: Keep default 0.1 for optimal balance

See [System Configuration](../../../configuration/system/system_config.md#control-backend) for complete configuration details.

## Implementation

The hybrid detection is implemented through:

- **`AppControlInfoStrategy`**: Orchestrates control collection from multiple backends
- **`PhotographerFacade.merge_target_info_list()`**: Performs IoU-based deduplication
- **`OmniparserGrounding`**: Handles visual detection and parsing

## Reference

:::automator.ui_control.grounding.omniparser.OmniparserGrounding