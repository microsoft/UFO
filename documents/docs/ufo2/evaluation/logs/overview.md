# UFO Logs

UFO generates comprehensive logs for debugging, analysis, and evaluation. Understanding these logs is essential for diagnosing issues and improving agent performance.

## Log Types

| Log Type | Description | Location |
| --- | --- | --- |
| [Request Log](./request_logs.md) | LLM prompt requests at each step | `logs/{task_name}/request.log` |
| [Step Log](./step_logs.md) | Agent responses and execution details | `logs/{task_name}/response.log` |
| [Evaluation Log](./evaluation_logs.md) | Task evaluation results | `logs/{task_name}/evaluation.log` |
| [Screenshots](./screenshots_logs.md) | UI screenshots and visual captures | `logs/{task_name}/` |
| [UI Tree](./ui_tree_logs.md) | Application UI structure data | `logs/{task_name}/ui_tree/` |

All logs are stored in the `logs/{task_name}` directory, where `{task_name}` is auto-generated based on timestamp.