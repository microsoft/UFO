# Sematic Control Filter

The semantic control filter is a method to filter the controls based on the semantic similarity between the agent's plan and the control's text using their embeddings. 

## Configuration

To activate the semantic control filtering, you need to add `SEMANTIC` to the `CONTROL_FILTER` list in the `config_dev.yaml` file. Below is the detailed sematic control filter configuration in the `config_dev.yaml` file:

- `CONTROL_FILTER`: A list of filtering methods that you want to apply to the controls. To activate the semantic control filtering, add `SEMANTIC` to the list.
- `CONTROL_FILTER_TOP_K_SEMANTIC`: The number of controls to keep after filtering.
- `CONTROL_FILTER_MODEL_SEMANTIC_NAME`: The control filter model name for semantic similarity. By default, it is set to "all-MiniLM-L6-v2".

# Reference

:::automator.ui_control.control_filter.SemanticControlFilter