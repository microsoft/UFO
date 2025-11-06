# Evaluation Logs

The evaluation logs store the evaluation results from the `EvaluationAgent`. The evaluation log contains the following information:

| Field | Description | Type |
| --- | --- | --- |
| Reason | The detailed reason for your judgment, by observing the screenshot differences and the <Execution Trajectory>. | String |
| Sub-score | The sub-score of the evaluation in decomposing the evaluation into multiple sub-goals. | List of Dictionaries |
| Complete | The completion status of the evaluation, can be `yes`, `no`, or `unsure`. | String |
| level | The level of the evaluation. | String |
| request | The request sent to the `EvaluationAgent`. | Dictionary |
| id | The ID of the evaluation. | Integer |


