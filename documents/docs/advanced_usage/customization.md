# Customization

Sometimes, UFO may need additional context or information to complete a task. These information are important and customized for each user. UFO can ask the user for additional information and save it in the local memory for future reference. This customization feature allows UFO to provide a more personalized experience to the user.

## Scenario

Let's consider a scenario where UFO needs additional information to complete a task. UFO is tasked with booking a cab for the user. To book a cab, UFO needs to know the exact address of the user. UFO will ask the user for the address and save it in the local memory for future reference. Next time, when UFO is asked to complete a task that requires the user's address, UFO will use the saved address to complete the task, without asking the user again.


## Implementation
We currently implement the customization feature in the `HostAgent` class. When the `HostAgent` needs additional information, it will transit to the `PENDING` state and ask the user for the information. The user will provide the information, and the `HostAgent` will save it in the local memory base for future reference. The saved information is stored in the `blackboard` and can be accessed by all agents in the session.

!!! note
    The customization memory base is only saved in a **local file**. These information will **not** upload to the cloud or any other storage to protect the user's privacy.

## Configuration

You can configure the customization feature by setting the following field in the `config_dev.yaml` file.

| Configuration Option   | Description                                  | Type    | Default Value                         |
|------------------------|----------------------------------------------|---------|---------------------------------------|
| `USE_CUSTOMIZATION`    | Whether to enable the customization.         | Boolean | True                                  |
| `QA_PAIR_FILE`         | The path for the historical QA pairs.        | String  | "customization/historical_qa.txt"     |
| `QA_PAIR_NUM`          | The number of QA pairs for the customization.| Integer | 20                                    |
