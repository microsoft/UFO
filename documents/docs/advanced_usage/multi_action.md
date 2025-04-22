# Speculative Multi-Action Execution

UFO² introduces a new feature called **Speculative Multi-Action Execution**. This feature allows the agent to bundle several predicted steps into one LLM call, which are then validated live. This approach can lead to up to **51% fewer queries** compared to inferring each step separately. The agent will first predict a batch of likely actions and then validate them against the live UIA state in a single shot. We illustrate the speculative multi-action execution in the figure below:



<h1 align="center">
    <img src="../../img/multiaction.png" alt="Speculative Multi-Action Execution" />
</h1>

## Configuration
To activate the speculative multi-action execution, you need to set `ACTION_SEQUENCE` to `True` in the `config_dev.yaml` file.

```yaml
ACTION_SEQUENCE: True
```


# References
The implementation of the speculative multi-action execution is located in the `ufo/agents/processors/actions.py` file. The following classes are used for the speculative multi-action execution:

:::agents.processors.actions.OneStepAction
