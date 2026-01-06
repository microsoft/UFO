# Speculative Multi-Action Execution

UFO² introduces **Speculative Multi-Action Execution**, a feature that allows agents to bundle multiple predicted steps into a single LLM call and validate them against the live application state. This approach can reduce LLM queries by up to **51%** compared to inferring each action separately.

## Overview

Traditional agent execution follows a sequential pattern: **think → act → observe → think → act → observe**. Each cycle requires a separate LLM inference, making complex tasks slow and expensive.

Speculative multi-action execution optimizes this by predicting a **batch of likely actions** upfront, then validating them against the live UI Automation state in a single execution pass:

![Speculative Multi-Action Execution](../../img/multiaction.png)

**Key Benefits:**

- **Reduced LLM Calls**: Up to 51% fewer inference requests for multi-step tasks
- **Faster Execution**: Batch prediction eliminates per-action round-trips
- **Lower Costs**: Fewer API calls reduce operational expenses
- **Maintained Accuracy**: Live validation ensures actions remain correct

## How It Works

When enabled, the agent:

1. **Predicts Action Sequence**: Uses contextual understanding to forecast likely next steps (e.g., "Open Excel → Navigate to cell A1 → Enter value → Save")
2. **Validates Against Live State**: Checks each predicted action against current UI Automation state
3. **Executes Valid Actions**: Runs all validated actions in sequence
4. **Handles Failures Gracefully**: Falls back to single-action mode if predictions fail validation

## Configuration

Enable speculative multi-action execution in `config/ufo/system.yaml`:

```yaml
# Action Configuration
ACTION_SEQUENCE: true  # Enable multi-action prediction and execution
```

**Configuration Location**: `config/ufo/system.yaml` (migrated from legacy `config_dev.yaml`)

For configuration migration details, see [Configuration Migration Guide](../../configuration/system/migration.md).

## Implementation Details

The multi-action system is implemented through two core classes in `ufo/agents/processors/schemas/actions.py`:

### ActionCommandInfo

Represents a single action with execution metadata:

:::agents.processors.schemas.actions.ActionCommandInfo

**Key Properties:**

- `function`: Action name (e.g., `click`, `type_text`)
- `arguments`: Action parameters
- `target`: UI element information
- `result`: Execution result with status and error details
- `action_string`: Human-readable representation

### ListActionCommandInfo

Manages sequences of multiple actions:

:::agents.processors.schemas.actions.ListActionCommandInfo

**Key Methods:**

- `add_action()`: Append action to sequence
- `to_list_of_dicts()`: Serialize for logging/debugging
- `to_representation()`: Generate human-readable summary
- `count_repeat_times()`: Track repeated actions for loop detection
- `get_results()`: Extract execution outcomes

## Example Scenarios

**Scenario 1: Excel Data Entry**

Without multi-action:
```
Think → Open Excel → Observe → Think → Click A1 → Observe → Think → Type "Sales" → Observe → Think → Save → Observe
```
**5 LLM calls**

With multi-action:
```
Think → [Open Excel, Click A1, Type "Sales", Save] → Observe
```
**1 LLM call** (80% reduction)

**Scenario 2: Email Composition**

Single-action mode:
```
Think → Open Outlook → Think → Click New → Think → Enter recipient → Think → Enter subject → Think → Type body → Think → Send
```
**7 LLM calls**

Multi-action mode:
```
Think → [Open Outlook, Click New, Enter recipient, Enter subject, Type body, Send] → Observe
```
**1 LLM call** (85% reduction)

## When to Use

**Best for:**

✅ Predictable workflows with clear action sequences  
✅ Repetitive tasks (data entry, form filling)  
✅ Applications with stable UI structures  
✅ Cost-sensitive deployments requiring fewer LLM calls

**Not recommended for:**

❌ Highly dynamic UIs with frequent state changes  
❌ Exploratory tasks requiring frequent observation  
❌ Error-prone applications where validation is critical per step  
❌ Tasks requiring user confirmation between actions

## Related Documentation

- [AppAgent Processing Strategy](../app_agent/strategy.md) — How agents process and execute actions
- [Hybrid GUI-API Actions](hybrid_actions.md) — Combining GUI automation with native APIs
- [System Configuration Reference](../../configuration/system/system_config.md) — Complete `system.yaml` options
- [Configuration Migration](../../configuration/system/migration.md) — Migrating from legacy `config_dev.yaml`

## Performance Considerations

**Trade-offs:**

- **Accuracy vs. Speed**: Multi-action sacrifices per-step validation for batch efficiency
- **Memory Usage**: Larger context windows needed to predict action sequences
- **Failure Recovery**: Invalid predictions require full sequence rollback and retry

**Optimization Tips:**

1. **Start Conservative**: Test with `ACTION_SEQUENCE: false` before enabling
2. **Monitor Validation Rates**: High rejection rates indicate poor prediction quality
3. **Combine with Hybrid Actions**: Use [API-based execution](hybrid_actions.md) where possible for fastest performance
4. **Tune MAX_STEP**: Set appropriate `MAX_STEP` limits in `system.yaml` to prevent runaway sequences
