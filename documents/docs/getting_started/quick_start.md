# Quick Start

### 🛠️ Step 1: Installation
UFO requires **Python >= 3.10** running on **Windows OS >= 10**. It can be installed by running the following command:
```powershell
# [optional to create conda environment]
# conda create -n ufo python=3.10
# conda activate ufo

# clone the repository
git clone https://github.com/microsoft/UFO.git
cd UFO
# install the requirements
pip install -r requirements.txt
# If you want to use the Qwen as your LLMs, uncomment the related libs.
```

### ⚙️ Step 2: Configure the LLMs
Before running UFO, you need to provide your LLM configurations **individually for HostAgent and AppAgent**. You can create your own config file `ufo/config/config.yaml`, by copying the `ufo/config/config.yaml.template` and editing config for **HOST_AGENT** and **APP_AGENT** as follows: 

```powershell
copy ufo\config\config.yaml.template ufo\config\config.yaml
notepad ufo\config\config.yaml   # paste your key & endpoint
```

#### OpenAI
```bash
VISUAL_MODE: True, # Whether to use the visual mode
API_TYPE: "openai" , # The API type, "openai" for the OpenAI API.  
API_BASE: "https://api.openai.com/v1/chat/completions", # The the OpenAI API endpoint.
API_KEY: "sk-",  # The OpenAI API key, begin with sk-
API_VERSION: "2024-02-15-preview", # "2024-02-15-preview" by default
API_MODEL: "gpt-4-vision-preview",  # The OpenAI model
```


#### Azure OpenAI (AOAI)
```bash
VISUAL_MODE: True, # Whether to use the visual mode
API_TYPE: "aoai" , # The API type, "aoai" for the Azure OpenAI.  
API_BASE: "YOUR_ENDPOINT", #  The AOAI API address. Format: https://{your-resource-name}.openai.azure.com
API_KEY: "YOUR_KEY",  # The aoai API key
API_VERSION: "2024-02-15-preview", # "2024-02-15-preview" by default
API_MODEL: "gpt-4-vision-preview",  # The OpenAI model
API_DEPLOYMENT_ID: "YOUR_AOAI_DEPLOYMENT", # The deployment id for the AOAI API
```
You can also non-visial model (e.g., GPT-4) for each agent, by setting `VISUAL_MODE: False` and proper `API_MODEL` (openai) and `API_DEPLOYMENT_ID` (aoai). You can also optionally set an backup LLM engine in the field of `BACKUP_AGENT` if the above engines failed during the inference. The `API_MODEL` can be any GPT models that can accept images as input.



####  Non-Visual Model Configuration
You can utilize non-visual models (e.g., GPT-4) for each agent by configuring the following settings in the `config.yaml` file:

!!! info
    - ```VISUAL_MODE: False```
    - Specify the appropriate `API_MODEL` (OpenAI) and `API_DEPLOYMENT_ID` (AOAI) for each agent.

Optionally, you can set a backup language model (LLM) engine in the `BACKUP_AGENT` field to handle cases where the primary engines fail during inference. Ensure you configure these settings accurately to leverage non-visual models effectively.

!!! note
    UFO also supports other LLMs and advanced configurations, such as customize your own model, please check the [documents](../supported_models/overview.md) for more details. Because of the limitations of model input, a lite version of the prompt is provided to allow users to experience it, which is configured in `config_dev.yaml`.

### 📔 Step 3: Additional Setting for RAG (optional).
If you want to enhance UFO's ability with external knowledge, you can optionally configure it with an external database for retrieval augmented generation (RAG) in the `ufo/config/config.yaml` file. 

We provide the following options for RAG to enhance UFO's capabilities:

- **[Offline Help Document](../advanced_usage/reinforce_appagent/learning_from_help_document.md)**: Enable UFO to retrieve information from offline help documents.

- **[Online Bing Search Engine](../advanced_usage/reinforce_appagent/learning_from_bing_search.md)**: Enhance UFO's capabilities by utilizing the most up-to-date online search results.

- **[Self-Experience](../advanced_usage/reinforce_appagent/experience_learning.md)**: Save task completion trajectories into UFO's memory for future reference.

- **[User-Demonstration](../advanced_usage/reinforce_appagent/learning_from_demonstration.md)**: Boost UFO's capabilities through user demonstration.

!!!tip
    Consult their respective documentation for more information on how to configure these settings.

### 🎉 Step 4: Start UFO

#### ⌨️ You can execute the following on your Windows command Line (CLI):

```bash
# assume you are in the cloned UFO folder
python -m ufo --task <your_task_name>
```

This will start the UFO process and you can interact with it through the command line interface. 
If everything goes well, you will see the following message:

```bash
Welcome to use UFO🛸, A UI-focused Agent for Windows OS Interaction. 
 _   _  _____   ___
| | | ||  ___| / _ \
| | | || |_   | | | |
| |_| ||  _|  | |_| |
 \___/ |_|     \___/
Please enter your request to be completed🛸:
```

Alternatively, you can also directly invoke UFO with a specific task and request by using the following command:

```powershell
python -m ufo --task <your_task_name> -r "<your_request>"
```


###  Step 5 🎥: Execution Logs 

You can find the screenshots taken and request & response logs in the following folder:
```
./ufo/logs/<your_task_name>/
```
You may use them to debug, replay, or analyze the agent output.


!!! note
    The LLM accepts screenshots of your desktop and application GUI as input. Please ensure that no sensitive or confidential information is visible or captured during the execution process. For further information, refer to [DISCLAIMER.md](https://github.com/microsoft/UFO/blob/vyokky/dev/DISCLAIMER.md).