# Control Filtering

There may be many controls items in the application, which may not be relevant to the task. UFO can filter out the irrelevant controls and only focus on the relevant ones. This filtering process can reduce the complexity of the task.

Execept for configuring the control types for selection on `CONTROL_LIST` in `config_dev.yaml`, UFO also supports filtering the controls based on semantic similarity or fuzzy matching. We currerntly support the following filtering methods:

| Filtering Method | Description |
|------------------|-------------|
| [`Text`](./text_filtering.md)     | Filter the controls based on the control text. |
| [`Semantic`](./semantic_filtering.md) | Filter the controls based on the semantic similarity. |
| [`Icon`](./icon_filtering.md)    | Filter the controls based on the control icon image. |


# Reference
The implementation of the control filtering is base on the `BasicControlFilter` class located in the `ufo/automator/ui_control/control_filter.py` file. Concrete filtering class inherit from the `BasicControlFilter` class and implement the `control_filter` method to filter the controls based on the specific filtering method.

:::automator.ui_control.control_filter.BasicControlFilter
