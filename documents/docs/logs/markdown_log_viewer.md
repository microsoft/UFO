# Markdown-Formatted Log Viewer

We provide a Markdown-formatted log viewer for better readability and organization of logs for debugging and analysis. The Markdown log viewer is designed to display logs in a structured format, making it easier to identify issues and understand the flow of the application.

## Configuration
To enable the Markdown log viewer, you need to set the `LOG_TO_MARKDOWN` option in the `config_dev.yaml` file to `True`. Below is the detailed configuration in the `config_dev.yaml` file:

```yaml
LOG_TO_MARKDOWN: True # Whether to log to markdown format
```

After setting this option, the logs will be saved in a Markdown format in your `logs/<task_name>` directory. 

!!! tip
    We strongly recommend to turn on this option. The development team uses this option to debug the agent's behavior and improve the performance of the agent.
