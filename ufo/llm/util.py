# Source: https://openai.com/pricing
# Prices in $ per 1000 tokens
# Last updated: 2024-01-26
OPENAI_PRICES = {
    "gpt-4-0613": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo-0613": {"input": 0.0015, "output": 0.002},
    "gpt-4-0125-preview": {"input": 0.01, "output": 0.03},
    "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
    "gpt-4-1106-vision-preview": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-32k": {"input": 0.06, "output": 0.12},
    "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
    "gpt-3.5-turbo-instruct": {"input": 0.0015, "output": 0.002},
    "gpt-3.5-turbo-16k-0613": {"input": 0.003, "output": 0.004},
    "whisper-1": {"input": 0.006, "output": 0.006},
    "tts-1": {"input": 0.015, "output": 0.015},
    "tts-hd-1": {"input": 0.03, "output": 0.03},
    "text-embedding-ada-002-v2": {"input": 0.0001, "output": 0.0001},
    "text-davinci:003": {"input": 0.02, "output": 0.02},
    "text-ada-001": {"input": 0.0004, "output": 0.0004},
    }

AZURE_PRICES = {
    "gpt-35-turbo-20220309":{"input": 0.0015, "output": 0.002},
    "gpt-35-turbo-20230613":{"input": 0.0015, "output": 0.002},
    "gpt-35-turbo-16k-20230613":{"input": 0.003, "output": 0.004},
    "gpt-35-turbo-1106":{"input": 0.001, "output": 0.002},
    "gpt-4-20230321":{"input": 0.03, "output": 0.06},
    "gpt-4-32k-20230321":{"input": 0.06, "output": 0.12},
    "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
    "gpt-4-0125-preview": {"input": 0.01, "output": 0.03},
    "gpt-4-visual-preview": {"input": 0.01, "output": 0.03},
}


def get_cost_estimator(type: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    if type == "openai":
        cost = prompt_tokens * OPENAI_PRICES[model]["input"]/1000 + completion_tokens * OPENAI_PRICES[model]["output"]/1000
    elif type == "azure_ad" or type == "aoai":
        if model in AZURE_PRICES:
            cost = prompt_tokens * AZURE_PRICES[model]["input"]/1000 + completion_tokens * AZURE_PRICES[model]["output"]/1000
        else:
            print(f"Model {model} not found in Azure prices")
            return None
    else:
        return None 
    return cost