# UIA Control Detection

UIA control detection is a method to detect standard controls in the application using the UI Automation (UIA) framework. It provides a set of APIs to access and manipulate the UI elements in Windows applications. 

!!! note
    The UIA control detection may fail to detect non-standard controls or custom controls in the application.

## Configuration

To activate the icon control filtering, you need to set `CONTROL_BACKEND` to `["uia"]` in the `config_dev.yaml` file.

```yaml
CONTROL_BACKEND: ["uia"]
```


# Reference

:::automator.ui_control.inspector.ControlInspectorFacade