# HostAgent 🤖

The `HostAgent` assumes three primary responsibilities:

- **Task Decomposition.** Given a user's natural language input, `HostAgent` identifies the underlying task goal and decomposes it into a dependency-ordered subtask graph.

- **Application Lifecycle Management.** For each subtask, `HostAgent` inspects system process metadata (via UIA APIs) to determine whether the target application is running. If not, it launches the program and registers it with the runtime.

- **`AppAgent` Instantiation.** `HostAgent` spawns the corresponding `AppAgent` for each active application, providing it with task context, memory references, and relevant toolchains (e.g., APIs, documentation).

- **Task Scheduling and Control.** The global execution plan is serialized into a finite state machine (FSM), allowing `HostAgent` to enforce execution order, detect failures, and resolve dependencies across agents.

- **Shared State Communication.** `HostAgent` reads from and writes to a global blackboard, enabling inter-agent communication and system-level observability for debugging and replay.

Below is a diagram illustrating the `HostAgent` architecture and its interactions with other components:

<h1 align="center">
    <img src="../../img/hostagent2.png" alt="Blackboard Image">
</h1>


The `HostAgent` activates its `Processor` to process the user's request and decompose it into sub-tasks. Each sub-task is then assigned to an `AppAgent` for execution. The `HostAgent` monitors the progress of the `AppAgents` and ensures the successful completion of the user's request.

## HostAgent Input

The `HostAgent` receives the following inputs:

| Input | Description | Type |
| --- | --- | --- |
| User Request | The user's request in natural language. | String |
| Application Information | Information about the existing active applications. | List of Strings |
| Desktop Screenshots | Screenshots of the desktop to provide context to the `HostAgent`. | Image |
| Previous Sub-Tasks | The previous sub-tasks and their completion status. | List of Strings |
| Previous Plan | The previous plan for the following sub-tasks. | List of Strings |
| Blackboard | The shared memory space for storing and sharing information among the agents. | Dictionary |

By processing these inputs, the `HostAgent` determines the appropriate application to fulfill the user's request and orchestrates the `AppAgents` to execute the necessary actions.

## HostAgent Output

With the inputs provided, the `HostAgent` generates the following outputs:

| Output | Description | Type |
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


Below is an example of the `HostAgent` output:

```json
{
    "Observation": "Desktop screenshot",
    "Thought": "Logical reasoning process",
    "Current Sub-Task": "Sub-task description",
    "Message": "Message to AppAgent",
    "ControlLabel": "Application index",
    "ControlText": "Application name",
    "Plan": ["Sub-task 1", "Sub-task 2"],
    "Status": "AgentState",
    "Comment": "Additional comments",
    "Questions": ["Question 1", "Question 2"],
    "Bash": "Bash command"
}
```

!!! info
    The `HostAgent` output is formatted as a JSON object by LLMs and can be parsed by the `json.loads` method in Python.


## HostAgent State

The `HostAgent` progresses through different states, as defined in the `ufo/agents/states/host_agent_states.py` module. The states include:

| State       | Description                                                                 |
|-------------|-----------------------------------------------------------------------------|
| `CONTINUE`  | Default state for action planning and execution.                            |
| `PENDING`   | Invoked for safety-critical actions (e.g., destructive operations); requires user confirmation. |
| `FINISH`    | Task completed; execution ends.                                              |
| `FAIL`      | Irrecoverable failure detected (e.g., application crash, permission error). |


The state machine diagram for the `HostAgent` is shown below:
<h1 align="center">
    <img src="../../img/host_state.png"/> 
</h1>


The `HostAgent` transitions between these states based on the user's request, the application information, and the progress of the `AppAgents` in executing the sub-tasks.


## Task Decomposition
Upon receiving the user's request, the `HostAgent` decomposes it into sub-tasks and assigns each sub-task to an `AppAgent` for execution. The `HostAgent` determines the appropriate application to fulfill the user's request based on the application information and the user's request. It then orchestrates the `AppAgents` to execute the necessary actions to complete the sub-tasks. We show the task decomposition process in the following figure:

<h1 align="center">
    <img src="../../img/desomposition.png" alt="Task Decomposition Image" width="100%">
</h1>

## Creating and Registering AppAgents
When the `HostAgent` determines the need for a new `AppAgent` to fulfill a sub-task, it creates an instance of the `AppAgent` and registers it with the `HostAgent`, by calling the `create_subagent` method:

```python
def create_subagent(
        self,
        agent_type: str,
        agent_name: str,
        process_name: str,
        app_root_name: str,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
        *args,
        **kwargs,
    ) -> BasicAgent:
        """
        Create an SubAgent hosted by the HostAgent.
        :param agent_type: The type of the agent to create.
        :param agent_name: The name of the SubAgent.
        :param process_name: The process name of the app.
        :param app_root_name: The root name of the app.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :return: The created SubAgent.
        """
        app_agent = self.agent_factory.create_agent(
            agent_type,
            agent_name,
            process_name,
            app_root_name,
            is_visual,
            main_prompt,
            example_prompt,
            api_prompt,
            *args,
            **kwargs,
        )
        self.appagent_dict[agent_name] = app_agent
        app_agent.host = self
        self._active_appagent = app_agent

        return app_agent
```

The `HostAgent` then assigns the sub-task to the `AppAgent` for execution and monitors its progress.

# Reference

:::agents.agent.host_agent.HostAgent
