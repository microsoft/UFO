# EvaluationAgent 🧐

The objective of the `EvaluationAgent` is to evaluate whether a `Session` or `Round` has been successfully completed. The `EvaluationAgent` assesses the performance of the `HostAgent` and `AppAgent` in fulfilling the request. You can configure whether to enable the `EvaluationAgent` in the `config_dev.yaml` file and the detailed documentation can be found [here](../configurations/developer_configuration.md).
!!! note
    The `EvaluationAgent` is fully LLM-driven and conducts evaluations based on the action trajectories and screenshots. It may not by 100% accurate since LLM may make mistakes.


## Evaluation Inputs
The `EvaluationAgent` takes the following inputs for evaluation:

| Input | Description | Type |
| --- | --- | --- |
| User Request | The user's request to be evaluated. | String |
| APIs Description | The description of the APIs used in the execution. | List of Strings |
| Action Trajectories | The action trajectories executed by the `HostAgent` and `AppAgent`. | List of Strings |
| Screenshots | The screenshots captured during the execution. | List of Images |

!!! tip
    You can configure whether to use all screenshots or only the first and last screenshot for evaluation in the `config_dev.yaml` file.

## Evaluation Outputs
The `EvaluationAgent` generates the following outputs after evaluation:

| Output | Description | Type |
| --- | --- | --- |
| Reason | The detailed reason for your judgment, by observing the screenshot differences and the <Execution Trajectory>. | String |
| Sub-score | The sub-score of the evaluation in decomposing the evaluation into multiple sub-goals. | List of Dictionaries |
| Complete | The completion status of the evaluation, can be `yes`, `no`, or `unsure`. | String |

The `EvaluationAgent` employs the CoT mechanism to first decompose the evaluation into multiple sub-goals and then evaluate each sub-goal separately. The sub-scores are then aggregated to determine the overall completion status of the evaluation.

# Reference

:::agents.agent.evaluation_agent.EvaluationAgent

