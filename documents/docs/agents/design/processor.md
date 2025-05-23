# Agents Processor

The `Processor` is a key component of the agent to process the core logic of the agent to process the user's request. The `Processor` is implemented as a class in the `ufo/agents/processors` folder. Each agent has its own `Processor` class withing the folder.

## Core Process
Once called, an agent follows a series of steps to process the user's request defined in the `Processor` class by calling the `process` method. The workflow of the `process` is as follows:

| Step | Description | Function |
| --- | --- | --- |
| 1 | Print the step information. | `print_step_info` |
| 2 | Capture the screenshot of the application. | `capture_screenshot` |
| 3 | Get the control information of the application. | `get_control_info` |
| 4 | Get the prompt message for the LLM. | `get_prompt_message` |
| 5 | Generate the response from the LLM. | `get_response` |
| 6 | Update the cost of the step. | `update_cost` |
| 7 | Parse the response from the LLM. | `parse_response` |
| 8 | Execute the action based on the response. | `execute_action` |
| 9 | Update the memory and blackboard. | `update_memory` |
| 10 | Update the status of the agent. | `update_status` |

At each step, the `Processor` processes the user's request by invoking the corresponding method sequentially to execute the necessary actions.


The process may be paused. It can be resumed, based on the agent's logic and the user's request using the `resume` method.

## Reference
Below is the basic structure of the `Processor` class:
:::agents.processors.basic.BaseProcessor