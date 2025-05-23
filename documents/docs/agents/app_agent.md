# AppAgent 👾

An `AppAgent` is responsible for iteratively executing actions on the selected applications until the task is successfully concluded within a specific application. The `AppAgent` is created by the `HostAgent` to fulfill a sub-task within a `Round`. The `AppAgent` is responsible for executing the necessary actions within the application to fulfill the user's request. The `AppAgent` has the following features:

1. **[ReAct](https://arxiv.org/abs/2210.03629) with the Application** - The `AppAgent` recursively interacts with the application in a workflow of observation->thought->action, leveraging the multi-modal capabilities of Visual Language Models (VLMs) to comprehend the application UI and fulfill the user's request.
2. **Comprehension Enhancement** - The `AppAgent` is enhanced by Retrieval Augmented Generation (RAG) from heterogeneous sources, including external knowledge bases, and demonstration libraries, making the agent an application "expert".
3. **Versatile Skill Set** - The `AppAgent` is equipped with a diverse set of skills to support comprehensive automation, such as mouse, keyboard, native APIs, and "Copilot".

!!! tip
    You can find the how to enhance the `AppAgent` with external knowledge bases and demonstration libraries in the [Reinforcing AppAgent](../advanced_usage/reinforce_appagent/overview.md) documentation.


We show the framework of the `AppAgent` in the following diagram:

<h1 align="center">
    <img src="../../img/appagent2.png" alt="AppAgent Image" width="80%">
</h1>

## AppAgent Input

To interact with the application, the `AppAgent` receives the following inputs:

| Input | Description | Type |
| --- | --- | --- |
| User Request | The user's request in natural language. | String |
| Sub-Task | The sub-task description to be executed by the `AppAgent`, assigned by the `HostAgent`. | String |
| Current Application | The name of the application to be interacted with. | String |
| Control Information | Index, name and control type of available controls in the application. | List of Dictionaries |
| Application Screenshots | Screenshots of the application, including a clean screenshot, an annotated screenshot with labeled controls, and a screenshot with a rectangle around the selected control at the previous step (optional). | List of Strings |
| Previous Sub-Tasks | The previous sub-tasks and their completion status. | List of Strings |
| Previous Plan | The previous plan for the following steps. | List of Strings |
| HostAgent Message | The message from the `HostAgent` for the completion of the sub-task. | String |
| Retrived Information | The retrieved information from external knowledge bases or demonstration libraries. | String |
| Blackboard | The shared memory space for storing and sharing information among the agents. | Dictionary |


Below is an example of the annotated application screenshot with labeled controls. This follow the [Set-of-Mark](https://arxiv.org/pdf/2310.11441) paradigm.
<h1 align="center">
    <img src="../../img/screenshots.png" alt="AppAgent Image" width="90%">
</h1>


By processing these inputs, the `AppAgent` determines the necessary actions to fulfill the user's request within the application.

!!! tip
    Whether to concatenate the clean screenshot and annotated screenshot can be configured in the `CONCAT_SCREENSHOT` field in the `config_dev.yaml` file.

!!! tip
     Whether to include the screenshot with a rectangle around the selected control at the previous step can be configured in the `INCLUDE_LAST_SCREENSHOT` field in the `config_dev.yaml` file.


## AppAgent Output

With the inputs provided, the `AppAgent` generates the following outputs:

| Output | Description | Type |
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

Below is an example of the `AppAgent` output:

```json
{
    "Observation": "Application screenshot",
    "Thought": "Logical reasoning process",
    "ControlLabel": "Control index",
    "ControlText": "Control name",
    "Function": "Function name",
    "Args": ["arg1", "arg2"],
    "Status": "AgentState",
    "Plan": ["Step 1", "Step 2"],
    "Comment": "Additional comments",
    "SaveScreenshot": true
}
```

!!! info
    The `AppAgent` output is formatted as a JSON object by LLMs and can be parsed by the `json.loads` method in Python.


## AppAgent State
The `AppAgent` state is managed by a state machine that determines the next action to be executed based on the current state, as defined in the `ufo/agents/states/app_agent_states.py` module. The states include:

| State       | Description                                                                 |
|-------------|-----------------------------------------------------------------------------|
| `CONTINUE`  | Main execution loop; evaluates which subtasks are ready to launch or resume. |
| `ASSIGN`    | Selects an available application process and spawns the corresponding `AppAgent`. |
| `PENDING`   | Waits for user input to resolve ambiguity or gather additional task parameters. |
| `FINISH`    | All subtasks complete; cleans up agent instances and finalizes session state. |
| `FAIL`      | Enters recovery or abort mode upon irrecoverable failure.                    |


The state machine diagram for the `AppAgent` is shown below:
<h1 align="center">
    <img src="../../img/app_state.png"/> 
</h1>

The `AppAgent` progresses through these states to execute the necessary actions within the application and fulfill the sub-task assigned by the `HostAgent`.


## Knowledge Enhancement
The `AppAgent` is enhanced by Retrieval Augmented Generation (RAG) from heterogeneous sources, including external knowledge bases and demonstration libraries. The `AppAgent` leverages this knowledge to enhance its comprehension of the application and learn from demonstrations to improve its performance.

### Learning from Help Documents
User can provide help documents to the `AppAgent` to enhance its comprehension of the application and improve its performance in the `config.yaml` file. 

!!! tip
    Please find details configuration in the [documentation](../configurations/user_configuration.md). 
!!! tip
    You may also refer to the [here]() for how to provide help documents to the `AppAgent`.


In the `AppAgent`, it calls the `build_offline_docs_retriever` to build a help document retriever, and uses the `retrived_documents_prompt_helper` to contruct the prompt for the `AppAgent`.



### Learning from Bing Search
Since help documents may not cover all the information or the information may be outdated, the `AppAgent` can also leverage Bing search to retrieve the latest information. You can activate Bing search and configure the search engine in the `config.yaml` file.

!!! tip
    Please find details configuration in the [documentation](../configurations/user_configuration.md).
!!! tip
    You may also refer to the [here]() for the implementation of Bing search in the `AppAgent`.

In the `AppAgent`, it calls the `build_online_search_retriever` to build a Bing search retriever, and uses the `retrived_documents_prompt_helper` to contruct the prompt for the `AppAgent`.


### Learning from Self-Demonstrations
You may save successful action trajectories in the `AppAgent` to learn from self-demonstrations and improve its performance. After the completion of a `session`, the `AppAgent` will ask the user whether to save the action trajectories for future reference. You may configure the use of self-demonstrations in the `config.yaml` file.

!!! tip
     You can find details of the configuration in the [documentation](../configurations/user_configuration.md).

!!! tip
    You may also refer to the [here]() for the implementation of self-demonstrations in the `AppAgent`.

In the `AppAgent`, it calls the `build_experience_retriever` to build a self-demonstration retriever, and uses the `rag_experience_retrieve` to retrieve the demonstration for the `AppAgent`.

### Learning from Human Demonstrations
In addition to self-demonstrations, you can also provide human demonstrations to the `AppAgent` to enhance its performance by using the [Step Recorder](https://support.microsoft.com/en-us/windows/record-steps-to-reproduce-a-problem-46582a9b-620f-2e36-00c9-04e25d784e47) tool built in the Windows OS. The `AppAgent` will learn from the human demonstrations to improve its performance and achieve better personalization. The use of human demonstrations can be configured in the `config.yaml` file.

!!! tip
    You can find details of the configuration in the [documentation](../configurations/user_configuration.md).
!!! tip
    You may also refer to the [here]() for the implementation of human demonstrations in the `AppAgent`.

In the `AppAgent`, it calls the `build_human_demonstration_retriever` to build a human demonstration retriever, and uses the `rag_experience_retrieve` to retrieve the demonstration for the `AppAgent`.


## Skill Set for Automation
The `AppAgent` is equipped with a versatile skill set to support comprehensive automation within the application by calling the `create_puppeteer_interface` method. The skills include:

| Skill | Description |
| --- | --- |
| UI Automation | Mimicking user interactions with the application UI controls using the `UI Automation` and `Win32` API. |
| Native API | Accessing the application's native API to execute specific functions and actions. |
| In-App Agent | Leveraging the in-app agent to interact with the application's internal functions and features. |

By utilizing these skills, the `AppAgent` can efficiently interact with the application and fulfill the user's request. You can find more details in the [Automator](../automator/overview.md) documentation and the code in the `ufo/automator` module.


# Reference

:::agents.agent.app_agent.AppAgent