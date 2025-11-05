# Agent Blackboard

The `Blackboard` is a shared memory space that is visible to all agents in the UFO framework. It stores information required for agents to interact with the user and applications at every step. The `Blackboard` is a key component of the UFO framework, enabling agents to share information and collaborate to fulfill user requests. The `Blackboard` is implemented as a class in the `ufo/agents/memory/blackboard.py` file.

## Components

The `Blackboard` consists of the following data components:

| Component | Description |
| --- | --- |
| `questions` | A list of questions that UFO asks the user, along with their corresponding answers. |
| `requests` | A list of historical user requests received in previous `Round`. |
| `trajectories` | A list of step-wise trajectories that record the agent's actions and decisions at each step. |
| `screenshots` | A list of screenshots taken by the agent when it believes the current state is important for future reference. |

!!! tip
    The keys stored in the `trajectories` are configured as `HISTORY_KEYS` in the `config_dev.yaml` file. You can customize the keys based on your requirements and the agent's logic.

!!! tip
    Whether to save the screenshots is determined by the `AppAgent`. You can enable or disable screenshot capture by setting the `SCREENSHOT_TO_MEMORY` flag in the `config_dev.yaml` file.

## Blackboard to Prompt

Data in the `Blackboard` is based on the `MemoryItem` class. It has a method `blackboard_to_prompt` that converts the information stored in the `Blackboard` to a string prompt. Agents call this method to construct the prompt for the LLM's inference. The `blackboard_to_prompt` method is defined as follows:

```python
def blackboard_to_prompt(self) -> List[str]:
    """
    Convert the blackboard to a prompt.
    :return: The prompt.
    """
    prefix = [
        {
            "type": "text",
            "text": "[Blackboard:]",
        }
    ]

    blackboard_prompt = (
        prefix
        + self.texts_to_prompt(self.questions, "[Questions & Answers:]")
        + self.texts_to_prompt(self.requests, "[Request History:]")
        + self.texts_to_prompt(self.trajectories, "[Step Trajectories Completed Previously:]")
        + self.screenshots_to_prompt()
    )

    return blackboard_prompt
```

## Reference

:::agents.memory.blackboard.Blackboard

!!!note
    You can customize the class to tailor the `Blackboard` to your requirements.