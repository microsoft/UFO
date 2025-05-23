# Example Prompts

The example prompts are used to generate textual demonstration examples for in-context learning. The examples are stored in the `ufo/prompts/examples` directory, with the following subdirectories:

| Directory | Description |
| --- | --- |
| `lite` | Lite version of demonstration examples |
| `non-visual` | Examples for non-visual LLMs |
| `visual` | Examples for visual LLMs |

!!!info
  You can configure the example prompt used in the `config.yaml` file. You can find more information about the configuration file [here](../configurations/developer_configuration.md).


## Example Prompts

Below are examples for the `HostAgent` and `AppAgent`:

- **HostAgent**:

```yaml
Request: |-
    Summarize and add all to do items on Microsoft To Do from the meeting notes email, and write a summary on the meeting_notes.docx.
Response:
    Observation: |-
        The current screenshot shows the Microsoft To Do application is visible, and outlook application and the meeting_notes.docx are available in the list of applications.
    Thought: |-
        The user request can be decomposed into three sub-tasks: (1) Summarize all to do items on Microsoft To Do from the meeting_notes email, (2) Add all to do items to Microsoft To Do, and (3) Write a summary on the meeting_notes.docx. I need to open the Microsoft To Do application to complete the first two sub-tasks.
        Each sub-task will be completed in individual applications sequentially.
    CurrentSubtask: |-
        Summarized all to do items from the meeting notes email in Outlook.
    Message:
        - (1) You need to first search for the meeting notes email in Outlook to summarize.
        - (2) Only summarize the to do items from the meeting notes email, without any redundant information.
    ControlLabel: |-
        16
    ControlText: |-
        Mail - Outlook - Jim
    Status: |-
        CONTINUE
    Plan:
        - Add all to do items previously summarized from the meeting notes email to one-by-one Microsoft To Do.
        - Write a summary about the meeting notes email on the meeting_notes.docx.
    Comment: |-
        I plan to first summarize all to do items from the meeting notes email in Outlook.
    Questions: []
```

- **AppAgent**:

```yaml
Request: |-
    How many stars does the Imdiffusion repo have?
Sub-task: |-
    Google search for the Imdiffusion repo on github and summarize the number of stars the Imdiffusion repo page visually.
Response: 
    Observation: |-
      I observe that the Edge browser is visible in the screenshot, with the Google search page opened.
    Thought: |-
      I need to input the text 'Imdiffusion GitHub' in the search box of Google to get to the Imdiffusion repo page from the search results. The search box is usually in a type of ComboBox.
    ControlLabel: |-
      36
    ControlText: |-
      搜索
    Function: |-
      set_edit_text
    Args: 
      {"text": "Imdiffusion GitHub"}
    Status: |-
      CONTINUE
    Plan:
      - (1) After input 'Imdiffusion GitHub', click Google Search to search for the Imdiffusion repo on github.
      - (2) Once the searched results are visible, click the Imdiffusion repo Hyperlink in the searched results to open the repo page.
      - (3) Observing and summarize the number of stars the Imdiffusion repo page, and reply to the user request.
    Comment: |-
      I plan to use Google search for the Imdiffusion repo on github and summarize the number of stars the Imdiffusion repo page visually.
    SaveScreenshot:
      {"save": false, "reason": ""}
Tips: |-
    - The search box is usually in a type of ComboBox.
    - The number of stars of a Github repo page can be found in the repo page visually.
```

These examples regulate the output format of the agent's response and provide a structured way to generate demonstration examples for in-context learning. 