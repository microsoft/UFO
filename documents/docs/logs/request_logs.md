# Request Logs

The request is the prompt requests to the LLMs. The request log is stored in the `request.log` file. The request log contains the following information for each step:

| Field | Description |
| --- | --- |
| `step` | The step number of the session. |
| `prompt` | The prompt message sent to the LLMs. |

The request log is stored at the `debug` level. You can configure the logging level in the `LOG_LEVEL` field in the `config_dev.yaml` file.

!!! tip
    You can use the following python code to read the request log:

        import json

        with open('logs/{task_name}/request.log', 'r') as f:
            for line in f:
                log = json.loads(line)
    