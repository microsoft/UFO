# Agent Prompter

The `Prompter` is a key component of the UFO framework, responsible for constructing prompts for the LLM to generate responses. The `Prompter` is implemented in the `ufo/prompts` folder. Each agent has its own `Prompter` class that defines the structure of the prompt and the information to be fed to the LLM.

## Components

A prompt fed to the LLM usually a list of dictionaries, where each dictionary contains the following keys:

| Key | Description |
| --- | --- |
| `role` | The role of the text in the prompt, can be `system`, `user`, or `assistant`. |
| `content` | The content of the text for the specific role. |

!!!tip
    You may find the [official documentation](https://help.openai.com/en/articles/7042661-moving-from-completions-to-chat-completions-in-the-openai-api) helpful for constructing the prompt.

In the `__init__` method of the `Prompter` class, you can define the template of the prompt for each component, and the final prompt message is constructed by combining the templates of each component using the `prompt_construction` method.

### System Prompt
The system prompt use the template configured in the `config_dev.yaml` file for each agent. It usually contains the instructions for the agent's role, action, tips, reponse format, etc.
You need use the `system_prompt_construction` method to construct the system prompt.

Prompts on the API instructions, and demonstration examples are also included in the system prompt, which are constructed by the `api_prompt_helper` and `examples_prompt_helper` methods respectively. Below is the sub-components of the system prompt:

| Component | Description | Method |
| --- | --- | --- |
| `apis` | The API instructions for the agent. | `api_prompt_helper` |
| `examples` | The demonstration examples for the agent. | `examples_prompt_helper` |

### User Prompt
The user prompt is constructed based on the information from the agent's observation, external knowledge, and `Blackboard`. You can use the `user_prompt_construction` method to construct the user prompt. Below is the sub-components of the user prompt:

| Component | Description | Method |
| --- | --- | --- |
| `observation` | The observation of the agent. | `user_content_construction` |
| `retrieved_docs` | The knowledge retrieved from the external knowledge base. | `retrived_documents_prompt_helper` |
| `blackboard` | The information stored in the `Blackboard`. | `blackboard_to_prompt` |


# Reference
You can find the implementation of the `Prompter` in the `ufo/prompts` folder. Below is the basic structure of the `Prompter` class:

:::prompter.basic.BasicPrompter


!!!tip
    You can customize the `Prompter` class to tailor the prompt to your requirements.