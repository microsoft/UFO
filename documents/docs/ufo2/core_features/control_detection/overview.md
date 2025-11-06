# Control Detection


We support different control detection methods to detect the controls in the application to accommodate both standard (UIA) and custom controls (Visual). The control detection methods include:

| Mechanism | Description |
|-----------|-------------|
| [**UIA**](./uia_detection.md)  | The UI Automation (UIA) framework is used to detect standard controls in the application. It provides a set of APIs to access and manipulate the UI elements in Windows applications. |
| [**Visual**](./visual_detection.md) | The visual control detection method uses OmniParser visual detection to detect custom controls in the application. It uses computer vision techniques to identify and interact with the UI elements based on their visual appearance. |
| [**Hybrid**](./hybrid_detection.md) | The hybrid control detection method combines both UIA and visual detection methods to detect the controls in the application. It first tries to use the UIA method, and if it fails, it falls back to the visual method. |



## Configuration
To configure the control detection method, you can set the `CONTROL_BACKEND` parameter in the `config_dev.yaml` file. The available options are `uia`, and `onmiparser`. If you want to use the hybrid method, you can set it to `["uia", "onmiparser"]`.

```yaml
CONTROL_BACKEND: ["uia"]
```

