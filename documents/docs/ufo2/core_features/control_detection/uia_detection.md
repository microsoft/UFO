# UIA Control Detection

UIA control detection uses the Windows UI Automation (UIA) framework to detect and interact with standard controls in Windows applications. It provides a robust set of APIs to access and manipulate UI elements programmatically.

## Features

- **Fast and Reliable**: Native Windows API with optimal performance
- **Standard Controls**: Works with most Windows applications using standard controls
- **Rich Metadata**: Provides detailed control information (type, name, position, state, etc.)

## Limitations

UIA control detection may not detect non-standard controls, custom-rendered UI elements, or visual components that don't expose UIA interfaces (e.g., canvas-based controls, game UIs, some web content).

## Configuration

UIA is the default control detection backend. Configure it in `config/ufo/system.yaml`:

```yaml
CONTROL_BACKEND: ["uia"]
```

For applications with custom controls, consider using [hybrid detection](./hybrid_detection.md) which combines UIA with visual detection.

## Implementation

UFO² uses the `ControlInspectorFacade` class to interact with the UIA framework. The facade pattern provides a simplified interface to:

- Enumerate desktop windows
- Find control elements in window hierarchies
- Filter controls by type, visibility, and state
- Extract control metadata and positions

See [System Configuration](../../../configuration/system/system_config.md#control-backend) for additional options.

## Reference

:::automator.ui_control.inspector.ControlInspectorFacade