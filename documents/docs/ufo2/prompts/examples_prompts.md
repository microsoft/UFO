# Example Prompts

The example prompts are used to generate textual demonstration examples for in-context learning. The examples are stored in the `ufo/prompts/examples` directory, with the following subdirectories:

| Directory | Description |
| --- | --- |
| `nonvisual` | Examples for non-visual LLMs |
| `visual` | Examples for visual LLMs |

!!!info
  You can configure the example prompt used in the configuration files. You can find more information about the configuration file [here](../../configuration/system/field_reference.md).

## How Examples Are Used

Example prompts serve as **in-context learning demonstrations** that help the LLM understand the expected output format and reasoning process. The agent's `Prompter` class:

1. Loads examples from YAML files based on the model type (visual/nonvisual)
2. Formats them into the system prompt using `examples_prompt_helper()`
3. Combines them with API documentation and base instructions

!!! tip
    See [Prompter documentation](../../infrastructure/agents/design/prompter.md) for details on how examples are loaded and formatted into the final prompt.


## Example Prompts

Below are examples for the `HostAgent` and `AppAgent`:

- **HostAgent**:

```yaml
Request: |-
    Summarize and add all to do items on Microsoft To Do from the meeting notes email, and write a summary on the meeting_notes.docx.
Response:
    observation: |-
        The current screenshot shows the Microsoft To Do application is visible, and outlook application and the meeting_notes.docx are available in the list of applications.
    thought: |-
        The user request can be decomposed into three sub-tasks: (1) Summarize all to do items on Microsoft To Do from the meeting_notes email, (2) Add all to do items to Microsoft To Do, and (3) Write a summary on the meeting_notes.docx. I need to open the Microsoft To Do application to complete the first two sub-tasks.
        Each sub-task will be completed in individual applications sequentially.
    current_subtask: |-
        Summarized all to do items from the meeting notes email in Outlook.
    message:
        - (1) You need to first search for the meeting notes email in Outlook to summarize.
        - (2) Only summarize the to do items from the meeting notes email, without any redundant information.
    status: |-
        ASSIGN
    plan:
        - Add all to do items previously summarized from the meeting notes email to one-by-one Microsoft To Do.
        - Write a summary about the meeting notes email on the meeting_notes.docx.
    function: select_application_window
    arguments:
        id: "16"
        name: "Mail - Outlook - Jim"
    comment: |-
        I plan to first summarize all to do items from the meeting notes email in Outlook.
    questions: []
    result: |-
        User request in ASSIGN state. Phase 1 defined: within Outlook window 'Mail - Outlook - Jim' (id:16) locate the meeting notes email and extract actionable to-do items. No search or extraction executed yet. Planned phases: (1) extract to-dos; (2) add each item to Microsoft To Do; (3) write overall summary into meeting_notes.docx. No extracted items or artifacts yet.
```

- **AppAgent**:

```yaml
Request: |-
    How many stars does the Imdiffusion repo have?
Sub-task: |-
    Google search for the Imdiffusion repo on github and summarize the number of stars the Imdiffusion repo page visually.
Response: 
    observation: |-
      I observe that the Edge browser is visible in the screenshot, with the Google search page opened.
    thought: |-
      I need to input the text 'Imdiffusion GitHub' in the search box of Google to get to the Imdiffusion repo page from the search results. The search box is usually in a type of ComboBox.
    action:
      function: |-
        set_edit_text
      arguments:
        id: "36"
        name: "搜索"
        text: "Imdiffusion GitHub"
      status: |-
        CONTINUE
    plan:
      - (1) After input 'Imdiffusion GitHub', click Google Search to search for the Imdiffusion repo on github.
      - (2) Once the searched results are visible, click the Imdiffusion repo Hyperlink in the searched results to open the repo page.
      - (3) Observing and summarize the number of stars the Imdiffusion repo page, and reply to the user request.
    comment: |-
      I plan to use Google search for the Imdiffusion repo on github and summarize the number of stars the Imdiffusion repo page visually.
    save_screenshot:
      {"save": false, "reason": ""}
Tips: |-
    - The search box is usually in a type of ComboBox.
    - The number of stars of a Github repo page can be found in the repo page visually.
```

These examples regulate the output format of the agent's response and provide a structured way to generate demonstration examples for in-context learning.

## Related Documentation

- **[Prompter Design](../../infrastructure/agents/design/prompter.md)** - Learn how examples are loaded and formatted
- **[Basic Template](./basic_template.md)** - Understand the YAML template structure
- **[Configuration Reference](../../configuration/system/field_reference.md)** - Configure which examples to use 