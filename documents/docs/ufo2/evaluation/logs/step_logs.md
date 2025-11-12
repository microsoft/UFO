# Step Logs

The step log captures agent responses and execution details at every step. Each line in `response.log` is a JSON entry representing one agent action.

## Location

```
logs/{task_name}/response.log
```

## HostAgent Logs

### LLM Response Fields

| Field | Description | Type |
| --- | --- | --- |
| `observation` | Desktop screenshot analysis and current state | String |
| `thought` | Reasoning process for task decomposition | String |
| `current_subtask` | Subtask to be executed by AppAgent | String |
| `message` | Instructions and context for AppAgent | List of Strings |
| `control_label` | Index of selected application | String |
| `control_text` | Name of selected application | String |
| `plan` | Future subtasks after current one | List of Strings |
| `status` | Agent state: `FINISH`, `CONTINUE`, `PENDING`, or `ASSIGN` | String |
| `comment` | User-facing summary or progress update | String |
| `questions` | Questions requiring user clarification | List of Strings |
| `function` | System command to execute (optional) | String |

### Additional Metadata

| Field | Description | Type |
| --- | --- | --- |
| `step` | Global step number in session | Integer |
| `round_step` | Step number within current round | Integer |
| `agent_step` | Step number for this agent instance | Integer |
| `round_num` | Current round number | Integer |
| `request` | Original user request | String |
| `agent_type` | Set to `HostAgent` | String |
| `agent_name` | Agent instance name | String |
| `application` | Application process name | String |
| `cost` | LLM cost for this step | Float |
| `result` | Execution results | String |
| `screenshot_clean` | Clean desktop screenshot path | String |
| `screenshot_annotated` | Annotated screenshot path | String |
| `screenshot_concat` | Concatenated screenshot path | String |
| `screenshot_selected_control` | Selected control screenshot path | String |
| `time_cost` | Time spent on each processing phase | Dictionary |

## AppAgent Logs

### LLM Response Fields

| Field | Description | Type |
| --- | --- | --- |
| `observation` | Application UI analysis and status | String |
| `thought` | Reasoning for next action | String |
| `control_label` | Index of selected control element | String |
| `control_text` | Name of selected control element | String |
| `action` | Action details including function and arguments | Dictionary or List |
| `status` | Agent state (CONTINUE, FINISH, etc.) | String |
| `plan` | Planned steps after current action | List of Strings |
| `comment` | Progress summary or completion notes | String |
| `save_screenshot` | Screenshot save configuration | Dictionary |

### Additional Metadata

| Field | Description | Type |
| --- | --- | --- |
| `step` | Global step number in session | Integer |
| `round_step` | Step number within current round | Integer |
| `agent_step` | Step number for this agent instance | Integer |
| `round_num` | Current round number | Integer |
| `subtask` | Subtask assigned by HostAgent | String |
| `subtask_index` | Index of subtask in current round | Integer |
| `action_type` | Type of action performed | String |
| `request` | Original user request | String |
| `agent_type` | Set to `AppAgent` | String |
| `agent_name` | Agent instance name | String |
| `application` | Application process name | String |
| `cost` | LLM cost for this step | Float |
| `result` | Execution results | String |
| `screenshot_clean` | Clean application screenshot path | String |
| `screenshot_annotated` | Annotated screenshot path | String |
| `screenshot_concat` | Concatenated screenshot path | String |
| `time_cost` | Time spent on each processing phase | Dictionary |

## Reading Step Logs

```python
import json

with open('logs/{task_name}/response.log', 'r') as f:
    for line in f:
        log = json.loads(line)
        print(f"Step {log['step']} - Agent: {log['agent_type']}")
        print(f"Thought: {log['thought']}")
```
