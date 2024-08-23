# Follower Mode

The Follower mode is a feature of UFO that the agent follows a list of pre-defined steps in natural language to take actions on applications. Different from the normal mode, this mode creates an `FollowerAgent` that follows the plan list provided by the user to interact with the application, instead of generating the plan itself. This mode is useful for debugging and software testing or verification.

## Quick Start

### Step 1: Create a Plan file

Before starting the Follower mode, you need to create a plan file that contains the list of steps for the agent to follow. The plan file is a JSON file that contains the following fields:

| Field | Description | Type |
| --- | --- | --- |
| task | The task description. | String |
| steps | The list of steps for the agent to follow. | List of Strings |
| object | The application or file to interact with. | String |

Below is an example of a plan file:

```json
{
    "task": "Type in a text of 'Test For Fun' with heading 1 level",
    "steps": 
    [
        "1.type in 'Test For Fun'", 
        "2.Select the 'Test For Fun' text",
        "3.Click 'Home' tab to show the 'Styles' ribbon tab",
        "4.Click 'Styles' ribbon tab to show the style 'Heading 1'",
        "5.Click 'Heading 1' style to apply the style to the selected text"
    ],
    "object": "draft.docx"
}
```

!!! note
    The `object` field is the application or file that the agent will interact with. The object **must be active** (can be minimized) when starting the Follower mode.


### Step 2: Start the Follower Mode
To start the Follower mode, run the following command:

```bash
# assume you are in the cloned UFO folder
python ufo.py --task_name {task_name} --mode follower --plan {plan_file}
```

!!! tip
    Replace `{task_name}` with the name of the task and `{plan_file}` with the path to the plan file.


### Step 3: Run in Batch (Optional)

You can also run the Follower mode in batch mode by providing a folder containing multiple plan files. The agent will follow the plans in the folder one by one. To run in batch mode, run the following command:

```bash
# assume you are in the cloned UFO folder
python ufo.py --task_name {task_name} --mode follower --plan {plan_folder}
``` 

UFO will automatically detect the plan files in the folder and run them one by one.

!!! tip
    Replace `{task_name}` with the name of the task and `{plan_folder}` with the path to the folder containing plan files.


## Evaluation
You may want to evaluate the `task` is completed successfully or not by following the plan. UFO will call the `EvaluationAgent` to evaluate the task if `EVA_SESSION` is set to `True` in the `config_dev.yaml` file.

You can check the evaluation log in the `logs/{task_name}/evaluation.log` file. 

# References
The follower mode employs a `PlanReader` to parse the plan file and create a `FollowerSession` to follow the plan. 

## PlanReader
The `PlanReader` is located in the `ufo/module/sessions/plan_reader.py` file.

:::module.sessions.plan_reader.PlanReader

<br>
## FollowerSession

The `FollowerSession` is also located in the `ufo/module/sessions/session.py` file.

:::module.sessions.session.FollowerSession