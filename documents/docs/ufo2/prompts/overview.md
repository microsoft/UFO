# Prompts

All prompts used in UFO are stored in the `ufo/prompts` directory. The folder structure is as follows:

```
📦prompts
 ┣ 📂demonstration       # Prompts for summarizing human demonstrations
 ┣ 📂evaluation          # Prompts for the EvaluationAgent
 ┣ 📂examples            # Demonstration examples for in-context learning
   ┣ 📂nonvisual        # Examples for non-visual LLMs
   ┗ 📂visual           # Examples for visual LLMs
 ┣ 📂experience          # Prompts for summarizing agent self-experience
 ┣ 📂share               # Shared prompt templates
   ┗ 📂base             # Basic version of shared prompts
     ┣ 📜api.yaml       # Basic API prompt
     ┣ 📜app_agent.yaml # Basic AppAgent prompt template
     ┗ 📜host_agent.yaml # Basic HostAgent prompt template
 ┗ 📂third_party         # Third-party integration prompts (e.g., Linux agents)
```

Visual LLMs can process screenshots while non-visual LLMs rely on text-only control information.

## Agent Prompts

Agent prompts are constructed from the following components:

| Component | Description | Source |
| --- | --- | --- |
| **Basic Template** | Base template with system and user roles | YAML files in `share/base/` |
| **API Documentation** | Skills and APIs available to the agent | Dynamically generated from MCP tools |
| **Examples** | In-context learning demonstrations | YAML files in `examples/visual/` or `examples/nonvisual/` |

You can find the base templates in the `share/base` directory.

## How Prompts Are Constructed

The agent's `Prompter` class is responsible for:

1. **Loading** YAML templates from the file system
2. **Formatting** API documentation from available tools
3. **Selecting** appropriate examples based on model type (visual/nonvisual)
4. **Combining** all components into a structured message list for the LLM
5. **Injecting** runtime context (observations, screenshots, retrieved knowledge)

Each agent type has its own specialized Prompter:

- **HostAgentPrompter**: Desktop-level orchestration with third-party agent support
- **AppAgentPrompter**: Application-level interactions with multi-action capabilities
- **EvaluationAgentPrompter**: Task evaluation and success assessment

For comprehensive details about the Prompter class architecture, template loading, and prompt construction workflow, see the [Prompter documentation](../../infrastructure/agents/design/prompter.md).


