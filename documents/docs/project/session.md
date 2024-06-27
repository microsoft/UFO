# Session

A `Session` is a conversation instance between the user and UFO. It is a continuous interaction that starts when the user initiates a request and ends when the request is completed. UFO supports multiple requests within the same session. Each request is processed sequentially, by a `Round` of interaction, until the user's request is fulfilled.

## Session Lifecycle

The lifecycle of a `Session` is as follows:

### 1. Session Initialization

A `Session` is initialized when the user starts a conversation with UFO. The `Session` object is created, and the first `Round` of interaction is initiated. At this stage, the user's request is processed by the `HostAgent` to determine the appropriate application to fulfill the request. The `Context` object is created to store the state of the conversation shared across all `Rounds` within the `Session`.

### 2. Round Processing

Once the `Session` is initialized, the `Round` of interaction begins, which completes a single user request by orchestrating the `HostAgent` and `AppAgent`. 


### 3. Next Round

After the completion of the first `Round`, the `Session` requests the next request from the user to start the next `Round` of interaction. This process continues until there are no more requests from the user.

### 4. Session Termination
If the user has no more requests or decides to end the conversation, the `Session` is terminated, and the conversation ends. The `EvaluationAgent` evaluates the completeness of the `Session` if it is configured to do so.


## Reference

::: module.basic.BaseSession