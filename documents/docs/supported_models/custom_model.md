# Customized LLM Models

We support and welcome the integration of custom LLM models in UFO. If you have a custom LLM model that you would like to use with UFO, you can follow the steps below to configure the model in UFO.

## Step 1
 Create a custom LLM model and serve it on your local environment. 

## Step 2
 Create a python script under the `ufo/llm` directory, and implement your own LLM model class by inheriting the `BaseService` class in the `ufo/llm/base.py` file. We leave a `PlaceHolderService` class in the `ufo/llm/placeholder.py` file as an example. You must implement the `chat_completion` method in your LLM model class to accept a list of messages and return a list of completions for each message.

```python
def chat_completion(
    self,
    messages,
    n,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    **kwargs: Any,
):
    """
    Generates completions for a given list of messages.
    Args:
        messages (List[str]): The list of messages to generate completions for.
        n (int): The number of completions to generate for each message.
        temperature (float, optional): Controls the randomness of the generated completions. Higher values (e.g., 0.8) make the completions more random, while lower values (e.g., 0.2) make the completions more focused and deterministic. If not provided, the default value from the model configuration will be used.
        max_tokens (int, optional): The maximum number of tokens in the generated completions. If not provided, the default value from the model configuration will be used.
        top_p (float, optional): Controls the diversity of the generated completions. Higher values (e.g., 0.8) make the completions more diverse, while lower values (e.g., 0.2) make the completions more focused. If not provided, the default value from the model configuration will be used.
        **kwargs: Additional keyword arguments to be passed to the underlying completion method.
    Returns:
        List[str], None:A list of generated completions for each message and the cost set to be None.
    Raises:
        Exception: If an error occurs while making the API request.
    """
    pass
```

## Step 3
After implementing the LLM model class, you can configure the `HOST_AGENT` and `APP_AGENT` in the `config.yaml` file (rename the `config_template.yaml` file to `config.yaml`) to use the custom LLM model. The following is an example configuration for the custom LLM model:

```yaml
VISUAL_MODE: True, # Whether to use visual mode to understand screenshots and take actions
API_TYPE: "custom_model" , # The API type, "openai" for the OpenAI API, "aoai" for the AOAI API, 'azure_ad' for the ad authority of the AOAI API.  
API_BASE: "YOUR_ENDPOINT", #  The custom LLM API address.
API_MODEL: "YOUR_MODEL",  # The custom LLM model name.
```

## Step 4
After configuring the `HOST_AGENT` and `APP_AGENT` with the custom LLM model, you can start using UFO to interact with the custom LLM model for various tasks on Windows OS. Please refer to the [Quick Start Guide](../getting_started/quick_start.md) for more details on how to get started with UFO.