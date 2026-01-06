# Learning from User Demonstration

For complex tasks, users can demonstrate the task execution process to help UFO learn effective action patterns. UFO uses Windows [Step Recorder](https://support.microsoft.com/en-us/windows/record-steps-to-reproduce-a-problem-46582a9b-620f-2e36-00c9-04e25d784e47) to capture user action trajectories, which are then processed and stored for future reference.

## Mechanism

UFO leverages the Windows Step Recorder tool to capture task demonstrations. The workflow operates as follows:

1. **Record**: User performs the task while Step Recorder captures the action sequence
2. **Process**: The `DemonstrationSummarizer` extracts and summarizes the recorded demonstration from the zip file
3. **Store**: Summarized demonstrations are saved to the configured demonstration database
4. **Retrieve**: When encountering similar tasks, the `DemonstrationRetriever` queries relevant demonstrations
5. **Apply**: Retrieved demonstrations guide the AppAgent's plan generation

See the [User Demonstration Provision](../../../tutorials/creating_app_agent/demonstration_provision.md) guide for detailed recording instructions.

**Demo Video:**

<iframe width="560" height="315" src="https://github.com/yunhao0204/UFO/assets/59384816/0146f83e-1b5e-4933-8985-fe3f24ec4777" frameborder="0" allowfullscreen></iframe>
## Configuration

To enable learning from user demonstrations:

1. **Provide Demonstrations**: Follow the [User Demonstration Provision](../../../tutorials/creating_app_agent/demonstration_provision.md) guide to record demonstrations

2. **Configure Parameters**: Set the following options in `config.yaml`:

| Configuration Option | Description | Type | Default |
|---------------------|-------------|------|---------|
| `RAG_DEMONSTRATION` | Enable demonstration-based learning | Boolean | `False` |
| `RAG_DEMONSTRATION_RETRIEVED_TOPK` | Number of top demonstrations to retrieve | Integer | `5` |
| `RAG_DEMONSTRATION_COMPLETION_N` | Number of completion choices for demonstration results | Integer | `3` |
| `DEMONSTRATION_SAVED_PATH` | Database path for storing demonstrations | String | `"vectordb/demonstration/"` |

For more details on RAG configuration, see the [RAG Configuration Guide](../../../configuration/system/rag_config.md).

## API Reference

### Demonstration Summarizer

The `DemonstrationSummarizer` class in `record_processor/summarizer/summarizer.py` handles demonstration summarization:

:::summarizer.summarizer.DemonstrationSummarizer

### Demonstration Retriever

The `DemonstrationRetriever` class in `ufo/rag/retriever.py` handles demonstration retrieval:

:::rag.retriever.DemonstrationRetriever