# Follower Mode

Follower mode enables UFO to execute a predefined list of steps in natural language. Unlike normal mode where the agent generates its own plan, follower mode creates an `AppAgent` that follows user-provided steps to interact with applications. This mode is particularly useful for debugging, software testing, and verification.

## Quick Start

### Step 1: Create a Plan File

Create a JSON plan file containing the steps for the agent to follow:

| Field | Description | Type |
| --- | --- | --- |
| task | The task description. | String |
| steps | The list of steps for the agent to follow. | List of Strings |
| object | The application or file to interact with. | String |

Example plan file:

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

The `object` field specifies the application or file the agent will interact with. This object should be opened and accessible before starting follower mode.

### Step 2: Start Follower Mode

Run the following command:

```bash
# Assume you are in the cloned UFO folder
python -m ufo --task {task_name} --mode follower --plan {plan_file}
```

**Parameters:**
- `{task_name}`: Name for this task execution (used for logging)
- `{plan_file}`: Path to the plan JSON file

### Step 3: Run in Batch (Optional)

To execute multiple plan files sequentially, provide a folder containing multiple plan files:

```bash
# Assume you are in the cloned UFO folder
python -m ufo --task {task_name} --mode follower --plan {plan_folder}
``` 

UFO will automatically detect and execute all plan files in the folder sequentially.

**Parameters:**
- `{task_name}`: Name for this batch execution (used for logging)
- `{plan_folder}`: Path to the folder containing plan JSON files

## Evaluation

UFO can automatically evaluate task completion. To enable evaluation, ensure `EVA_SESSION` is set to `True` in `config/ufo/system.yaml`.

Check the evaluation results in `logs/{task_name}/evaluation.log`.

## References

Follower mode uses a `PlanReader` to parse the plan file and creates a `FollowerSession` to execute the steps.

### PlanReader

The `PlanReader` is located at `ufo/module/sessions/plan_reader.py`.

:::module.sessions.plan_reader.PlanReader

### FollowerSession

The `FollowerSession` is located at `ufo/module/sessions/session.py`.

:::module.sessions.session.FollowerSession