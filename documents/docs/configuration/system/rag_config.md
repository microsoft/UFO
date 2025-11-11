# RAG Configuration (rag.yaml)

Configure Retrieval-Augmented Generation (RAG) to enhance UFO² with external knowledge sources, online search, experience learning, and demonstration-based learning.

---

## Overview

The `rag.yaml` file configures knowledge retrieval systems that augment UFO²'s capabilities beyond its base LLM knowledge. RAG helps UFO² make better decisions by providing:

- **Offline Documentation**: Application manuals and documentation
- **Online Search**: Real-time web search via Bing
- **Experience Learning**: Learn from past successful executions
- **Demonstration Learning**: Learn from user demonstrations

**File Location**: `config/ufo/rag.yaml`

**Optional Configuration:** RAG features are **optional**. UFO² works without them, but they can significantly improve performance on complex or domain-specific tasks.

---

## Quick Start

### Disable All RAG (Default)

```yaml
# Minimal configuration - no external knowledge
RAG_OFFLINE_DOCS: False
RAG_ONLINE_SEARCH: False
RAG_EXPERIENCE: False
RAG_DEMONSTRATION: False
```

### Enable Online Search Only

```yaml
# Most useful for general tasks
RAG_OFFLINE_DOCS: False

RAG_ONLINE_SEARCH: True
BING_API_KEY: "YOUR_BING_API_KEY_HERE"
RAG_ONLINE_SEARCH_TOPK: 5
RAG_ONLINE_RETRIEVED_TOPK: 5

RAG_EXPERIENCE: False
RAG_DEMONSTRATION: False
```

### Enable Experience Learning

```yaml
# Learn from past executions
RAG_OFFLINE_DOCS: False
RAG_ONLINE_SEARCH: False

RAG_EXPERIENCE: True
RAG_EXPERIENCE_RETRIEVED_TOPK: 5

RAG_DEMONSTRATION: False
```

### Enable All Features

```yaml
# Maximum knowledge augmentation
RAG_OFFLINE_DOCS: True
RAG_OFFLINE_DOCS_RETRIEVED_TOPK: 1

RAG_ONLINE_SEARCH: True
BING_API_KEY: "YOUR_BING_API_KEY_HERE"
RAG_ONLINE_SEARCH_TOPK: 5
RAG_ONLINE_RETRIEVED_TOPK: 5

RAG_EXPERIENCE: True
RAG_EXPERIENCE_RETRIEVED_TOPK: 5

RAG_DEMONSTRATION: True
RAG_DEMONSTRATION_RETRIEVED_TOPK: 5
```

---

## RAG Components

### 1. Offline Documentation

Retrieve relevant documentation from local knowledge bases (app manuals, guides, API docs).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `RAG_OFFLINE_DOCS` | Boolean | `False` | Enable offline documentation retrieval |
| `RAG_OFFLINE_DOCS_RETRIEVED_TOPK` | Integer | `1` | Number of documents to retrieve |

**Example**:
```yaml
RAG_OFFLINE_DOCS: True
RAG_OFFLINE_DOCS_RETRIEVED_TOPK: 1
```

!!!info "Use Case"
    - Application-specific tasks (Excel formulas, Word formatting)
    - Domain-specific workflows (accounting, design)
    - Requires pre-indexed documentation

**Setup**:
1. Place documentation in `vectordb/docs/`
2. Index documents: `python -m learner`
3. Enable in `rag.yaml`

---

### 2. Online Search

Search the web in real-time using Bing Search API.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `RAG_ONLINE_SEARCH` | Boolean | `False` | Enable online Bing search |
| `BING_API_KEY` | String | `""` | Bing Search API key |
| `RAG_ONLINE_SEARCH_TOPK` | Integer | `5` | Number of search results to fetch |
| `RAG_ONLINE_RETRIEVED_TOPK` | Integer | `5` | Number of results to include in prompt |

**Example**:
```yaml
RAG_ONLINE_SEARCH: True
BING_API_KEY: "abc123xyz..."
RAG_ONLINE_SEARCH_TOPK: 5
RAG_ONLINE_RETRIEVED_TOPK: 5
```

!!!tip "Getting Bing API Key"
    1. Go to [Azure Portal](https://portal.azure.com)
    2. Create a "Bing Search v7" resource
    3. Copy the API key from "Keys and Endpoint"
    4. Add to `rag.yaml`: `BING_API_KEY: "your-key"`

**Use Cases**:
- Tasks requiring current information
- Unfamiliar applications or features
- Troubleshooting specific error messages
- Finding how-to guides dynamically

**Example Query Flow**:
```
User Request: "Create a pivot table in Excel"
↓
Bing Search: "how to create pivot table in Excel"
↓
Retrieved: Top 5 results about pivot tables
↓
LLM receives context from search results
↓
Better action decisions
```

---

### 3. Experience Learning

Learn from UFO²'s own past successful task executions.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `RAG_EXPERIENCE` | Boolean | `False` | Enable experience learning |
| `RAG_EXPERIENCE_RETRIEVED_TOPK` | Integer | `5` | Number of past experiences to retrieve |
| `EXPERIENCE_SAVED_PATH` | String | Auto-generated | Path to experience database |
| `EXPERIENCE_PROMPT` | String | Auto-generated | Experience prompt template |

**Example**:
```yaml
RAG_EXPERIENCE: True
RAG_EXPERIENCE_RETRIEVED_TOPK: 5
```

!!!info "How It Works"
    1. UFO² completes a task successfully
    2. Task steps are saved to experience database
    3. For future similar tasks, relevant past experiences are retrieved
    4. LLM learns from successful patterns

**Use Cases**:
- Repetitive tasks with slight variations
- Learning organizational-specific workflows
- Improving over time on common tasks

**Example**:
```
First Time: "Create a monthly sales report"
→ Task succeeds, 15 steps recorded

Second Time: "Create a quarterly sales report"
→ Retrieves "monthly report" experience
→ Adapts the pattern, faster execution
```

**Default Paths**:
```yaml
# Auto-generated if not specified
EXPERIENCE_SAVED_PATH: "vectordb/experience"
EXPERIENCE_PROMPT: "ufo/prompts/share/experience/experience.yaml"
```

---

### 4. Demonstration Learning

Learn from user demonstrations (you show UFO² how to do a task).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `RAG_DEMONSTRATION` | Boolean | `False` | Enable demonstration learning |
| `RAG_DEMONSTRATION_RETRIEVED_TOPK` | Integer | `5` | Number of demonstrations to retrieve |
| `DEMONSTRATION_SAVED_PATH` | String | Auto-generated | Path to demonstration database |
| `DEMONSTRATION_PROMPT` | String | Auto-generated | Demonstration prompt template |

**Example**:
```yaml
RAG_DEMONSTRATION: True
RAG_DEMONSTRATION_RETRIEVED_TOPK: 5
```

!!!info "How It Works"
    1. User demonstrates a task (UFO² records it)
    2. Demonstration is saved with annotations
    3. For similar future tasks, demonstrations are retrieved
    4. LLM mimics the demonstrated behavior

**Use Cases**:
- Complex, domain-specific workflows
- Organizational-specific procedures
- Tasks with many edge cases

**Workflow**:
```
1. Record Demonstration:
   python -m ufo --mode demonstration
   → Perform task manually
   → UFO² records your actions

2. Save Demonstration:
   → Stored in vectordb/demonstration/

3. Future Task:
   "Do the same report formatting"
   → Retrieves your demonstration
   → Replicates your steps
```

**Default Paths**:
```yaml
# Auto-generated if not specified
DEMONSTRATION_SAVED_PATH: "vectordb/demonstration"
DEMONSTRATION_PROMPT: "ufo/prompts/share/demonstration/demonstration.yaml"
```

---

## Complete Configuration Examples

### Minimal (No RAG)

```yaml
# config/ufo/rag.yaml
RAG_OFFLINE_DOCS: False
RAG_ONLINE_SEARCH: False
RAG_EXPERIENCE: False
RAG_DEMONSTRATION: False
```

### Online Search Only

```yaml
RAG_OFFLINE_DOCS: False

RAG_ONLINE_SEARCH: True
BING_API_KEY: "your-bing-api-key-here"
RAG_ONLINE_SEARCH_TOPK: 5
RAG_ONLINE_RETRIEVED_TOPK: 5

RAG_EXPERIENCE: False
RAG_DEMONSTRATION: False
```

### Experience Learning Only

```yaml
RAG_OFFLINE_DOCS: False
RAG_ONLINE_SEARCH: False

RAG_EXPERIENCE: True
RAG_EXPERIENCE_RETRIEVED_TOPK: 5
EXPERIENCE_SAVED_PATH: "vectordb/experience"
EXPERIENCE_PROMPT: "ufo/prompts/share/experience/experience.yaml"

RAG_DEMONSTRATION: False
```

### Full RAG Setup

```yaml
# Offline docs
RAG_OFFLINE_DOCS: True
RAG_OFFLINE_DOCS_RETRIEVED_TOPK: 1

# Online search
RAG_ONLINE_SEARCH: True
BING_API_KEY: "your-bing-api-key"
RAG_ONLINE_SEARCH_TOPK: 5
RAG_ONLINE_RETRIEVED_TOPK: 5

# Experience
RAG_EXPERIENCE: True
RAG_EXPERIENCE_RETRIEVED_TOPK: 5
EXPERIENCE_SAVED_PATH: "vectordb/experience"
EXPERIENCE_PROMPT: "ufo/prompts/share/experience/experience.yaml"

# Demonstration
RAG_DEMONSTRATION: True
RAG_DEMONSTRATION_RETRIEVED_TOPK: 5
DEMONSTRATION_SAVED_PATH: "vectordb/demonstration"
DEMONSTRATION_PROMPT: "ufo/prompts/share/demonstration/demonstration.yaml"
```

---

## Setting Up Each RAG Component

### Setup: Offline Documentation

**Step 1**: Prepare documentation
```powershell
# Place docs in vectordb/docs/
New-Item -ItemType Directory -Path "vectordb\docs\excel" -Force
Copy-Item "C:\path\to\excel_guide.pdf" "vectordb\docs\excel\"
```

**Step 2**: Index documents
```powershell
python -m learner --index-docs
```

**Step 3**: Enable in config
```yaml
RAG_OFFLINE_DOCS: True
RAG_OFFLINE_DOCS_RETRIEVED_TOPK: 1
```

---

### Setup: Online Search

**Step 1**: Get Bing API key

1. Go to [Azure Portal](https://portal.azure.com)
2. Create resource → Search for "Bing Search v7"
3. Create the resource
4. Go to "Keys and Endpoint"
5. Copy Key 1

**Step 2**: Add to config
```yaml
RAG_ONLINE_SEARCH: True
BING_API_KEY: "your-copied-key-here"
RAG_ONLINE_SEARCH_TOPK: 5
RAG_ONLINE_RETRIEVED_TOPK: 5
```

**Step 3**: Test
```python
from config.config_loader import get_ufo_config

config = get_ufo_config()
print(f"Bing search enabled: {config.rag.online_search}")
print(f"API key set: {bool(config.rag.BING_API_KEY)}")
```

---

### Setup: Experience Learning

**Step 1**: Enable in config
```yaml
RAG_EXPERIENCE: True
RAG_EXPERIENCE_RETRIEVED_TOPK: 5
```

**Step 2**: Run tasks normally
```powershell
python -m ufo --request "Create a sales report"
```

**Step 3**: Successful tasks are auto-saved
```
Experience saved to: vectordb/experience/
```

**Step 4**: Future tasks retrieve experiences
```powershell
# Similar task will use past experience
python -m ufo --request "Create a quarterly report"
```

---

### Setup: Demonstration Learning

**Step 1**: Record demonstration
```powershell
python -m ufo --mode demonstration --task "format_monthly_report"
```

**Step 2**: Perform task manually
- UFO² records your every action
- Add annotations/comments

**Step 3**: Save demonstration
```
Demonstration saved to: vectordb/demonstration/
```

**Step 4**: Enable in config
```yaml
RAG_DEMONSTRATION: True
RAG_DEMONSTRATION_RETRIEVED_TOPK: 5
```

**Step 5**: Use demonstrations
```powershell
python -m ufo --request "Format the report like I showed you"
```

---

## Programmatic Access

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# Check RAG settings
if config.rag.online_search:
    print(f"Online search enabled")
    print(f"Top K: {config.rag.online_search_topk}")
    
if config.rag.experience:
    print(f"Experience learning enabled")
    print(f"Experience path: {config.rag.EXPERIENCE_SAVED_PATH}")

if config.rag.offline_docs:
    print(f"Offline docs enabled")

# Access specific fields
bing_key = config.rag.BING_API_KEY
exp_topk = config.rag.experience_retrieved_topk
```

---

## Performance Considerations

### Impact on Speed

| RAG Type | Speed Impact | When to Use |
|----------|--------------|-------------|
| **Offline Docs** | Low | Always (if indexed) |
| **Online Search** | Medium | For unfamiliar tasks |
| **Experience** | Low | Always (improves over time) |
| **Demonstration** | Low | For specific workflows |

### Impact on Cost

| RAG Type | Cost Impact | Notes |
|----------|-------------|-------|
| **Offline Docs** | None | One-time indexing cost |
| **Online Search** | Low | Bing API: ~$3/1000 queries |
| **Experience** | None | Free storage |
| **Demonstration** | None | Free storage |

!!!tip "Recommended Configuration"
    For most users:
    ```yaml
    RAG_ONLINE_SEARCH: True  # Useful for general tasks
    RAG_EXPERIENCE: True     # Improves over time
    RAG_OFFLINE_DOCS: False  # Unless you have specific docs
    RAG_DEMONSTRATION: False # Unless training specific workflows
    ```

---

## Troubleshooting

### Issue 1: Bing Search Not Working

!!!bug "Error Message"
    ```
    BingSearchError: Invalid API key
    ```
    
    **Solutions**:
    1. Verify API key is correct
    2. Check key has not expired
    3. Ensure Bing Search v7 resource is active
    4. Check Azure subscription is active

---

### Issue 2: Experience Not Retrieved

!!!bug "Symptom"
    UFO² doesn't seem to learn from past tasks
    
    **Solutions**:
    1. Check experience database exists:
       ```powershell
       Test-Path "vectordb\experience"
       ```
    2. Verify tasks completed successfully
    3. Check similarity threshold (may be too strict)
    4. Increase `RAG_EXPERIENCE_RETRIEVED_TOPK`

---

### Issue 3: Offline Docs Not Indexed

!!!bug "Error Message"
    ```
    No offline documents found
    ```
    
    **Solutions**:
    1. Run indexing:
       ```powershell
       python -m learner --index-docs
       ```
    2. Check documents are in `vectordb/docs/`
    3. Verify supported formats (PDF, TXT, MD)

---

### Issue 4: Too Much Context

!!!bug "Symptom"
    Token limits exceeded, slow responses
    
    **Solution**: Reduce Top-K values
    ```yaml
    RAG_ONLINE_RETRIEVED_TOPK: 3  # Instead of 5
    RAG_EXPERIENCE_RETRIEVED_TOPK: 3
    RAG_DEMONSTRATION_RETRIEVED_TOPK: 3
    ```

---

## Best Practices

### When to Enable Each Component

| Scenario | Recommended RAG |
|----------|----------------|
| **General automation** | Online Search |
| **Repetitive tasks** | Experience Learning |
| **Domain-specific workflows** | Offline Docs + Demonstration |
| **Learning over time** | Experience |
| **New to UFO²** | Online Search only |
| **Production deployment** | Experience + Offline Docs |

### Top-K Selection

| Field | Recommended Range | Notes |
|-------|-------------------|-------|
| `RAG_ONLINE_SEARCH_TOPK` | 3-10 | More = better context, slower |
| `RAG_ONLINE_RETRIEVED_TOPK` | 3-5 | Balance quality vs tokens |
| `RAG_EXPERIENCE_RETRIEVED_TOPK` | 3-5 | Most relevant experiences |
| `RAG_DEMONSTRATION_RETRIEVED_TOPK` | 1-3 | Usually need few examples |
| `RAG_OFFLINE_DOCS_RETRIEVED_TOPK` | 1-2 | Docs are usually long |

---

## Environment Variables

Store API keys securely:

```yaml
# Use environment variable instead of hardcoded key
BING_API_KEY: "${BING_API_KEY}"
```

**Set environment variable**:

**Windows PowerShell:**
```powershell
$env:BING_API_KEY = "your-key-here"
```

**Windows (Persistent):**
```powershell
[System.Environment]::SetEnvironmentVariable('BING_API_KEY', 'your-key', 'User')
```

---

## Related Documentation

- **[Agent Configuration](agents_config.md)** - LLM settings
- **[System Configuration](system_config.md)** - Runtime settings

---

## Summary

!!!success "Key Takeaways"
    ✅ **RAG is optional** - UFO² works without it  
    ✅ **Online Search** - Most useful for general tasks (needs Bing API key)  
    ✅ **Experience** - Free, improves over time automatically  
    ✅ **Offline Docs** - Great for domain-specific knowledge  
    ✅ **Demonstration** - Best for complex, specific workflows  
    ✅ **Start simple** - Enable Online Search first, add others as needed  
    
    **Enhance UFO² with knowledge retrieval!** 🧠
