# Icon Filter

The icon control filter is a method to filter the controls based on the similarity between the control icon image and the agent's plan using the image/text embeddings.

## Configuration

To activate the icon control filtering, you need to add `ICON` to the `CONTROL_FILTER` list in the `config_dev.yaml` file. Below is the detailed icon control filter configuration in the `config_dev.yaml` file:

- `CONTROL_FILTER`: A list of filtering methods that you want to apply to the controls. To activate the icon control filtering, add `ICON` to the list.
- `CONTROL_FILTER_TOP_K_ICON`: The number of controls to keep after filtering.
- `CONTROL_FILTER_MODEL_ICON_NAME`: The control filter model name for icon similarity. By default, it is set to "clip-ViT-B-32".


# Reference

:::automator.ui_control.control_filter.IconControlFilter