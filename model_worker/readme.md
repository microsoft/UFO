### If you use QWEN as the Agent

1. QWen (Tongyi Qianwen) is a LLM developed by Alibaba. Go to [QWen](https://dashscope.aliyun.com/) and register an account and get the API key. More details can be found [here](https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key?spm=a2c4g.11186623.0.0.7b5749d72j3SYU) (in Chinese).
2. Install the required packages dashscope.
```bash
pip install dashscope
```
3. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "qwen" ,
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
## Install ollama on Linux & WSL2
curl https://ollama.ai/install.sh | sh
## Run the serving
ollama serve
```
Open another terminal and run:
```bash
ollama run YOUR_MODEL
```

:::info
When serving LLMs via Ollama, it will by default start a server at `http://localhost:11434`, which will later be used as the API base in `config.yaml`.
:::

2. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "ollama" ,
    "API_BASE": "http://localhost:11434", 
    "API_KEY": "ARBITRARY_STRING",  
    "API_MODEL": "YOUR_MODEL"
}
```
NOTE: `API_BASE` is the URL started in the Ollama LLM server and `API_MODEL` is the model name of Ollama LLM, it should be same as the one you served before. In addition, due to model limitations, you can use `use_lite` to enable a lightweight version of prompt to have a taste on UFO.

### If you use LLaVA-1.5 as the Agent

1. Please refer to the [LLaVA](https://github.com/haotian-liu/LLaVA) project to download and prepare the LLaVA-1.5 model, for example:

```bash
git clone https://github.com/haotian-liu/LLaVA.git
cd LLaVA
conda create -n llava python=3.10 -y
conda activate llava
pip install --upgrade pip  # enable PEP 660 support
pip install -e .
```

2. And start it with the following command (It will automatically download the pretained model):
```bash
python llava_worker.py --host 0.0.0.0 --port 11434 --model-path liuhaotian/llava-v1.5-13b
```

3. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "llava" ,
    "API_BASE": "http://localhost:11434", 
    "API_KEY": "ARBITRARY_STRING",  
    "API_MODEL": "YOUR_MODEL"
}
```

### If you use CogAgent as the Agent

1. Please refer to the [CogVLM](https://github.com/THUDM/CogVLM) project to download and prepare the CogAgent model. Download the sat version of the CogAgent weights `cogagent-chat.zip` from [here](https://huggingface.co/THUDM/CogAgent/tree/main), unzip it.

2. And start it with the following command:
```bash
python ./cogagent_model_worker.py --host 0.0.0.0  --port 11434 --from_pretrained "cogagent-chat" --bf16 --max_length 2048
```

3. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "cogagent" ,
    "API_BASE": "http://localhost:11434", 
    "API_KEY": "ARBITRARY_STRING",  
    "API_MODEL": "YOUR_MODEL"
}
```

Note: there is someting wrong with [SAT](https://github.com/THUDM/SwissArmyTransforme), when it fixed, the program will automatically download the pretained model.