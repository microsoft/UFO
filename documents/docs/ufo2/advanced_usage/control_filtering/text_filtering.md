# Text Control Filter

The text control filter is a method to filter the controls based on the control text. The agent's plan on the current step usually contains some keywords or phrases. This method filters the controls based on the matching between the control text and the keywords or phrases in the agent's plan.

## Configuration

To activate the text control filtering, you need to add `TEXT` to the `CONTROL_FILTER` list in the `config_dev.yaml` file. Below is the detailed text control filter configuration in the `config_dev.yaml` file:

- `CONTROL_FILTER`: A list of filtering methods that you want to apply to the controls. To activate the text control filtering, add `TEXT` to the list.
- `CONTROL_FILTER_TOP_K_PLAN`: The number of agent's plan keywords or phrases to use for filtering the controls.



# Reference

:::automator.ui_control.control_filter.TextControlFilter