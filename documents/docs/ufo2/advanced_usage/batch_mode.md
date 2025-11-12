# Batch Mode

Batch mode allows automated execution of tasks on specific applications or files using predefined plan files. This mode is particularly useful for repetitive tasks on Microsoft Office applications (Word, Excel, PowerPoint).

## Quick Start

### Step 1: Create a Plan File

Create a JSON plan file that defines the task to be automated. The plan file should contain the following fields:

| Field  | Description                                                                                  | Type    |
| ------ | -------------------------------------------------------------------------------------------- | ------- |
| task   | The task description.                                                                        | String  |
| object | The application or file to interact with.                                                    | String  |
| close  | Determines whether to close the corresponding application or file after completing the task. | Boolean |

Example plan file:

```json
{
    "task": "Type in a text of 'Test For Fun' with heading 1 level",
    "object": "draft.docx",
    "close": false
}
```

**Important:** The `close` field should be a boolean value (`true` or `false`), not a Python boolean (`True` or `False`).

The file structure should be organized as follows:

```
Parent/
├── tasks/
│   └── plan.json
└── files/
    └── draft.docx
```

The `object` field in the plan file refers to files in the `files` directory. The plan reader will automatically resolve the full file path by replacing `tasks` with `files` in the directory structure.

### Step 2: Start Batch Mode

Run the following command to start batch mode:

```bash
# Assume you are in the cloned UFO folder
python -m ufo --task {task_name} --mode batch_normal --plan {plan_file}
```

**Parameters:**
- `{task_name}`: Name for this task execution (used for logging)
- `{plan_file}`: Full path to the plan JSON file (e.g., `C:/Parent/tasks/plan.json`)

### Supported Applications

Batch mode currently supports the following Microsoft Office applications:

- **Word** (`.docx` files) - `WINWORD.EXE`
- **Excel** (`.xlsx` files) - `EXCEL.EXE`
- **PowerPoint** (`.pptx` files) - `POWERPNT.EXE`

The application will be automatically launched when the batch mode starts, and the specified file will be opened and maximized.

## Evaluation

UFO can automatically evaluate whether the task was completed successfully. To enable evaluation, ensure `EVA_SESSION` is set to `True` in the `config/ufo/system.yaml` file.

Check the evaluation results in `logs/{task_name}/evaluation.log`.

## References

The batch mode uses a `PlanReader` to parse the plan file and creates a `FromFileSession` to execute the plan.

### PlanReader

The `PlanReader` is located at `ufo/module/sessions/plan_reader.py`.

:::module.sessions.plan_reader.PlanReader

### FromFileSession

The `FromFileSession` is located at `ufo/module/sessions/session.py`.

:::module.sessions.session.FromFileSession