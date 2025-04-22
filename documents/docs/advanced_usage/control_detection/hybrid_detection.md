# Hybrid Detection

We also support hybrid control detection using both UIA and OmniParser-v2. This method is useful for detecting standard controls in the application using the UI Automation (UIA) framework, and for detecting custom controls in the application that may not be recognized by standard UIA methods. The visually detected controls are merged with the UIA controls by removing the duplicate controls based on IOU. We illustrate the hybrid control detection in the figure below:

<h1 align="center">
    <img src="../../../img/controls.png" alt="Hybrid Control Detection" />
</h1>


## Configuration


Before using the hybrid control detection, you need to deploy and configure the OmniParser model. You can refer to the [OmniParser deployment](./visual_detection.md) for more details.

To activate the icon control filtering, you need to set `CONTROL_BACKEND` to `["uia", "omniparser"]` in the `config_dev.yaml` file.

```yaml
CONTROL_BACKEND: ["uia", "omniparser"]
```


# Reference
The following classes are used for visual control detection in OmniParser:


:::automator.ui_control.grounding.omniparser.OmniparserGrounding