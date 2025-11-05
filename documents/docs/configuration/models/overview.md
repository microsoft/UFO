# Supported Models

UFO supports a variety of LLM models and APIs. You can customize the model and API used by the `HOST_AGENT` and `APP_AGENT` in the `config.yaml` file. Additionally, you can configure a `BACKUP_AGENT` to handle requests when the primary agent fails to respond.

Please refer to the following sections for more information on the supported models and APIs:

| LLMs | Documentation |
| --- | --- |
| `OPENAI` | [OpenAI API](./openai.md) |
| `Azure OpenAI (AOAI)` | [Azure OpenAI API](./azure_openai.md) |
| `Gemini` | [Gemini API](./gemini.md) |
| `Claude` | [Claude API](./claude.md) |
| `QWEN` | [QWEN API](./qwen.md) |
| `Ollama` | [Ollama API](./ollama.md) |
| `Custom` | [Custom API](./custom_model.md) |


!!! info
    Each model is implemented as a separate class in the `ufo/llm` directory, and uses the functions `chat_completion` defined in the `BaseService` class of the `ufo/llm/base.py` file to obtain responses from the model.