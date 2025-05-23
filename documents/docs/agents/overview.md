# Agents

In UFO, there are four types of agents: `HostAgent`, `AppAgent`, `FollowerAgent`, and `EvaluationAgent`. Each agent has a specific role in the UFO system and is responsible for different aspects of the user interaction process:

| Agent                                              | Description                                                                                                |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| [`HostAgent`](../agents/host_agent.md)             | Decomposes the user request into sub-tasks and selects the appropriate application to fulfill the request. |
| [`AppAgent`](../agents/app_agent.md)               | Executes actions on the selected application.                                                              |
| [`FollowerAgent`](../agents/follower_agent.md)     | Follows the user's instructions to complete the task.                                                      |
| [`EvaluationAgent`](../agents/evaluation_agent.md) | Evaluates the completeness of a session or a round.                                                        |

In the normal workflow, only the `HostAgent` and `AppAgent` are involved in the user interaction process. The `FollowerAgent` and `EvaluationAgent` are used for specific tasks.

Please see below the orchestration of the agents in UFO:

<h1 align="center">
    <img src="../../img/framework_v2.png"/> 
</h1>

## Main Components

An agent in UFO is composed of the following main components to fulfill its role in the UFO system:

| Component                                      | Description                                                                                                      |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| [`State`](../agents/design/state.md)           | Represents the current state of the agent and determines the next action and agent to handle the request.        |
| [`Memory`](../agents/design/memory.md)         | Stores information about the user request, application state, and other relevant data.                           |
| [`Blackboard`](../agents/design/blackboard.md) | Stores information shared between agents.                                                                        |
| [`Prompter`](../agents/design/prompter.md)     | Generates prompts for the language model based on the user request and application state.                        |
| [`Processor`](../agents/design/processor.md)   | Processes the workflow of the agent, including handling user requests, executing actions, and memory management. |

## Reference

Below is the reference for the `Agent` class in UFO. All agents in UFO inherit from the `Agent` class and implement necessary methods to fulfill their roles in the UFO system.

::: agents.agent.basic.BasicAgent

