# Visual Control Detection (OmniParser)

Visual control detection uses [OmniParser-v2](https://github.com/microsoft/OmniParser), a vision-based grounding model that detects UI elements through computer vision. This method is particularly effective for custom controls, icons, images, and visual elements that may not be accessible through standard UIA.

## Use Cases

- **Custom Controls**: Detects proprietary or non-standard UI elements
- **Visual Elements**: Icons, images, and graphics-based controls
- **Web Content**: Elements within browser windows or web views
- **Canvas-based UIs**: Applications that render custom graphics

## Deployment

### 1. Clone the OmniParser Repository

On your remote GPU server:

```bash
git clone https://github.com/microsoft/OmniParser.git
cd OmniParser/omnitool/omniparserserver
```

### 2. Start the OmniParser Service

```bash
python gradio_demo.py
```

This will generate output similar to:

```
* Running on local URL:  http://0.0.0.0:7861
* Running on public URL: https://xxxxxxxxxxxxxxxxxx.gradio.live
```

For detailed deployment instructions, refer to the [OmniParser README](https://github.com/microsoft/OmniParser/tree/master/omnitool).

## Configuration

### OmniParser Settings

Configure the OmniParser endpoint and parameters in `config/ufo/system.yaml`:

```yaml
OMNIPARSER:
  ENDPOINT: "<YOUR_END_POINT>"  # The endpoint URL from deployment
  BOX_THRESHOLD: 0.05            # Bounding box confidence threshold
  IOU_THRESHOLD: 0.1             # IoU threshold for non-max suppression
  USE_PADDLEOCR: True            # Enable OCR for text detection
  IMGSZ: 640                     # Input image size for the model
```

### Enable Visual Detection

Set `CONTROL_BACKEND` to use OmniParser:

```yaml
# Use OmniParser only
CONTROL_BACKEND: ["omniparser"]

# Or use hybrid mode (recommended for maximum coverage)
CONTROL_BACKEND: ["uia", "omniparser"]
```

See [Hybrid Detection](./hybrid_detection.md) for combining UIA and OmniParser, or [System Configuration](../../../configuration/system/system_config.md#control-backend) for detailed options.

## Reference

:::automator.ui_control.grounding.omniparser.OmniparserGrounding