# Learning from Bing Search

UFO provides the capability to reinforce the AppAgent by searching for information on Bing to obtain up-to-date knowledge for niche tasks or applications which beyond the `AppAgent`'s knowledge.

## Mechanism
Upon receiving a request, the `AppAgent` constructs a Bing search query based on the request and retrieves the search results from Bing. The `AppAgent` then extracts the relevant information from the top-k search results from Bing and generates a plan based on the retrieved information.


## Activate the Learning from Bing Search


### Step 1: Obtain Bing API Key
To use the Bing search, you need to obtain a Bing API key. You can follow the instructions on the [Microsoft Azure Bing Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) to get the API key.


### Step 2: Configure the AppAgent

Configure the following parameters to allow UFO to use online Bing search for the decision-making process:

| Configuration Option | Description | Type | Default Value |
|----------------------|-------------|------|---------------|
| `RAG_ONLINE_SEARCH` | Whether to use the Bing search | Boolean | False |
| `BING_API_KEY` | The Bing search API key | String | "" |
| `RAG_ONLINE_SEARCH_TOPK` | The topk for the online search | Integer | 5 |
| `RAG_ONLINE_RETRIEVED_TOPK` | The topk for the online retrieved searched results | Integer | 1 |

# Reference

:::rag.retriever.OnlineDocRetriever