# Context

The `Context` object is a shared state object that stores the state of the conversation across all `Rounds` within a `Session`. It is used to maintain the context of the conversation, as well as the overall status of the conversation.

## Context Attributes

The attributes of the `Context` object are defined in the `ContextNames` class, which is an `Enum`. The `ContextNames` class specifies various context attributes used throughout the session. Below is the definition:
```python
class ContextNames(Enum):
    """
    The context names.
    """

    ID = "ID"  # The ID of the session
    MODE = "MODE"  # The mode of the session
    LOG_PATH = "LOG_PATH"  # The folder path to store the logs
    REQUEST = "REQUEST"  # The current request
    SUBTASK = "SUBTASK"  # The current subtask processed by the AppAgent
    PREVIOUS_SUBTASKS = "PREVIOUS_SUBTASKS"  # The previous subtasks processed by the AppAgent
    HOST_MESSAGE = "HOST_MESSAGE"  # The message from the HostAgent sent to the AppAgent
    REQUEST_LOGGER = "REQUEST_LOGGER"  # The logger for the LLM request
    LOGGER = "LOGGER"  # The logger for the session
    EVALUATION_LOGGER = "EVALUATION_LOGGER"  # The logger for the evaluation
    ROUND_STEP = "ROUND_STEP"  # The step of all rounds
    SESSION_STEP = "SESSION_STEP"  # The step of the current session
    CURRENT_ROUND_ID = "CURRENT_ROUND_ID"  # The ID of the current round
    APPLICATION_WINDOW = "APPLICATION_WINDOW"  # The window of the application
    APPLICATION_PROCESS_NAME = "APPLICATION_PROCESS_NAME"  # The process name of the application
    APPLICATION_ROOT_NAME = "APPLICATION_ROOT_NAME"  # The root name of the application
    CONTROL_REANNOTATION = "CONTROL_REANNOTATION"  # The re-annotation of the control provided by the AppAgent
    SESSION_COST = "SESSION_COST"  # The cost of the session
    ROUND_COST = "ROUND_COST"  # The cost of all rounds
    ROUND_SUBTASK_AMOUNT = "ROUND_SUBTASK_AMOUNT"  # The amount of subtasks in all rounds
    CURRENT_ROUND_STEP = "CURRENT_ROUND_STEP"  # The step of the current round
    CURRENT_ROUND_COST = "CURRENT_ROUND_COST"  # The cost of the current round
    CURRENT_ROUND_SUBTASK_AMOUNT = "CURRENT_ROUND_SUBTASK_AMOUNT"  # The amount of subtasks in the current round
    STRUCTURAL_LOGS = "STRUCTURAL_LOGS"  # The structural logs of the session
```
Each attribute is a string that represents a specific aspect of the session context, ensuring that all necessary information is accessible and manageable within the application.


## Attributes Description

| Attribute                      | Description                                             |
|--------------------------------|---------------------------------------------------------|
| `ID`                           | The ID of the session.                                  |
| `MODE`                         | The mode of the session.                                |
| `LOG_PATH`                     | The folder path to store the logs.                      |
| `REQUEST`                     | The current request.                                    |
| `SUBTASK`                      | The current subtask processed by the AppAgent.          |
| `PREVIOUS_SUBTASKS`            | The previous subtasks processed by the AppAgent.        |
| `HOST_MESSAGE`                 | The message from the HostAgent sent to the AppAgent.    |
| `REQUEST_LOGGER`               | The logger for the LLM request.                         |
| `LOGGER`                       | The logger for the session.                             |
| `EVALUATION_LOGGER`            | The logger for the evaluation.                          |
| `ROUND_STEP`                   | The step of all rounds.                                 |
| `SESSION_STEP`                 | The step of the current session.                        |
| `CURRENT_ROUND_ID`             | The ID of the current round.                            |
| `APPLICATION_WINDOW`           | The window of the application.                          |
| `APPLICATION_PROCESS_NAME`     | The process name of the application.                    |
| `APPLICATION_ROOT_NAME`        | The root name of the application.                       |
| `CONTROL_REANNOTATION`         | The re-annotation of the control provided by the AppAgent. |
| `SESSION_COST`                 | The cost of the session.                                |
| `ROUND_COST`                   | The cost of all rounds.                                 |
| `ROUND_SUBTASK_AMOUNT`         | The amount of subtasks in all rounds.                   |
| `CURRENT_ROUND_STEP`           | The step of the current round.                          |
| `CURRENT_ROUND_COST`           | The cost of the current round.                          |
| `CURRENT_ROUND_SUBTASK_AMOUNT` | The amount of subtasks in the current round.            |
| `STRUCTURAL_LOGS`              | The structural logs of the session.                     |


# Reference for the `Context` object

::: module.context.Context