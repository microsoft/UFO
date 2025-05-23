# API Prompts

The API prompts provide the description and usage of the APIs used in UFO. Shared APIs and app-specific APIs are stored in different directories:

| Directory | Description |
| --- | --- |
| `ufo/prompts/share/base/api.yaml` | Shared APIs used by multiple applications |
| `ufo/prompts/{app_name}` | APIs specific to an application |

!!! info
    You can configure the API prompt used in the `config.yaml` file. You can find more information about the configuration file [here](../configurations/developer_configuration.md).
!!! tip
    You may customize the API prompt for a specific application by adding the API prompt in the application's directory.


## Example API Prompt

Below is an example of an API prompt:

```yaml
click_input:
  summary: |-
    "click_input" is to click the control item with mouse.
  class_name: |-
    ClickInputCommand
  usage: |-
    [1] API call: click_input(button: str, double: bool)
    [2] Args:
      - button: 'The mouse button to click. One of ''left'', ''right'', ''middle'' or ''x'' (Default: ''left'')'
      - double: 'Whether to perform a double click or not (Default: False)'
    [3] Example: click_input(button="left", double=False)
    [4] Available control item: All control items.
    [5] Return: None
```

To create a new API prompt, follow the template above and add it to the appropriate directory.