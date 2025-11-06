# Basic Prompt Template

The basic prompt template is a fixed format that is used to generate prompts for the `HostAgent`, `AppAgent` and `EvaluationAgent`. It includes the template for the `system` and `user` roles to construct the agent's prompt. 

Below is the default file path for the basic prompt template:

| Agent | File Path |
| --- | --- |
| HostAgent | [ufo/prompts/share/base/host_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/base/host_agent.yaml) |
| AppAgent | [ufo/prompts/share/base/app_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/base/app_agent.yaml) |
| EvaluationAgent | [ufo/prompts/evaluation/evaluate.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/evaluation/evaluate.yaml) |

!!! info
    You can configure the prompt template used in the configuration files. You can find more information about the configuration in the [System Configuration Guide](../../configuration/system/system_config.md).

## Template Structure

Each YAML template contains structured sections for the `system` and `user` roles:

- **System role**: Contains agent instructions, capabilities, and output format requirements
- **User role**: Defines the structure for runtime context injection (observations, tasks, etc.)

These templates are loaded and populated by the agent's **Prompter** class at runtime.

!!! tip
    Learn how templates are processed and combined with dynamic content in the [Prompter documentation](../../infrastructure/agents/design/prompter.md).
