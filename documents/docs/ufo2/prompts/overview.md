# Prompts

All prompts used in UFO are stored in the `ufo/prompts` directory. The folder structure is as follows:

```bash
📦prompts
 ┣ 📂demonstration       # Stores prompts for summarizing demonstrations from humans using Step Recorder
 ┣ 📂evaluation          # Stores prompts for the EvaluationAgent
 ┣ 📂examples            # Stores demonstration examples for in-context learning
   ┣ 📂nonvisual        # Examples for non-visual LLMs
   ┗ 📂visual           # Examples for visual LLMs
 ┣ 📂experience          # Stores prompts for summarizing the agent's self-experience
 ┣ 📂share               # Stores shared prompts
   ┗ 📂base             # Basic version of shared prompts
     ┣ 📜api.yaml       # Basic API prompt
     ┣ 📜app_agent.yaml # Basic AppAgent prompt template
     ┗ 📜host_agent.yaml # Basic HostAgent prompt template
 ┗ 📂third_party         # Stores prompts for third-party integrations (e.g., Linux agents)
```

!!! note
    The `nonvisual` and `visual` folders contain examples for non-visual and visual LLMs, respectively. Visual LLMs can process screenshots while non-visual LLMs rely on text-only control information.

## Agent Prompts

Prompts used by an agent usually contain the following information:

| Prompt Component | Description | Source |
| --- | --- | --- |
| `Basic template` | A basic template for the agent prompt with system and user roles | YAML files in `share/base/` |
| `API` | Documentation for all skills and APIs available to the agent | Dynamically generated from MCP tools |
| `Examples` | Demonstration examples for in-context learning | YAML files in `examples/visual/` or `examples/nonvisual/` |

You can find these prompts in the `share` directory.

## How Prompts Are Constructed

The agent's **Prompter** class is responsible for:

1. **Loading** YAML templates from the file system
2. **Formatting** API documentation from available tools
3. **Selecting** appropriate examples based on model type (visual/nonvisual)
4. **Combining** all components into a structured message list for the LLM
5. **Injecting** runtime context (observations, screenshots, retrieved knowledge)

Each agent type has its own specialized Prompter:

- **HostAgentPrompter**: Desktop-level orchestration with third-party agent support
- **AppAgentPrompter**: Application-level interactions with multi-action capabilities
- **EvaluationAgentPrompter**: Task evaluation and success assessment

!!! tip
    All information is constructed using the agent's `Prompter` class. You can find more details about the `Prompter` class architecture, template loading, and prompt construction workflow in the [Prompter documentation](../../infrastructure/agents/design/prompter.md).


