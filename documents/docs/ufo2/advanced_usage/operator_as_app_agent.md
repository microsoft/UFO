# Operator as an AppAgent

UFO² supports wrapping third-party agents as AppAgents, enabling them to be orchestrated by the HostAgent in multi-agent workflows. This guide demonstrates how to run **Operator**, an OpenAI-based Conversational UI Agent (CUA), within the UFO² ecosystem.

![Operator Integration](../../img/everything.png)

## Prerequisites

Before proceeding, ensure that Operator has been properly configured. Follow the setup instructions in the [OpenAI CUA (Operator) guide](../../configuration/models/operator.md).

## Running the Operator

UFO² provides two modes for running Operator:

1. **Single Agent Mode (`operator`)** — Run Operator independently through UFO² as a launcher
2. **AppAgent Mode (`normal_operator`)** — Run Operator as an `AppAgent` orchestrated by the `HostAgent`

### Single Agent Mode

In single agent mode, Operator functions independently but is launched through UFO². This mode is useful for debugging or quick prototyping.

```powershell
python -m ufo --mode operator --task <your_task_name> --request <your_request>
```

**Example:**
```powershell
python -m ufo --mode operator --task test_operator --request "Open Notepad and type Hello World"
```

### AppAgent Mode

In AppAgent mode, Operator is wrapped as an `AppAgent` and can be triggered as a sub-agent within the HostAgent workflow. This enables task decomposition where the HostAgent coordinates multiple agents including Operator.

```powershell
python -m ufo --mode normal_operator --task <your_task_name> --request <your_request>
```

**Example:**
```powershell
python -m ufo --mode normal_operator --task test_integration --request "Search for Python documentation and open the first result"
```

## Logs

In both modes, execution logs are saved in:

```
logs/<your_task_name>/
```

These logs follow the same structure and conventions as other UFO² sessions.