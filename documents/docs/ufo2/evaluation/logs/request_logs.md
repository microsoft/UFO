# Request Logs

The request log stores all prompt messages sent to LLMs during execution. Each line is a JSON entry representing one LLM request at a specific step.

## Location

```
logs/{task_name}/request.log
```

## Log Fields

| Field | Description | Type |
| --- | --- | --- |
| `step` | Step number in the session | Integer |
| `prompt` | Complete prompt message sent to the LLM | Dictionary/List |

## Reading Request Logs

```python
import json

with open('logs/{task_name}/request.log', 'r') as f:
    for line in f:
        log = json.loads(line)
        print(f"Step {log['step']}: {log['prompt']}")
```

The request log is useful for:

- Debugging LLM interactions
- Understanding what context was provided at each step
- Analyzing prompt effectiveness
- Reproducing agent behavior
    