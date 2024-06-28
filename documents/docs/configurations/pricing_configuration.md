# Pricing Configuration

We provide a configuration file `pricing_config.yaml` to calculate the pricing of the UFO agent using different LLM APIs. The pricing configuration file is located in the `ufo/config` directory. Note that the pricing configuration file is only used for reference and may not be up-to-date. Please refer to the official pricing documentation of the respective LLM API provider for the most accurate pricing information.

You can also customize the pricing configuration file based on the configured model names and their respective input and output prices by adding or modifying the pricing information in the `pricing_config.yaml` file. Below is the default pricing configuration:

```yaml
# Prices in $ per 1000 tokens
# Last updated: 2024-05-13
PRICES: { 
    "openai/gpt-4-0613": {"input": 0.03, "output": 0.06},
    "openai/gpt-3.5-turbo-0613": {"input": 0.0015, "output": 0.002},
    "openai/gpt-4-0125-preview": {"input": 0.01, "output": 0.03},
    "openai/gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
    "openai/gpt-4-1106-vision-preview": {"input": 0.01, "output": 0.03},
    "openai/gpt-4": {"input": 0.03, "output": 0.06},
    "openai/gpt-4-32k": {"input": 0.06, "output": 0.12},
    "openai/gpt-4-turbo": {"input":0.01,"output": 0.03},
    "openai/gpt-4o": {"input": 0.005,"output": 0.015},
    "openai/gpt-4o-2024-05-13": {"input": 0.005, "output": 0.015},
    "openai/gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
    "openai/gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
    "openai/gpt-3.5-turbo-instruct": {"input": 0.0015, "output": 0.002},
    "openai/gpt-3.5-turbo-16k-0613": {"input": 0.003, "output": 0.004},
    "openai/whisper-1": {"input": 0.006, "output": 0.006},
    "openai/tts-1": {"input": 0.015, "output": 0.015},
    "openai/tts-hd-1": {"input": 0.03, "output": 0.03},
    "openai/text-embedding-ada-002-v2": {"input": 0.0001, "output": 0.0001},
    "openai/text-davinci:003": {"input": 0.02, "output": 0.02},
    "openai/text-ada-001": {"input": 0.0004, "output": 0.0004},
    "azure/gpt-35-turbo-20220309":{"input": 0.0015, "output": 0.002},
    "azure/gpt-35-turbo-20230613":{"input": 0.0015, "output": 0.002},
    "azure/gpt-35-turbo-16k-20230613":{"input": 0.003, "output": 0.004},
    "azure/gpt-35-turbo-1106":{"input": 0.001, "output": 0.002},
    "azure/gpt-4-20230321":{"input": 0.03, "output": 0.06},
    "azure/gpt-4-32k-20230321":{"input": 0.06, "output": 0.12},
    "azure/gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
    "azure/gpt-4-0125-preview": {"input": 0.01, "output": 0.03},
    "azure/gpt-4-visual-preview": {"input": 0.01, "output": 0.03},
    "azure/gpt-4-turbo-20240409": {"input":0.01,"output": 0.03},
    "azure/gpt-4o": {"input": 0.005,"output": 0.015},
    "azure/gpt-4o-20240513": {"input": 0.005, "output": 0.015},
    "qwen/qwen-vl-plus": {"input": 0.008, "output": 0.008},
    "qwen/qwen-vl-max": {"input": 0.02, "output": 0.02},
    "gemini/gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
    "gemini/gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
    "gemini/gemini-1.0-pro": {"input": 0.0005, "output": 0.0015},
}
```

Please refer to the official pricing documentation of the respective LLM API provider for the most accurate pricing information.