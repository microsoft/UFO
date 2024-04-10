### NOTE
The lite version of the prompt is not fully optimized. To achieve better results, it is recommended that users adjust the prompt according to performance!!!
### If you use QWEN as the Agent

1. QWen (Tongyi Qianwen) is a LLM developed by Alibaba. Go to [QWen](https://dashscope.aliyun.com/) and register an account and get the API key. More details can be found [here](https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key?spm=a2c4g.11186623.0.0.7b5749d72j3SYU) (in Chinese).
2. Install the required packages dashscope or run the `setup.py` with `-qwen` options.
```bash
pip install dashscope
```
3. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "Qwen" ,
    "API_KEY": "YOUR_KEY",  
    "API_MODEL": "YOUR_MODEL"
}
```
NOTE: `API_MODEL` is the model name of QWen LLM API. 
You can find the model name in the [QWen LLM model list](https://help.aliyun.com/zh/dashscope/developer-reference/model-square/?spm=a2c4g.11186623.0.0.35a36ffdt97ljI).

### If you use Ollama as the Agent
1. Go to [Ollama](https://github.com/jmorganca/ollama) and follow the instructions to serve a LLM model on your local environment.
We provide a short example to show how to configure the ollama in the following, which might change if ollama makes updates.

```bash title="install ollama and serve LLMs in local" showLineNumbers
## Install ollama on Linux & WSL2 or run the `setup.py` with `-ollama` options
curl https://ollama.ai/install.sh | sh
## Run the serving
ollama serve
```
Open another terminal and run:
```bash
ollama run YOUR_MODEL
```

***info***
When serving LLMs via Ollama, it will by default start a server at `http://localhost:11434`, which will later be used as the API base in `config.yaml`.


2. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "Ollama" ,
    "API_BASE": "YOUR_ENDPOINT",   
    "API_MODEL": "YOUR_MODEL"
}
```
NOTE: `API_BASE` is the URL started in the Ollama LLM server and `API_MODEL` is the model name of Ollama LLM, it should be same as the one you served before. In addition, due to model limitations, you can use lite version of prompt to have a taste on UFO which can be configured in `config_dev.yaml`. Attention to the top ***note***.

#### If you use your custom model as the Agent
1. Start a server with your model, which will later be used as the API base in `config.yaml`.

2. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "custom_model" ,
    "API_BASE": "YOUR_ENDPOINT", 
    "API_KEY": "YOUR_KEY",  
    "API_MODEL": "YOUR_MODEL"
}
```

NOTE: You should create a new Python script <custom_model>.py in the ufo/llm folder like the format of the <placeholder>.py, which needs to inherit `BaseService` as the parent class, as well as the `__init__` and `chat_completion` methods. At the same time, you need to add the dynamic import of your file in the `get_service` method of `BaseService`.