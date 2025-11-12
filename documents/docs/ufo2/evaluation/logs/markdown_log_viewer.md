# Markdown Log Viewer

UFO provides a Markdown-formatted log viewer that consolidates all execution data into a readable, structured document. This format is ideal for debugging, analysis, and documentation.

## Configuration

Enable Markdown log generation in `config_dev.yaml`:

```yaml
LOG_TO_MARKDOWN: true
```

## Output

**File location:** `logs/{task_name}/output.md`

The generated Markdown file includes:

- Session overview and metadata
- Step-by-step execution timeline
- Agent responses and reasoning
- Screenshots embedded inline
- Evaluation results

## Use Cases

**Debugging:** Quickly trace through execution flow with visual context

**Documentation:** Share execution logs with human-readable formatting

**Analysis:** Review agent decision-making process with screenshots

**Reporting:** Generate execution reports for evaluation or review

## Implementation

The Markdown log is automatically generated at session end by the `Trajectory` class (located in `ufo/trajectory/parser.py`), which parses `response.log` and combines it with screenshots and other artifacts.
