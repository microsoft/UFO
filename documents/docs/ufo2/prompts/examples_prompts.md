# Example Prompts

Example prompts provide demonstration examples for in-context learning. They are stored in the `ufo/prompts/examples` directory with the following subdirectories:

| Directory | Description |
| --- | --- |
| `nonvisual` | Examples for non-visual LLMs |
| `visual` | Examples for visual LLMs |

You can configure which example prompts to use in the system configuration files. See the [System Configuration Guide](../../configuration/system/system_config.md) for details.

## How Examples Are Used

Example prompts serve as in-context learning demonstrations that help the LLM understand the expected output format and reasoning process. The agent's `Prompter` class:

1. Loads examples from YAML files based on the model type (visual/nonvisual)
2. Formats them into the system prompt using `examples_prompt_helper()`
3. Combines them with API documentation and base instructions

See the [Prompter documentation](../../infrastructure/agents/design/prompter.md) for details on how examples are loaded and formatted into the final prompt.


## Example Structure

Below are examples for the `HostAgent` and `AppAgent`:

### HostAgent Example

```yaml
Request: |-
  My name is Zac. Please send a email to jack@outlook.com to thanks his contribution on the open source.
Response: 
  observation: |-
    I observe that the outlook application is visible in the screenshot, with the title of 'Mail - Outlook - Zac'. I can see a list of emails in the application.
  thought: |-
    The user request can be solely complete on the outlook application. I need to open the outlook application for the current sub-task. If successful, no further sub-tasks are needed.
  current_subtask: |- 
    Compose an email to send to Jack (jack@outlook.com) to thank him for his contribution to the open source project on the outlook application, using the name Zac.
  message:
    - (1) The name of the sender is Zac.
    - (2) The email composed should be detailed and professional.
  status: |-  
    ASSIGN
  plan: []
  function: select_application_window
  arguments:
    id: "12"
    name: "Mail - Outlook - Zac"
  comment: |-
    It is time to open the outlook application!
  questions: []
  result: |-
    User request in ASSIGN state. Target window 'Mail - Outlook - Zac' (id:12) identified; will call select_application_window to focus Outlook and begin composing.
```

### AppAgent Example

```yaml
Request: |-
  My name is Zac. Please send a email to jack@outlook.com to thanks his contribution on the open source.
Sub-task: |-
  Compose an email to send to Jack (jack@outlook.com) to thank him for his contribution to the open source project on the outlook application, using the name Zac.
Response: 
  observation: |-
    The screenshot shows that I am on the Main Page of Outlook. The Main Page has a list of control items and email received. The new email editing window is not opened.
  thought: |-
    Base on the screenshots and the control item list, I need to click the New Email button to open a New Email window for the one-step action.
  action:
    function: |-
      click_input
    arguments: 
      {"id": "1", "name": "New Email", "button": "left", "double": false}
    status: |-
      CONTINUE
  plan:
    - (1) Input the email address of the receiver.
    - (2) Input the title of the email.
    - (3) Input the content of the email.
    - (4) Click the Send button to send the email.
  comment: |-
    After I click the New Email button, the New Email window will be opened and available for composing the email.
  save_screenshot:
    {"save": false, "reason": ""}
  result: |-
    Successfully clicked the 'New Email' button in Outlook to initiate email composition.
Tips: 
  - Sending an email is a sensitive action that needs to be confirmed by the user before the execution.
  - You need to draft the content of the email and send it to the receiver.
```

These examples regulate the output format of the agent's response and provide a structured way to generate demonstration examples for in-context learning.

## Related Documentation

- **[Prompter Design](../../infrastructure/agents/design/prompter.md)** - Learn how examples are loaded and formatted
- **[Basic Template](./basic_template.md)** - Understand the YAML template structure
- **[System Configuration](../../configuration/system/system_config.md)** - Configure which examples to use 