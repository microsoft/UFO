# Follower Agent 🚶🏽‍♂️

The `FollowerAgent` is inherited from the `AppAgent` and is responsible for following the user's instructions to perform specific tasks within the application. The `FollowerAgent` is designed to execute a series of actions based on the user's guidance. It is particularly useful for software testing, when clear instructions are provided to validate the application's behavior.


## Different from the AppAgent
The `FollowerAgent` shares most of the functionalities with the `AppAgent`, but it is designed to follow the step-by-step instructions provided by the user, instead of does its own reasoning to determine the next action. 


## Usage
The `FollowerAgent` is available in `follower` mode. You can find more details in the [documentation]().  It also uses differnt `Session` and `Processor` to handle the user's instructions. The step-wise instructions are provided by the user in the in a json file, which is then parsed by the `FollowerAgent` to execute the actions. An example of the json file is shown below:

```json
{
    "task": "Type in a bold text of 'Test For Fun'",
    "steps": 
    [
        "1.type in 'Test For Fun'",
        "2.select the text of 'Test For Fun'",
        "3.click on the bold"
    ],
    "object": "draft.docx"
}
```

# Reference

:::agents.agent.follower_agent.FollowerAgent