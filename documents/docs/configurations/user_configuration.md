# User Configuration

An overview of the user configuration options available in UFO. You need to rename the `config.yaml.template` in the folder `ufo/config` to `config.yaml` to configure the LLMs and other custom settings.

## LLM Configuration

You can configure the LLMs for the `HOST_AGENT` and `APP_AGENT` separately in the `config.yaml` file. The `FollowerAgent` and `EvaluationAgent` share the same LLM configuration as the `APP_AGENT`. Additionally, you can configure a backup LLM engine in the `BACKUP_AGENT` field to handle cases where the primary engines fail during inference.

Below are the configuration options for the LLMs, using OpenAI and Azure OpenAI (AOAI) as examples. You can find the settings for other LLM API configurations and usage in the `Supported Models` section of the documentation.

| Configuration Option | Description | Type | Default Value |
|----------------------|-------------|------|---------------|
| `VISUAL_MODE` | Whether to use visual mode to understand screenshots and take actions | Boolean | True |
| `API_TYPE` | The API type: "openai" for the OpenAI API, "aoai" for the AOAI API. | String | "openai" |
| `API_BASE` | The API endpoint for the LLM | String | "https://api.openai.com/v1/chat/completions" |
| `API_KEY` | The API key for the LLM | String | "sk-" |
| `API_VERSION` | The version of the API | String | "2024-02-15-preview" |
| `API_MODEL` | The LLM model name | String | "gpt-4-vision-preview" |

### For Azure OpenAI (AOAI) API
The following additional configuration option is available for the AOAI API:

| Configuration Option | Description | Type | Default Value |
|----------------------|-------------|------|---------------|
| `API_DEPLOYMENT_ID` | The deployment ID, only available for the AOAI API | String | "" |

Ensure to fill in the necessary API details for both the `HOST_AGENT` and `APP_AGENT` to enable UFO to interact with the LLMs effectively.

### LLM Parameters
You can also configure additional parameters for the LLMs in the `config.yaml` file:

| Configuration Option | Description | Type | Default Value |
|----------------------|-------------|------|---------------|
| `MAX_TOKENS` | The maximum token limit for the response completion | Integer | 2000 |
| `MAX_RETRY` | The maximum retry limit for the response completion | Integer | 3 |
| `TEMPERATURE` | The temperature of the model: the lower the value, the more consistent the output of the model | Float | 0.0 |
| `TOP_P` | The top_p of the model: the lower the value, the more conservative the output of the model | Float | 0.0 |
| `TIMEOUT` | The call timeout in seconds | Integer | 60 |

### For RAG Configuration to Enhance the UFO Agent
You can configure the RAG parameters in the `config.yaml` file to enhance the UFO agent with additional knowledge sources:

#### RAG Configuration for the Offline Docs
Configure the following parameters to allow UFO to use offline documents for the decision-making process:

| Configuration Option | Description | Type | Default Value |
|----------------------|-------------|------|---------------|
| `RAG_OFFLINE_DOCS` | Whether to use the offline RAG | Boolean | False |
| `RAG_OFFLINE_DOCS_RETRIEVED_TOPK` | The topk for the offline retrieved documents | Integer | 1 |


#### RAG Configuration for the Bing search
Configure the following parameters to allow UFO to use online Bing search for the decision-making process:

| Configuration Option | Description | Type | Default Value |
|----------------------|-------------|------|---------------|
| `RAG_ONLINE_SEARCH` | Whether to use the Bing search | Boolean | False |
| `BING_API_KEY` | The Bing search API key | String | "" |
| `RAG_ONLINE_SEARCH_TOPK` | The topk for the online search | Integer | 5 |
| `RAG_ONLINE_RETRIEVED_TOPK` | The topk for the online retrieved searched results | Integer | 1 |


#### RAG Configuration for experience
Configure the following parameters to allow UFO to use the RAG from its self-experience:

| Configuration Option | Description | Type | Default Value |
|----------------------|-------------|------|---------------|
| `RAG_EXPERIENCE` | Whether to use the RAG from its self-experience | Boolean | False |
| `RAG_EXPERIENCE_RETRIEVED_TOPK` | The topk for the offline retrieved documents | Integer | 5 |

#### RAG Configuration for demonstration
Configure the following parameters to allow UFO to use the RAG from user demonstration:

| Configuration Option | Description | Type | Default Value |
|----------------------|-------------|------|---------------|
| `RAG_DEMONSTRATION` | Whether to use the RAG from its user demonstration | Boolean | False |
| `RAG_DEMONSTRATION_RETRIEVED_TOPK` | The topk for the offline retrieved documents | Integer | 5 |
| `RAG_DEMONSTRATION_COMPLETION_N` | The number of completion choices for the demonstration result | Integer | 3 |


Explore the various RAG configurations to enhance the UFO agent with additional knowledge sources and improve its decision-making capabilities.






