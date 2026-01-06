# Customization

UFO can ask users for additional context or information when needed and save it in local memory for future reference. This customization feature enables a more personalized user experience by remembering user-specific information across sessions.

## Example Scenario

Consider a task where UFO needs to book a cab. To complete this task, UFO requires the user's address. UFO will:

1. Ask the user for their address
2. Save the address in local memory
3. Use the saved address automatically in future tasks that require it

This eliminates the need to repeatedly provide the same information.

## How It Works

The customization feature is implemented across multiple agent types (`HostAgent`, `AppAgent`, and `OpenAIOperatorAgent`). When an agent needs additional information:

1. The agent transitions to the `PENDING` state
2. The agent asks the user for the required information (if `ASK_QUESTION` is enabled)
3. The user's response is saved to the `blackboard` in the QA pairs file
4. All agents in the session can access this information from the shared `blackboard`

The saved QA pairs are stored locally as JSON lines in the file specified by `QA_PAIR_FILE`. Privacy is preserved as this information never leaves the local machine.

## Configuration

Configure the customization feature in `config/ufo/system.yaml`:

| Configuration Option   | Description                                                      | Type    | Default Value                         |
|------------------------|------------------------------------------------------------------|---------|---------------------------------------|
| `ASK_QUESTION`         | Whether to allow agents to ask users questions                   | Boolean | False                                 |
| `USE_CUSTOMIZATION`    | Whether to load and use saved QA pairs from previous sessions    | Boolean | False                                 |
| `QA_PAIR_FILE`         | Path to the file storing historical QA pairs                     | String  | "customization/global_memory.jsonl"   |
| `QA_PAIR_NUM`          | Maximum number of recent QA pairs to load into memory            | Integer | 20                                    |

**Note:** Both `ASK_QUESTION` and `USE_CUSTOMIZATION` need to be enabled for the full customization experience. `ASK_QUESTION` controls whether agents can prompt users for information, while `USE_CUSTOMIZATION` controls whether previously saved information is loaded.
