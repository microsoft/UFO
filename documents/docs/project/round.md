# Round

A `Round` is a single interaction between the user and UFO that processes a single user request. A `Round` is responsible for orchestrating the `HostAgent` and `AppAgent` to fulfill the user's request.


## Round Lifecycle

In a `Round`, the following steps are executed:

### 1. Round Initialization
At the beginning of a `Round`, the `Round` object is created, and the user's request is processed by the `HostAgent` to determine the appropriate application to fulfill the request.

### 2. Action Execution
The `HostAgent` selects the appropriate application, and the `AppAgent` executes the necessary actions to fulfill the user's request within the application.

### 3. Request Completion
The `AppAgent` completes the actions within the application. If the request spans multiple applications, the `HostAgent` may switch to a different application to continue the task.

### 4. Round Termination
Once the user's request is fulfilled, the `Round` is terminated, and the results are returned to the user. If configured, the `EvaluationAgent` evaluates the completeness of the `Round`.


# Reference

::: module.basic.BaseRound