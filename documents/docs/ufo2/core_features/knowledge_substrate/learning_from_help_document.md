# Learning from Help Documents

Users or applications can provide help documents to enhance the AppAgent's capabilities. The AppAgent retrieves relevant knowledge from these documents to improve task understanding, plan quality, and application interaction efficiency.

For instructions on providing help documents, see the [Help Document Provision](../../../tutorials/creating_app_agent/help_document_provision.md) guide.

## Mechanism

Help documents are structured as **task-solution pairs**. When processing a request, the AppAgent:

1. Retrieves relevant help documents by matching the request against task descriptions
2. Uses the retrieved solutions as references for plan generation
3. Adapts the solutions to the specific context

Since retrieved documents may not be perfectly relevant, the AppAgent treats them as references rather than strict instructions, allowing for flexible adaptation to the actual task requirements.

## Configuration

To enable learning from help documents:

1. **Provide Help Documents**: Follow the [Help Document Provision](../../../tutorials/creating_app_agent/help_document_provision.md) guide to prepare and index help documents

2. **Configure Parameters**: Set the following options in `config.yaml`:

| Configuration Option | Description | Type | Default |
|---------------------|-------------|------|---------|
| `RAG_OFFLINE_DOCS` | Enable offline help document retrieval | Boolean | `False` |
| `RAG_OFFLINE_DOCS_RETRIEVED_TOPK` | Number of top documents to retrieve | Integer | `1` |

For more details on RAG configuration, see the [RAG Configuration Guide](../../../configuration/system/rag_config.md).

## API Reference

:::rag.retriever.OfflineDocRetriever