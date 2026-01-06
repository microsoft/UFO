# Basic Prompt Template

The basic prompt template is a fixed format used to generate prompts for the `HostAgent`, `AppAgent`, and `EvaluationAgent`. It includes templates for the `system` and `user` roles to construct each agent's prompt.

Default file paths for basic prompt templates:

| Agent | File Path |
| --- | --- |
| HostAgent | [ufo/prompts/share/base/host_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/base/host_agent.yaml) |
| AppAgent | [ufo/prompts/share/base/app_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/base/app_agent.yaml) |
| EvaluationAgent | [ufo/prompts/evaluation/evaluate.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/evaluation/evaluate.yaml) |

You can configure the prompt template in the system configuration files. See the [System Configuration Guide](../../configuration/system/system_config.md) for details.

## Template Structure

Each YAML template contains structured sections for the `system` and `user` roles:

- **System role**: Contains agent instructions, capabilities, and output format requirements
- **User role**: Defines the structure for runtime context injection (observations, tasks, etc.)

These templates are loaded and populated by the agent's `Prompter` class at runtime. Learn how templates are processed and combined with dynamic content in the [Prompter documentation](../../infrastructure/agents/design/prompter.md).
