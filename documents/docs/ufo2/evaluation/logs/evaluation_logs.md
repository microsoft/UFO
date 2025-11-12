# Evaluation Logs

The evaluation log stores task completion assessment results from the `EvaluationAgent`. The log is saved as `evaluation.log` in JSON format, containing a single entry that evaluates the entire session.

## Log Structure

The evaluation log contains the following fields:

| Field | Description | Type |
| --- | --- | --- |
| `complete` | Overall completion status: `yes`, `no`, or `unsure` | String |
| `sub_scores` | Breakdown of evaluation into sub-goals, each with name and evaluation status | List of Dictionaries |
| `reason` | Detailed justification based on screenshots and execution trajectory | String |
| `level` | Evaluation scope (e.g., `session`) | String |
| `request` | Original user request being evaluated | String |
| `type` | Log entry type, set to `evaluation_result` | String |

## Sub-score Structure

Each item in `sub_scores` contains:

| Field | Description | Type |
| --- | --- | --- |
| `name` | Name of the sub-goal being evaluated | String |
| `evaluation` | Completion status: `yes`, `no`, or `unsure` | String |

## Example

```json
{
    "complete": "yes",
    "sub_scores": [
        {
            "name": "Open application",
            "evaluation": "yes"
        },
        {
            "name": "Complete data entry",
            "evaluation": "yes"
        }
    ],
    "reason": "All sub-tasks completed successfully. Screenshots show the application was opened and data was correctly entered.",
    "level": "session",
    "request": "Open the application and enter data",
    "type": "evaluation_result"
}


