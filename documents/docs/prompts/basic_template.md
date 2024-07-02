# Basic Prompt Template

The basic prompt template is a fixed format that is used to generate prompts for the `HostAgent`, `AppAgent`, `FollowerAgent`, and `EvaluationAgent`. It include the template for the `system` and `user` roles to construct the agent's prompt. 

Below is the default file path for the basic prompt template:

| Agent | File Path | Version |
| --- | --- | --- |
| HostAgent | [ufo/prompts/share/base/host_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/base/host_agent.yaml) | base |
| HostAgent | [ufo/prompts/share/lite/host_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/lite/host_agent.yaml) | lite |
| AppAgent | [ufo/prompts/share/base/app_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/base/app_agent.yaml) | base |
| AppAgent | [ufo/prompts/share/lite/app_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/lite/app_agent.yaml) | lite |
| FollowerAgent | [ufo/prompts/share/base/app_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/base/app_agent.yaml) | base |
| FollowerAgent | [ufo/prompts/share/lite/app_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/share/lite/app_agent.yaml) | lite |
| EvaluationAgent | [ufo/prompts/evaluation/evaluation_agent.yaml](https://github.com/microsoft/UFO/blob/main/ufo/prompts/evaluation/evaluate.yaml) | - |

!!! info
    You can configure the prompt template used in the `config.yaml` file. You can find more information about the configuration file [here](../configurations/developer_configuration.md).
