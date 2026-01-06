# Pricing Configuration (prices.yaml)

Configure token pricing for different LLM models to track and estimate API costs during UFO² execution.

---

## Overview

The `prices.yaml` file defines the cost per 1,000 tokens for different LLM models. UFO² uses this information to calculate and report the estimated cost of task executions.

**File Location**: `config/ufo/prices.yaml`

!!!warning "Pricing May Be Outdated"
    The pricing information in this file **may not be current**. LLM providers frequently update their pricing.
    
    - Always verify current pricing on provider websites
    - This file will be updated periodically
    - Use these values as estimates only

---

## Quick Start

### View Current Pricing

```yaml
# config/ufo/prices.yaml
gpt-4o:
  prompt: 0.0025
  completion: 0.01

gpt-4o-mini:
  prompt: 0.00015
  completion: 0.0006

gpt-4-turbo:
  prompt: 0.01
  completion: 0.03
```

### Add Your Model

```yaml
# Add pricing for your custom model
my-custom-model:
  prompt: 0.001      # USD per 1K prompt tokens
  completion: 0.003  # USD per 1K completion tokens
```

---

## Configuration Format

### Structure

Each model has two pricing fields:

```yaml
model-name:
  prompt: <cost_per_1k_prompt_tokens>
  completion: <cost_per_1k_completion_tokens>
```

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `prompt` | Float | USD/1K tokens | Cost per 1,000 input (prompt) tokens |
| `completion` | Float | USD/1K tokens | Cost per 1,000 output (completion) tokens |

---

## Common Models (As of Template)

!!!info "Verify Current Pricing"
    These prices are from the template and **may be outdated**. Always check provider websites for current pricing:
    
    - [OpenAI Pricing](https://openai.com/pricing)
    - [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)
    - [Anthropic Pricing](https://www.anthropic.com/pricing)
    - [Google AI Pricing](https://ai.google.dev/pricing)

### OpenAI Models

| Model | Prompt ($/1K) | Completion ($/1K) | Notes |
|-------|---------------|-------------------|-------|
| `gpt-4o` | $0.0025 | $0.01 | Latest GPT-4 optimized |
| `gpt-4o-mini` | $0.00015 | $0.0006 | Cheaper alternative |
| `gpt-4-turbo` | $0.01 | $0.03 | GPT-4 Turbo |
| `gpt-4-vision-preview` | $0.01 | $0.03 | GPT-4 with vision |
| `gpt-3.5-turbo` | $0.0005 | $0.0015 | GPT-3.5 |

### Example Configuration

```yaml
# OpenAI Models
gpt-4o:
  prompt: 0.0025
  completion: 0.01

gpt-4o-mini:
  prompt: 0.00015
  completion: 0.0006

gpt-4-turbo:
  prompt: 0.01
  completion: 0.03

gpt-4-vision-preview:
  prompt: 0.01
  completion: 0.03

gpt-3.5-turbo:
  prompt: 0.0005
  completion: 0.0015

# Claude Models (example)
claude-3-5-sonnet-20241022:
  prompt: 0.003
  completion: 0.015

# Gemini Models (example)
gemini-2.0-flash-exp:
  prompt: 0.0
  completion: 0.0
```

---

## Cost Tracking

UFO² automatically tracks costs when pricing information is available.

### During Execution

```python
# UFO² automatically calculates costs
Session logs show:
- Total prompt tokens used
- Total completion tokens used
- Estimated cost (based on prices.yaml)
```

### View Cost Summary

After task execution, check logs:

```
logs/<session-id>/cost_summary.json
```

**Example output**:
```json
{
  "total_cost_usd": 0.15,
  "prompt_tokens": 5000,
  "completion_tokens": 2000,
  "model": "gpt-4o"
}
```

---

## Updating Pricing

### Step 1: Check Current Pricing

Visit your LLM provider's pricing page:

- **OpenAI**: https://openai.com/pricing
- **Azure OpenAI**: https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/
- **Anthropic**: https://www.anthropic.com/pricing
- **Google**: https://ai.google.dev/pricing

### Step 2: Update prices.yaml

```yaml
# Update with current pricing
gpt-4o:
  prompt: 0.0025  # Update if changed
  completion: 0.01
```

### Step 3: Add New Models

```yaml
# Add newly released models
gpt-5:
  prompt: 0.005
  completion: 0.02
```

---

## Programmatic Access

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# Get pricing for a specific model
model_name = "gpt-4o"
if model_name in config.prices:
    prompt_cost = config.prices[model_name]["prompt"]
    completion_cost = config.prices[model_name]["completion"]
    print(f"{model_name}:")
    print(f"  Prompt: ${prompt_cost}/1K tokens")
    print(f"  Completion: ${completion_cost}/1K tokens")
else:
    print(f"No pricing info for {model_name}")
```

---

## Cost Estimation Example

```python
# Example: Estimate cost for a task
prompt_tokens = 10000      # 10K prompt tokens
completion_tokens = 5000   # 5K completion tokens
model = "gpt-4o"

# Get pricing
prompt_cost_per_1k = 0.0025
completion_cost_per_1k = 0.01

# Calculate
total_cost = (
    (prompt_tokens / 1000) * prompt_cost_per_1k +
    (completion_tokens / 1000) * completion_cost_per_1k
)

print(f"Estimated cost: ${total_cost:.4f}")
# Output: Estimated cost: $0.0750
```

---

## Notes

!!!info "Important Notes"
    - ✅ Pricing is for **cost estimation only**, not billing
    - ✅ Actual costs may vary based on your provider contract
    - ✅ Different Azure regions may have different pricing
    - ✅ Some models have tiered pricing based on volume
    - ✅ Prices change frequently - update regularly

---

## Related Documentation

- **[Agent Configuration](agents_config.md)** - LLM model selection
- **[System Configuration](system_config.md)** - Token limits and usage

---

## Summary

!!!success "Key Takeaways"
    ✅ **prices.yaml tracks LLM costs** - Estimates API spending  
    ✅ **Pricing may be outdated** - Always verify current rates  
    ✅ **Update regularly** - Providers change pricing frequently  
    ✅ **Add new models** - Include pricing for any custom models  
    ✅ **Cost tracking is automatic** - UFO² calculates costs during execution  
    
    **Keep pricing updated for accurate cost tracking!** 💰
