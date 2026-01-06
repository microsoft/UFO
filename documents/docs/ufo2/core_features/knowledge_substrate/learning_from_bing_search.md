# Learning from Bing Search

UFO can enhance the AppAgent by searching for information on Bing to obtain up-to-date knowledge for niche tasks or applications beyond the AppAgent's existing knowledge base.

## Mechanism

When processing a request, the AppAgent:

1. Constructs a Bing search query based on the request context
2. Retrieves top-k search results from Bing
3. Extracts relevant information from the search results
4. Generates a plan informed by the retrieved information

This mechanism is particularly useful for:
- Tasks requiring current information (e.g., latest software features, current events)
- Applications or domains not covered by the agent's training data
- Dynamic information that changes frequently

## Configuration

To enable Bing search integration:

1. **Obtain Bing API Key**: Get your API key from [Microsoft Azure Bing Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)

2. **Configure Parameters**: Set the following options in `config.yaml`:

| Configuration Option | Description | Type | Default |
|---------------------|-------------|------|---------|
| `RAG_ONLINE_SEARCH` | Enable Bing search integration | Boolean | `False` |
| `BING_API_KEY` | Bing Search API key | String | `""` |
| `RAG_ONLINE_SEARCH_TOPK` | Number of search results to retrieve | Integer | `5` |
| `RAG_ONLINE_RETRIEVED_TOPK` | Number of retrieved results to include in prompt | Integer | `5` |

For more details on RAG configuration, see the [RAG Configuration Guide](../../../configuration/system/rag_config.md).

## API Reference

:::rag.retriever.OnlineDocRetriever