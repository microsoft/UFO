# Customized LLM Models

UFO supports and welcomes the integration of custom LLM models. If you have a custom LLM model that you would like to use with UFO, follow the steps below to configure it.

## Step 1: Create and Serve Your Model

Create a custom LLM model and serve it on your local or remote environment. Ensure your model has an accessible API endpoint.

## Step 2: Implement Model Service Class

Create a Python script under the `ufo/llm` directory and implement your own LLM model class by inheriting the `BaseService` class from `ufo/llm/base.py`.

**Reference Example:** See `PlaceHolderService` in `ufo/llm/placeholder.py` as a template.

You must implement the `chat_completion` method:

```python
def chat_completion(
    self,
    messages: List[Dict[str, str]],
    n: int = 1,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    **kwargs: Any,
) -> Tuple[List[str], Optional[float]]:
    """
    Generates completions for a given list of messages.
    
    Args:
        messages: The list of messages to generate completions for.
        n: The number of completions to generate for each message.
        temperature: Controls the randomness (higher = more random).
        max_tokens: The maximum number of tokens in completions.
        top_p: Controls diversity (higher = more diverse).
        **kwargs: Additional keyword arguments.
    
    Returns:
        Tuple[List[str], Optional[float]]: 
            - List of generated completions for each message
            - Cost of the API call (None if not applicable)
    
    Raises:
        Exception: If an error occurs while making the API request.
    """
    # Your implementation here
    pass
```

**Key Implementation Points:**

- Handle message formatting according to your model's API
- Process visual inputs if `VISUAL_MODE` is enabled
- Implement retry logic for failed requests
- Calculate and return cost if applicable

## Step 3: Configure Agent Settings

Configure the `HOST_AGENT` and `APP_AGENT` in the `config/ufo/agents.yaml` file to use your custom model.

If the file doesn't exist, copy it from the template:

```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

Edit `config/ufo/agents.yaml` with your custom model configuration:

```yaml
HOST_AGENT:
  VISUAL_MODE: True  # Set based on your model's capabilities
  API_TYPE: "custom_model"  # Use custom model type
  API_BASE: "http://your-endpoint:port"  # Your model's API endpoint
  API_KEY: "YOUR_API_KEY"  # Your API key (if required)
  API_MODEL: "your-model-name"  # Your model identifier

APP_AGENT:
  VISUAL_MODE: True
  API_TYPE: "custom_model"
  API_BASE: "http://your-endpoint:port"
  API_KEY: "YOUR_API_KEY"
  API_MODEL: "your-model-name"
```

**Configuration Fields:**

- **`VISUAL_MODE`**: Set to `True` if your model supports visual inputs
- **`API_TYPE`**: Use `"custom_model"` for custom implementations
- **`API_BASE`**: Your custom model's API endpoint URL
- **`API_KEY`**: Authentication key (if your model requires it)
- **`API_MODEL`**: Model identifier or name

**For detailed configuration options, see:**

- [Agent Configuration Guide](../system/agents_config.md) - Complete agent settings reference
- [Model Configuration Overview](overview.md) - Compare different LLM providers

## Step 4: Register Your Model

Update the model factory in `ufo/llm/__init__.py` to include your custom model class:

```python
from ufo.llm.your_model import YourModelService

# Add to the model factory mapping
MODEL_FACTORY = {
    # ... existing models ...
    "custom_model": YourModelService,
}
```

## Step 5: Start Using UFO

After configuration, you can start using UFO with your custom model. Refer to the [Quick Start Guide](../../getting_started/quick_start_ufo2.md) for detailed instructions on running your first tasks.

**Testing Your Integration:**

1. Test with simple requests first
2. Verify visual mode works (if applicable)
3. Check error handling and retry logic
4. Monitor response quality and latency