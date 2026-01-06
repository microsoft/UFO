# Ollama

## Step 1: Install and Start Ollama

Go to [Ollama](https://github.com/jmorganca/ollama) and follow the installation instructions for your platform.

**For Linux & WSL2:**

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Start the Ollama server
ollama serve
```

**For Windows/Mac:** Download and install from the [Ollama website](https://ollama.ai/).

## Step 2: Pull and Test a Model

Open a new terminal and pull a model:

```bash
# Pull a model (e.g., llama2)
ollama pull llama2

# Test the model
ollama run llama2
```

By default, Ollama starts a server at `http://localhost:11434`, which will be used as the API base in your configuration.

## Step 3: Configure Agent Settings

Configure the `HOST_AGENT` and `APP_AGENT` in the `config/ufo/agents.yaml` file to use Ollama.

If the file doesn't exist, copy it from the template:

```powershell
Copy-Item config\ufo\agents.yaml.template config\ufo\agents.yaml
```

Edit `config/ufo/agents.yaml` with your Ollama configuration:

```yaml
HOST_AGENT:
  VISUAL_MODE: True  # Enable if model supports vision (e.g., llava)
  API_TYPE: "ollama"  # Use Ollama API
  API_BASE: "http://localhost:11434"  # Ollama server endpoint
  API_KEY: "ollama"  # Placeholder (not used but required)
  API_MODEL: "llama2"  # Model name (must match pulled model)

APP_AGENT:
  VISUAL_MODE: True
  API_TYPE: "ollama"
  API_BASE: "http://localhost:11434"
  API_KEY: "ollama"
  API_MODEL: "llama2"
```

**Configuration Fields:**

- **`VISUAL_MODE`**: Set to `True` only for vision-capable models like `llava`
- **`API_TYPE`**: Use `"ollama"` for Ollama API (case-sensitive in code: lowercase)
- **`API_BASE`**: Ollama server URL (default: `http://localhost:11434`)
- **`API_KEY`**: Placeholder value (not used but required in config)
- **`API_MODEL`**: Model name matching your pulled model

**Important: Increase Context Length**

UFO requires at least 20,000 tokens to function properly. Ollama's default context length is 2048 tokens, which is insufficient. You must create a custom model with increased context:

1. Create a `Modelfile`:

```text
FROM llama2
PARAMETER num_ctx 32768
```

2. Build the custom model:

```bash
ollama create llama2-max-ctx -f Modelfile
```

3. Use the custom model in your config:

```yaml
API_MODEL: "llama2-max-ctx"
```

For more details, see [Ollama's Modelfile documentation](https://github.com/ollama/ollama/blob/main/docs/modelfile.md).

**For detailed configuration options, see:**

- [Agent Configuration Guide](../system/agents_config.md) - Complete agent settings reference
- [Model Configuration Overview](overview.md) - Compare different LLM providers

## Step 4: Start Using UFO

After configuration, you can start using UFO with Ollama. Refer to the [Quick Start Guide](../../getting_started/quick_start_ufo2.md) for detailed instructions on running your first tasks.



