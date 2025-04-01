# Developer Configuration

This section provides detailed information on how to configure the UFO agent for developers. The configuration file `config_dev.yaml` is located in the `ufo/config` directory and contains various settings and switches to customize the UFO agent for development purposes.

## System Configuration

The following parameters are included in the system configuration of the UFO agent:

| Configuration Option    | Description                                                                                             | Type     | Default Value |
|-------------------------|---------------------------------------------------------------------------------------------------------|----------|---------------|
| `CONTROL_BACKEND`       | The list of backend for control action, currently supporting `uia` and `win32` and `onmiparser`         | List     | ["uia"]       |
| `ACTION_SEQUENCE`       | Whether to use output multiple actions in a single step.                                                | Boolean  | False         |
| `MAX_STEP`              | The maximum step limit for completing the user request in a session.                                    | Integer  | 100           |
| `MAX_ROUND`             | The maximum round limit for completing the user request in a session.                                   | Integer  | 10            |
| `SLEEP_TIME`            | The sleep time in seconds between each step to wait for the window to be ready.                         | Integer  | 5             |
| `RECTANGLE_TIME`        | The time in seconds for the rectangle display around the selected control.                              | Integer  | 1             |
| `SAFE_GUARD`            | Whether to use the safe guard to ask for user confirmation before performing sensitive operations.      | Boolean  | True          |
| `CONTROL_LIST`          | The list of widgets allowed to be selected.                                                             | List     | ["Button", "Edit", "TabItem", "Document", "ListItem", "MenuItem", "ScrollBar", "TreeItem", "Hyperlink", "ComboBox", "RadioButton", "DataItem"] |
| `HISTORY_KEYS`          | The keys of the step history added to the [`Blackboard`](../agents/design/blackboard.md) for agent decision-making.                         | List     | ["Step", "Thought", "ControlText", "Subtask", "Action", "Comment", "Results", "UserConfirm"] |
| `ANNOTATION_COLORS`     | The colors assigned to different control types for annotation.                                          | Dictionary | {"Button": "#FFF68F", "Edit": "#A5F0B5", "TabItem": "#A5E7F0", "Document": "#FFD18A", "ListItem": "#D9C3FE", "MenuItem": "#E7FEC3", "ScrollBar": "#FEC3F8", "TreeItem": "#D6D6D6", "Hyperlink": "#91FFEB", "ComboBox": "#D8B6D4"} |
| `ANNOTATION_FONT_SIZE`  | The font size for the annotation.                                                                       | Integer  | 22            |
| `PRINT_LOG`             | Whether to print the log in the console.                                                                | Boolean  | False         |
| `CONCAT_SCREENSHOT`     | Whether to concatenate the screenshots into a single image for the LLM input.                          | Boolean  | False         |
| `INCLUDE_LAST_SCREENSHOT` | Whether to include the screenshot from the last step in the observation.                             | Boolean  | True          |
| `LOG_LEVEL`             | The log level for the UFO agent.                                                                        | String   | "DEBUG"       |
| `REQUEST_TIMEOUT`       | The call timeout in seconds for the LLM model.                                                          | Integer  | 250           |
| `USE_APIS`              | Whether to allow the use of application APIs.                                                           | Boolean  | True          |
| `LOG_XML`               | Whether to log the XML file at every step.                                                              | Boolean  | False         |
| `SCREENSHOT_TO_MEMORY`  | Whether to allow the screenshot to [`Blackboard`](../agents/design/blackboard.md) for the agent's decision making.                              | Boolean  | True          |
| `SAVE_UI_TREE`          | Whether to save the UI tree in the log.                                                                 | Boolean  | False         |
| `SAVE_EXPERIENCE`       | Whether to save the experience, can be "always" for always save, "always_not" for always not save, "ask" for asking the user to save or not. By default, it is "always_not" | String   | "always_not"  |
| `TASK_STATUS`           | Whether to record the status of the tasks in batch execution mode.                                     | Boolean  | True         |


## Main Prompt Configuration

### Main Prompt Templates

The main prompt templates include the prompts in the UFO agent for both `system` and `user` roles.

| Configuration Option    | Description                                                         | Type   | Default Value                                      |
|-------------------------|---------------------------------------------------------------------|--------|----------------------------------------------------|
| `HOSTAGENT_PROMPT`      | The main prompt template for the `HostAgent`.                       | String | "ufo/prompts/share/base/host_agent.yaml"           |
| `APPAGENT_PROMPT`       | The main prompt template for the `AppAgent`.                        | String | "ufo/prompts/share/base/app_agent.yaml"            |
| `FOLLOWERAGENT_PROMPT`  | The main prompt template for the `FollowerAgent`.                   | String | "ufo/prompts/share/base/app_agent.yaml"            |
| `EVALUATION_PROMPT`     | The prompt template for the evaluation.                             | String | "ufo/prompts/evaluation/evaluate.yaml"             |

Lite versions of the main prompt templates can be found in the `ufo/prompts/share/lite` directory to reduce the input size for specific token limits.

### Example Prompt Templates

Example prompt templates are used for demonstration purposes in the UFO agent.

| Configuration Option         | Description                                                            | Type   | Default Value                                       |
|------------------------------|------------------------------------------------------------------------|--------|-----------------------------------------------------|
| `HOSTAGENT_EXAMPLE_PROMPT`   | The example prompt template for the `HostAgent` used for demonstration. | String | "ufo/prompts/examples/{mode}/host_agent_example.yaml"|
| `APPAGENT_EXAMPLE_PROMPT`    | The example prompt template for the `AppAgent` used for demonstration.  | String | "ufo/prompts/examples/{mode}/app_agent_example.yaml" |

Lite versions of the example prompt templates can be found in the `ufo/prompts/examples/lite/{mode}` directory to reduce the input size for demonstration purposes.

### Experience and Demonstration Learning

These configuration parameters are used for experience and demonstration learning in the UFO agent.

| Configuration Option          | Description                                    | Type   | Default Value                                      |
|-------------------------------|------------------------------------------------|--------|----------------------------------------------------|
| `EXPERIENCE_PROMPT`           | The prompt for self-experience learning.       | String | "ufo/prompts/experience/experience_summary.yaml"   |
| `EXPERIENCE_SAVED_PATH`       | The path to save the experience learning data. | String | "vectordb/experience/"                             |
| `DEMONSTRATION_PROMPT`        | The prompt for user demonstration learning.    | String | "ufo/prompts/demonstration/demonstration_summary.yaml" |
| `DEMONSTRATION_SAVED_PATH`    | The path to save the demonstration learning data. | String | "vectordb/demonstration/"                          |

### Application API Configuration

These prompt configuration parameters are used for the application and control APIs in the UFO agent.

| Configuration Option   | Description                         | Type   | Default Value                              |
|------------------------|-------------------------------------|--------|--------------------------------------------|
| `API_PROMPT`           | The prompt for the UI automation API. | String | "ufo/prompts/share/base/api.yaml"          |
| `APP_API_PROMPT_ADDRESS`      | The prompt address for the application API. | Dict | {"WINWORD.EXE": "ufo/prompts/apps/word/api.yaml", "EXCEL.EXE": "ufo/prompts/apps/excel/api.yaml", "msedge.exe": "ufo/prompts/apps/web/api.yaml", "chrome.exe": "ufo/prompts/apps/web/api.yaml"} |

## pywinauto Configuration

The API configuration parameters are used for the pywinauto API in the UFO agent.

| Configuration Option     | Description                                      | Type    | Default Value |
|--------------------------|--------------------------------------------------|---------|---------------|
| `CLICK_API`              | The API used for click action, can be `click_input` or `click`. | String  | "click_input" |
| `INPUT_TEXT_API`         | The API used for input text action, can be `type_keys` or `set_text`. | String  | "type_keys"   |
| `INPUT_TEXT_ENTER`       | Whether to press enter after typing the text.    | Boolean | False         |

## Control Filtering

The control filtering configuration parameters are used for control filtering in the agent's observation.

| Configuration Option                | Description                                      | Type    | Default Value           |
|-------------------------------------|--------------------------------------------------|---------|-------------------------|
| `CONTROL_FILTER`                    | The control filter type, can be `TEXT`, `SEMANTIC`, or `ICON`. | List    | []                      |
| `CONTROL_FILTER_TOP_K_PLAN`         | The control filter effect on top k plans from the agent. | Integer | 2                       |
| `CONTROL_FILTER_TOP_K_SEMANTIC`     | The control filter top k for semantic similarity. | Integer | 15                      |
| `CONTROL_FILTER_TOP_K_ICON`         | The control filter top k for icon similarity.    | Integer | 15                      |
| `CONTROL_FILTER_MODEL_SEMANTIC_NAME`| The control filter model name for semantic similarity. | String  | "all-MiniLM-L6-v2"      |
| `CONTROL_FILTER_MODEL_ICON_NAME`    | The control filter model name for icon similarity. | String  | "clip-ViT-B-32"         |

## Customizations

The customization configuration parameters are used for customizations in the UFO agent.

| Configuration Option   | Description                                  | Type    | Default Value                         |
|------------------------|----------------------------------------------|---------|---------------------------------------|
| `ASK_QUESTION`         | Whether to ask the user for a question.      | Boolean | True                                  |
| `USE_CUSTOMIZATION`    | Whether to enable the customization.         | Boolean | True                                  |
| `QA_PAIR_FILE`         | The path for the historical QA pairs.        | String  | "customization/historical_qa.txt"     |
| `QA_PAIR_NUM`          | The number of QA pairs for the customization.| Integer | 20                                    |

## Evaluation

The evaluation configuration parameters are used for the evaluation in the UFO agent.

| Configuration Option      | Description                                   | Type    | Default Value |
|---------------------------|-----------------------------------------------|---------|---------------|
| `EVA_SESSION`             | Whether to include the session in the evaluation. | Boolean | True          |
| `EVA_ROUND`               | Whether to include the round in the evaluation.   | Boolean | False         |
| `EVA_ALL_SCREENSHOTS`     | Whether to include all the screenshots in the evaluation. | Boolean | True          |

You can customize the configuration parameters in the `config_dev.yaml` file to suit your development needs and enhance the functionality of the UFO agent.