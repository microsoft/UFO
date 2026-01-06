# WindowsAppEnv

The usage scenarios for the `WindowsAppEnv` class are as follows:

* **Opening a specified document.**
* **Matching document windows** using different strategies (`contains`, `fuzzy`, and `regex`).
* **Matching the controls** required for each step in the instantiated plan using various strategies (`contains`, `fuzzy`, and `regex`).
* **Closing a specified document.**

The following sections provide a detailed explanation of the **matching strategies for windows and controls**, as well as their usage methods.

## Matching Strategies

In the `WindowsAppEnv` class, matching strategies are rules that determine how to match `window` or `control` names with a given document name or target text. Based on the configuration file, three different matching strategies can be selected: `contains`, `fuzzy`, and `regex`.

* `Contains` matching is the simplest strategy, suitable when the window and document names match exactly.
* `Fuzzy` matching is more flexible and can match even when there are spelling errors or partial matches between the window title and document name.
* `Regex` matching offers the most flexibility, ideal for complex matching patterns in window titles.

### 1. **Window Matching** Example

The method `find_matching_window` is responsible for matching windows based on the configured matching strategy. Here's how you can use it to find a window by providing a document name:

#### Example:

```python
# Initialize your application object (assuming app_object is already defined)
app_env = WindowsAppEnv(app_object)

# Define the document name you're looking for
doc_name = "example_document_name"

# Call find_matching_window to find the window that matches the document name
matching_window = app_env.find_matching_window(doc_name)

if matching_window:
    print(f"Found matching window: {matching_window.element_info.name}")
else:
    print("No matching window found.")
```

#### Explanation:

- `app_env.find_matching_window(doc_name)` will search through all open windows and match the window title using the strategy defined in the configuration (contains, fuzzy, or regex).
- If a match is found, the `matching_window` object will contain the matched window, and you can print the window's name.
- If no match is found, it will return `None`.

### 2. **Control Matching** Example

To find a matching control within a window, you can use the `find_matching_controller` method. This method requires a dictionary of filtered controls and a control text to match against.

#### Example:

```python
# Initialize your application object (assuming app_object is already defined)
app_env = WindowsAppEnv(app_object)

# Define a filtered annotation dictionary of controls (control_key, control_object)
# Here, we assume you have a dictionary of UIAWrapper controls from a window.
filtered_annotation_dict = {
    1: some_control_1,  # Example control objects
    2: some_control_2,  # Example control objects
}

# Define the control text you're searching for
control_text = "submit_button"

# Call find_matching_controller to find the best match
controller_key, control_selected = app_env.find_matching_controller(filtered_annotation_dict, control_text)

if control_selected:
    print(f"Found matching control with key {controller_key}: {control_selected.window_text()}")
else:
    print("No matching control found.")
```

#### Explanation:

- `filtered_annotation_dict` is a dictionary where the key represents the control's ID and the value is the control object (`UIAWrapper`).
- `control_text` is the text you're searching for within those controls.
- `app_env.find_matching_controller(filtered_annotation_dict, control_text)` will calculate the matching score for each control based on the defined strategy and return the control with the highest match score.
- If a match is found, it will return the control object (`control_selected`) and its key (`controller_key`), which can be used for further interaction.

# Reference

::: env.env_manager.WindowsAppEnv
