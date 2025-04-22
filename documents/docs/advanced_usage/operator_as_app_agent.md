# Operator as an AppAgent

UFO² supports **wrapping any third-party agent as an AppAgent**, allowing it to be invoked by the HostAgent within a multi-agent workflow. This section demonstrates how to run **Operator**, an OpenAI-based Conversational UI Agent (CUA), as an AppAgent inside the UFO² ecosystem.

<div align="center">
    <img src="../../img/everything.png" alt="Speculative Multi-Action Execution" />
</div>

<br><br>

## 📦 Prerequisites

Before proceeding, please ensure that the Operator has been properly configured. You can follow the setup instructions in the [OpenAI CUA (Operator) guide](../supported_models/operator.md).

## 🚀 Running the Operator

UFO² provides two modes for running the Operator:

1. **Single Agent Mode** — Use UFO² as the launcher to run Operator in standalone mode.
2. **AppAgent Mode** — Run Operator as an `AppAgent`, enabling it to be orchestrated by the `HostAgent` as part of a broader task decomposition.

### 🔹 Single Agent Mode

In this mode, the Operator functions independently but is launched through UFO². This is useful for debugging or quick prototyping.

```powershell
python -m ufo -m operator -t <your_task_name> -r <your_request>
```

### 🔸 AppAgent Mode

This mode wraps Operator as an AppAgent (`normal_operator`) so that it can be triggered as a sub-agent within a full HostAgent workflow.

```powershell
python -m ufo -m normal_operator -t <your_task_name> -r <your_request>
```

## 📝 Logs

In both modes, execution logs will be saved in the following directory:

```
logs/<your_task_name>/
```

These logs follow the same structure and conventions as previous UFO² sessions.