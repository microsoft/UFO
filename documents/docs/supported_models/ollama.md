# Ollama

## Step 1
If you want to use the Ollama model, Go to [Ollama](https://github.com/jmorganca/ollama) and follow the instructions to serve a LLM model on your local environment. We provide a short example to show how to configure the ollama in the following, which might change if ollama makes updates.

```bash
## Install ollama on Linux & WSL2
curl https://ollama.ai/install.sh | sh
## Run the serving
ollama serve
```

## Step 2
Open another terminal and run the following command to test the ollama model:

```bash
ollama run YOUR_MODEL
```

!!!info
    When serving LLMs via Ollama, it will by default start a server at `http://localhost:11434`, which will later be used as the API base in `config.yaml`.

## Step 3
After obtaining the API key, you can configure the `HOST_AGENT` and `APP_AGENT` in the `config.yaml` file (rename the `config_template.yaml` file to `config.yaml`) to use the Ollama API. The following is an example configuration for the Ollama API:

```yaml
VISUAL_MODE: True, # Whether to use visual mode to understand screenshots and take actions
API_TYPE: "ollama" ,
API_BASE: "YOUR_ENDPOINT",   
API_KEY: "ollama", # not used but required
API_MODEL: "YOUR_MODEL"
```


!!! tip
    `API_BASE` is the URL started in the Ollama LLM server and `API_MODEL` is the model name of Ollama LLM, it should be same as the one you served before. In addition, due to model token limitations, you can use lite version of prompt to have a taste on UFO which can be configured in `config_dev.yaml`.

!!! note
    To run UFO successfully with Ollama, you must increase the default token limit of 2048 tokens by creating a custom model with a modified Modelfile. Create a new Modelfile that specifies `PARAMETER num_ctx 32768` (or your model's maximum context length), then build your custom model with `ollama create [model]-max-ctx -f Modelfile`. UFO requires at least 20,000 tokens to function properly, so setting the `num_ctx` parameter to your model's maximum supported context length will ensure optimal performance. For more details on Modelfile configuration, refer to [Ollama's official documentation](https://github.com/ollama/ollama/blob/main/docs/modelfile.md).

!!! tip
    If you set `VISUAL_MODE` to `True`, make sure the `API_MODEL` supports visual inputs.

## Step 4
After configuring the `HOST_AGENT` and `APP_AGENT` with the Ollama API, you can start using UFO to interact with the Ollama API for various tasks on Windows OS. Please refer to the [Quick Start Guide](../getting_started/quick_start.md) for more details on how to get started with UFO.



