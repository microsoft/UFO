# EvaluationAgent 🧐

The objective of the `EvaluationAgent` is to evaluate whether a `Session` or `Round` has been successfully completed. The `EvaluationAgent` assesses the performance of the `HostAgent` and `AppAgent` in fulfilling the request. You can configure whether to enable the `EvaluationAgent` in the `config_dev.yaml` file and the detailed documentation can be found [here](../configurations/developer_configuration.md).
!!! note
    The `EvaluationAgent` is fully LLM-driven and conducts evaluations based on the action trajectories and screenshots. It may not by 100% accurate since LLM may make mistakes.


We illustrate the evaluation process in the following figure:
<h1 align="center">
    <img src="../../img/evaluator.png " alt="Evaluation Agent Image" width="60%">
</h1>

## Configuration
To enable the `EvaluationAgent`, you can configure the following parameters in the `config_dev.yaml` file to evaluate the task completion status at different levels:

| Configuration Option      | Description                                   | Type    | Default Value |
|---------------------------|-----------------------------------------------|---------|---------------|
| `EVA_SESSION`             | Whether to include the session in the evaluation. | Boolean | True          |
| `EVA_ROUND`               | Whether to include the round in the evaluation.   | Boolean | False         |
| `EVA_ALL_SCREENSHOTS`     | Whether to include all the screenshots in the evaluation. | Boolean | True          |


## Evaluation Inputs
The `EvaluationAgent` takes the following inputs for evaluation:

| Input | Description | Type |
| --- | --- | --- |
| User Request | The user's request to be evaluated. | String |
| APIs Description | The description of the APIs used in the execution. | List of Strings |
| Action Trajectories | The action trajectories executed by the `HostAgent` and `AppAgent`. | List of Strings |
| Screenshots | The screenshots captured during the execution. | List of Images |

For more details on how to construct the inputs, please refer to the `EvaluationAgentPrompter` class in `ufo/prompter/eva_prompter.py`.

!!! tip
    You can configure whether to use all screenshots or only the first and last screenshot for evaluation in the `EVA_ALL_SCREENSHOTS` of the `config_dev.yaml` file.


## Evaluation Outputs
The `EvaluationAgent` generates the following outputs after evaluation:

| Output | Description | Type |
| --- | --- | --- |
| reason | The detailed reason for your judgment, by observing the screenshot differences and the <Execution Trajectory>. | String |
| sub_scores | The sub-score of the evaluation in decomposing the evaluation into multiple sub-goals. | List of Dictionaries |
| complete | The completion status of the evaluation, can be `yes`, `no`, or `unsure`. | String |

Below is an example of the evaluation output:

```json
{
    "reason": "The agent successfully completed the task of sending 'hello' to Zac on Microsoft Teams. 
    The initial screenshot shows the Microsoft Teams application with the chat window of Chaoyun Zhang open. 
    The agent then focused on the chat window, input the message 'hello', and clicked the Send button. 
    The final screenshot confirms that the message 'hello' was sent to Zac.", 
    "sub_scores": {
        "correct application focus": "yes", 
        "correct message input": "yes", 
        "message sent successfully": "yes"
        }, 
    "complete": "yes"}
```

!!!info
    The log of the evaluation results will be saved in the `logs/{task_name}/evaluation.log` file.

The `EvaluationAgent` employs the CoT mechanism to first decompose the evaluation into multiple sub-goals and then evaluate each sub-goal separately. The sub-scores are then aggregated to determine the overall completion status of the evaluation.

# Reference

:::agents.agent.evaluation_agent.EvaluationAgent

