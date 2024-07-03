# Round

A `Round` is a single interaction between the user and UFO that processes a single user request. A `Round` is responsible for orchestrating the `HostAgent` and `AppAgent` to fulfill the user's request.


## Round Lifecycle

In a `Round`, the following steps are executed:

### 1. Round Initialization
At the beginning of a `Round`, the `Round` object is created, and the user's request is processed by the `HostAgent` to determine the appropriate application to fulfill the request.

### 2. Action Execution
Once created, the `Round` orchestrates the `HostAgent` and `AppAgent` to execute the necessary actions to fulfill the user's request. The core logic of a `Round` is shown below:

```python
def run(self) -> None:
    """
    Run the round.
    """

    while not self.is_finished():

        self.agent.handle(self.context)

        self.state = self.agent.state.next_state(self.agent)
        self.agent = self.agent.state.next_agent(self.agent)
        self.agent.set_state(self.state)

        # If the subtask ends, capture the last snapshot of the application.
        if self.state.is_subtask_end():
            time.sleep(configs["SLEEP_TIME"])
            self.capture_last_snapshot(sub_round_id=self.subtask_amount)
            self.subtask_amount += 1

    self.agent.blackboard.add_requests(
        {"request_{i}".format(i=self.id), self.request}
    )

    if self.application_window is not None:
        self.capture_last_snapshot()

    if self._should_evaluate:
        self.evaluation()
```

At each step, the `Round` processes the user's request by invoking the `handle` method of the `AppAgent` or `HostAgent` based on the current state. The state determines the next agent to handle the request and the next state to transition to.

### 3. Request Completion
The `AppAgent` completes the actions within the application. If the request spans multiple applications, the `HostAgent` may switch to a different application to continue the task.

### 4. Round Termination
Once the user's request is fulfilled, the `Round` is terminated, and the results are returned to the user. If configured, the `EvaluationAgent` evaluates the completeness of the `Round`.


# Reference

::: module.basic.BaseRound