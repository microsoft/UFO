# Visual Control Detection (OmniParser)

We also support visual control detection using OmniParser-v2. This method is useful for detecting custom controls in the application that may not be recognized by standard UIA methods. The visual control detection uses computer vision techniques to identify and interact with the UI elements based on their visual appearance.


## Deployment

## Configuration

After deploying the OmniParser model, you need to configure the OmniParser settings in the `config.yaml` file:

```yaml
OMNIPARSER: {
  ENDPOINT: "<YOUR_END_POINT>", # The endpoint for the omniparser deployment
  BOX_THRESHOLD: 0.05, # The box confidence threshold for the omniparser, default is 0.05
  IOU_THRESHOLD: 0.1, # The iou threshold for the omniparser, default is 0.1
  USE_PADDLEOCR: True, # Whether to use the paddleocr for the omniparser
  IMGSZ: 640 # The image size for the omniparser
}
```

To activate the icon control filtering, you need to set `CONTROL_BACKEND` to `["omniparser"]` in the `config_dev.yaml` file.

```yaml
CONTROL_BACKEND: ["omniparser"]
```


# Reference
The following classes are used for visual control detection in OmniParser:


:::automator.ui_control.grounding.omniparser.OmniparserGrounding