# AI Tool Automator

The AI Tool Automator is a component of the UFO framework that enables the agent to interact with AI tools based on large language models (LLMs). The AI Tool Automator is designed to facilitate the integration of LLM-based AI tools into the UFO framework, enabling the agent to leverage the capabilities of these tools to perform complex tasks.

!!! note
    UFO can also call in-app AI tools, such as `Copilot`, to assist with the automation process. This is achieved by using either `UI Automation` or `API` to interact with the in-app AI tool. These in-app AI tools differ from the AI Tool Automator, which is designed to interact with external AI tools based on LLMs that are not integrated into the application.

## Configuration
The AI Tool Automator shares the same prompt configuration options as the UI Automator:

| Configuration Option    | Description                                                                                             | Type     | Default Value |
|-------------------------|---------------------------------------------------------------------------------------------------------|----------|---------------|
| `API_PROMPT`           | The prompt for the UI automation API. | String | "ufo/prompts/share/base/api.yaml"          |


## Receiver
The AI Tool Automator shares the same receiver structure as the UI Automator. Please refer to the [UI Automator Receiver](./ui_automator.md#receiver) section for more details.

## Command
The command of the AI Tool Automator shares the same structure as the UI Automator. Please refer to the [UI Automator Command](./ui_automator.md#command) section for more details. The list of available commands in the AI Tool Automator is shown below:

| Command Name | Function Name | Description |
|--------------|---------------|-------------|
| `AnnotationCommand` | `annotation` | Annotate the control items on the screenshot. |
| `SummaryCommand` | `summary` | Summarize the observation of the current application window. |

