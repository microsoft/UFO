# Batch Mode

Batch mode is a feature of UFO, the agent allows batch automation of tasks.

## Quick Start

### Step 1: Create a Plan file

Before starting the Batch mode, you need to create a plan file that contains the list of steps for the agent to follow. The plan file is a JSON file that contains the following fields:

| Field  | Description                                                                                  | Type    |
| ------ | -------------------------------------------------------------------------------------------- | ------- |
| task   | The task description.                                                                        | String  |
| object | The application or file to interact with.                                                    | String  |
| close  | Determines whether to close the corresponding application or file after completing the task. | Boolean |

Below is an example of a plan file:

```json
{
    "task": "Type in a text of 'Test For Fun' with heading 1 level",
    "object": "draft.docx",
    "close": False
}
```

!!! note
    The `object` field is the application or file that the agent will interact with. The object **must be active** (can be minimized) when starting the Batch mode.
    The structure of your files should be as follows, where `tasks` is the directory for your tasks and `files` is where your object files are stored:

    - Parent
      - tasks
      - files


### Step 2: Start the Batch Mode
To start the Batch mode, run the following command:

```bash
# assume you are in the cloned UFO folder
python ufo.py --task_name {task_name} --mode batch_normal --plan {plan_file}
```

!!! tip
    Replace `{task_name}` with the name of the task and `{plan_file}` with the `Path_to_Parent/Plan_file`.



## Evaluation
You may want to evaluate the `task` is completed successfully or not by following the plan. UFO will call the `EvaluationAgent` to evaluate the task if `EVA_SESSION` is set to `True` in the `config_dev.yaml` file.

You can check the evaluation log in the `logs/{task_name}/evaluation.log` file. 

# References
The batch mode employs a `PlanReader` to parse the plan file and create a `FromFileSession` to follow the plan. 

## PlanReader
The `PlanReader` is located in the `ufo/module/sessions/plan_reader.py` file.

:::module.sessions.plan_reader.PlanReader

<br>
## FollowerSession

The `FromFileSession` is also located in the `ufo/module/sessions/session.py` file.

:::module.sessions.session.FromFileSession