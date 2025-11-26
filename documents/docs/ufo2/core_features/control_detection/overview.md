# Control Detection

We support different control detection methods to detect controls in the application to accommodate both standard (UIA) and custom controls (Visual).

## Detection Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| [**UIA**](./uia_detection.md) | Uses Windows UI Automation framework to detect standard controls. Provides APIs to access and manipulate UI elements in Windows applications. | Standard Windows applications with native controls |
| [**Visual (OmniParser)**](./visual_detection.md) | Uses OmniParser vision-based detection to identify custom controls through computer vision techniques based on visual appearance. | Applications with custom controls, icons, or visual elements not accessible via UIA |
| [**Hybrid**](./hybrid_detection.md) | Combines both UIA and OmniParser detection methods. Merges results from both approaches, removing duplicates based on IoU overlap. | Maximum coverage for applications with both standard and custom controls |

## Configuration

Configure the control detection method by setting the `CONTROL_BACKEND` parameter in `config/ufo/system.yaml`:

```yaml
# Use UIA only (default, recommended)
CONTROL_BACKEND: ["uia"]

# Use OmniParser only
CONTROL_BACKEND: ["omniparser"]

# Use hybrid mode (UIA + OmniParser)
CONTROL_BACKEND: ["uia", "omniparser"]
```

See [System Configuration](../../../configuration/system/system_config.md#control-backend) for detailed configuration options.

