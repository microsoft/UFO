# Step Logs

The step log contains the agent's response to the user's request and additional information at every step. The step log is stored in the `response.log` file. The log fields are different for `HostAgent` and `AppAgent`. The step log is at the `info` level.
## HostAgent Logs

The `HostAgent` logs contain the following fields:


### LLM Output

| Field | Description | Type |
| --- | --- | --- |
| Observation | The observation of current desktop screenshots. | String |
| Thought | The logical reasoning process of the `HostAgent`. | String |
| Current Sub-Task | The current sub-task to be executed by the `AppAgent`. | String |
| Message | The message to be sent to the `AppAgent` for the completion of the sub-task. | String |
| ControlLabel | The index of the selected application to execute the sub-task. | String |
| ControlText | The name of the selected application to execute the sub-task. | String |
| Plan | The plan for the following sub-tasks after the current sub-task. | List of Strings |
| Status | The status of the agent, mapped to the `AgentState`. | String |
| Comment | Additional comments or information provided to the user. | String |
| Questions | The questions to be asked to the user for additional information. | List of Strings |
| Bash | The bash command to be executed by the `HostAgent`. It can be used to open applications or execute system commands. | String |


### Additional Information

| Field | Description | Type |
| --- | --- | --- |
| Step | The step number of the session. | Integer |
| RoundStep | The step number of the current round. | Integer |
| AgentStep | The step number of the `HostAgent`. | Integer |
| Round | The round number of the session. | Integer |
| ControlLabel | The index of the selected application to execute the sub-task. | Integer |
| ControlText | The name of the selected application to execute the sub-task. | String |
| Request | The user request. | String |
| Agent | The agent that executed the step, set to `HostAgent`. | String |
| AgentName | The name of the agent. | String |
| Application | The application process name. | String |
| Cost | The cost of the step. | Float |
| Results | The results of the step, set to an empty string. | String |
| CleanScreenshot | The image path of the desktop screenshot. | String |
| AnnotatedScreenshot | The image path of the annotated application screenshot. | String |
| ConcatScreenshot | The image path of the concatenated application screenshot. | String |
| SelectedControlScreenshot | The image path of the selected control screenshot. | String |
| time_cost | The time cost of each step in the process. | Dictionary |



## AppAgent Logs

The `AppAgent` logs contain the following fields:

### LLM Output

| Field | Description | Type |
| --- | --- | --- |
| Observation | The observation of the current application screenshots. | String |
| Thought | The logical reasoning process of the `AppAgent`. | String |
| ControlLabel | The index of the selected control to interact with. | String |
| ControlText | The name of the selected control to interact with. | String |
| Function | The function to be executed on the selected control. | String |
| Args | The arguments required for the function execution. | List of Strings |
| Status | The status of the agent, mapped to the `AgentState`. | String |
| Plan | The plan for the following steps after the current action. | List of Strings |
| Comment | Additional comments or information provided to the user. | String |
| SaveScreenshot | The flag to save the screenshot of the application to the `blackboard` for future reference. | Boolean |

### Additional Information

| Field | Description | Type |
| --- | --- | --- |
| Step | The step number of the session. | Integer |
| RoundStep | The step number of the current round. | Integer |
| AgentStep | The step number of the `AppAgent`. | Integer |
| Round | The round number of the session. | Integer |
| Subtask | The sub-task to be executed by the `AppAgent`. | String |
| SubtaskIndex | The index of the sub-task in the current round. | Integer |
| Action | The action to be executed by the `AppAgent`. | String |
| ActionType | The type of the action to be executed. | String |
| Request | The user request. | String |
| Agent | The agent that executed the step, set to `AppAgent`. | String |
| AgentName | The name of the agent. | String |
| Application | The application process name. | String |
| Cost | The cost of the step. | Float |
| Results | The results of the step. | String |
| CleanScreenshot | The image path of the desktop screenshot. | String |
| AnnotatedScreenshot | The image path of the annotated application screenshot. | String |
| ConcatScreenshot | The image path of the concatenated application screenshot. | String |
| time_cost | The time cost of each step in the process. | Dictionary |

!!! tip
    You can use the following python code to read the request log:

        import json

        with open('logs/{task_name}/request.log', 'r') as f:
            for line in f:
                log = json.loads(line)

!!! info
    The `FollowerAgent` logs share the same fields as the `AppAgent` logs.