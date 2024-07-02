# Prompts

All prompts used in UFO are stored in the `ufo/prompts` directory. The folder structure is as follows:

```bash
📦prompts
 ┣ 📂apps                # Stores API prompts for specific applications
   ┣ 📂excel            # Stores API prompts for Excel
   ┣ 📂word             # Stores API prompts for Word
   ┗ ...
 ┣ 📂demonstration       # Stores prompts for summarizing demonstrations from humans using Step Recorder
 ┣ 📂experience          # Stores prompts for summarizing the agent's self-experience
 ┣ 📂evaluation          # Stores prompts for the EvaluationAgent
 ┣ 📂examples            # Stores demonstration examples for in-context learning
   ┣ 📂lite             # Lite version of demonstration examples
   ┣ 📂non-visual       # Examples for non-visual LLMs
   ┗ 📂visual           # Examples for visual LLMs
 ┗ 📂share               # Stores shared prompts
   ┣ 📂lite             # Lite version of shared prompts
   ┗ 📂base             # Basic version of shared prompts
     ┣ 📜api.yaml       # Basic API prompt
     ┣ 📜app_agent.yaml # Basic AppAgent prompt template
     ┗ 📜host_agent.yaml # Basic HostAgent prompt template
```

!!! note
    The `lite` version of prompts is a simplified version of the full prompts, which is used for LLMs that have a limited token budget. However, the `lite` version is not fully optimized and may lead to **suboptimal** performance.

!!! note
    The `non-visual` and `visual` folders contain examples for non-visual and visual LLMs, respectively.

## Agent Prompts

Prompts used an agent usually contain the following information:

| Prompt | Description |
| --- | --- |
| `Basic template` | A basic template for the agent prompt. |
| `API` | A prompt for all skills and APIs used by the agent. |
| `Examples` | Demonstration examples for the agent for in-context learning. |

You can find these prompts `share` directory. The prompts for specific applications are stored in the `apps` directory.


!!! tip
    All information is constructed using the agent's `Prompter` class. You can find more details about the `Prompter` class in the documentation [here](../agents/design/prompter.md).


