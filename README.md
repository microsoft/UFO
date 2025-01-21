<h1 align="center">
    <b>UFO</b> <img src="./assets/ufo_blue.png" alt="UFO Image" width="40">: A <b>U</b>I-<b>Fo</b>cused Agent for Windows OS Interaction
</h1>


<div align="center">

[![arxiv](https://img.shields.io/badge/Paper-arXiv:202402.07939-b31b1b.svg)](https://arxiv.org/abs/2402.07939)&ensp;
![Python Version](https://img.shields.io/badge/Python-3776AB?&logo=python&logoColor=white-blue&label=3.10%20%7C%203.11)&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)&ensp;
[![Documentation](https://img.shields.io/badge/Documentation-%230ABAB5?style=flat&logo=readthedocs&logoColor=black)](https://microsoft.github.io/UFO/)&ensp;
[![YouTube](https://img.shields.io/badge/YouTube-white?logo=youtube&logoColor=%23FF0000)](https://www.youtube.com/watch?v=QT_OhygMVXU)&ensp;
<!-- [![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/UFO_Agent)](https://twitter.com/intent/follow?screen_name=UFO_Agent) -->
<!-- ![Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)&ensp; -->

</div>

**UFO** is a **UI-Focused** multi-agent framework to fulfill user requests on **Windows OS** by seamlessly navigating and operating within individual or spanning multiple applications.

<h1 align="center">
    <img src="./assets/overview_n.png"/> 
</h1>


## 🕌 Framework
<b>UFO</b> <img src="./assets/ufo_blue.png" alt="UFO Image" width="24"> operates as a multi-agent framework, encompassing:
- <b>HostAgent 🤖</b>, tasked with choosing an application for fulfilling user requests. This agent may also switch to a different application when a request spans multiple applications, and the task is partially completed in the preceding application. 
- <b>AppAgent 👾</b>, responsible for iteratively executing actions on the selected applications until the task is successfully concluded within a specific application. 
- <b>Application Automator 🎮</b>, is tasked with translating actions from HostAgent and AppAgent into interactions with the application and through UI controls, native APIs or AI tools. Check out more details [here](https://microsoft.github.io/UFO/automator/overview/).

Both agents leverage the multi-modal capabilities of GPT-4V(o) to comprehend the application UI and fulfill the user's request. For more details, please consult our [technical report](https://arxiv.org/abs/2402.07939) and [documentation](https://microsoft.github.io/UFO/).
<h1 align="center">
    <img src="./assets/framework_v2.png"/> 
</h1>


## 📢 News
- 📅 2025-01-21: Version **v1.2.1** Released! We’re excited to announce the release of **v1.2.1**! 🎉 This update includes:
    1. **Bug Fixes**: Resolved issues in `requirements.txt` for smoother setup.
    2. **Multi-Action Mode**: Introducing a powerful new feature to execute **multiple actions** in a single inference step! Enable this mode by setting `ACTION_SEQUENCE=True` in `config_dev.yaml` and enjoy a more efficient workflow.
- 📅 2024-12-13: We have a **New Release for v1.2.0!**! Checkout our new features and improvements:
    1. **Large Action Model (LAM) Data Collection:** We have released the code and sample data for Large Action Model (LAM) data collection with UFO! Please checkout our [new paper](https://arxiv.org/abs/2412.10047), [code](dataflow/README.md) and [documentation](https://microsoft.github.io/UFO/dataflow/overview/) for more details.    
    2. **Bash Command Support:** HostAgent also support bash command now!
    3. **Bug Fixes:** We have fixed some bugs, error handling, and improved the overall performance.
- 📅 2024-09-08: We have a **New Release for v1.1.0!**, to allows UFO to click on any region of the application and reduces its latency by up tp 1/3!
- 📅 2024-07-06: We have a **New Release for v1.0.0!**.  You can check out our [documentation](https://microsoft.github.io/UFO/). We welcome your contributions and feedback!
- 📅 2024-06-28: We are thrilled to announce that our official introduction video is now available on [YouTube](https://www.youtube.com/watch?v=QT_OhygMVXU)!
<!-- - 📅 2024-06-25: **New Release for v0.2.1!**  We are excited to announce the release of version 0.2.1! This update includes several new features and improvements:
    1. **HostAgent Refactor:** We've refactored the HostAgent to enhance its efficiency in managing AppAgents within UFO.
    2. **Evaluation Agent:** Introducing an evaluation agent that assesses task completion and provides real-time feedback.
    3. **Google Gemini && Claude Support:** UFO now supports Google Gemini and Cluade as the inference engine. Refer to our detailed guide in [Gemini documentation](https://microsoft.github.io/UFO/supported_models/gemini/) or [Claude documentation](https://microsoft.github.io/UFO/supported_models/claude/).
    4. **Customized User Agents:** Users can now create customized agents by simply answering a few questions.
- 📅 2024-05-21: We have reached 5K stars!✨
- 📅 2024-05-08: **New Release for v0.1.1!** We've made some significant updates! Previously known as AppAgent and ActAgent, we've rebranded them to HostAgent and AppAgent to better align with their functionalities. Explore the latest enhancements:
    1. **Learning from Human Demonstration:** UFO now supports learning from human demonstration! Utilize the [Windows Step Recorder](https://support.microsoft.com/en-us/windows/record-steps-to-reproduce-a-problem-46582a9b-620f-2e36-00c9-04e25d784e47) to record your steps and demonstrate them for UFO. Refer to our detailed guide in [README.md](https://microsoft.github.io/UFO/creating_app_agent/demonstration_provision/) for more information.
    2. **Win32 Support:** We've incorporated support for [Win32](https://learn.microsoft.com/en-us/windows/win32/controls/window-controls) as a control backend, enhancing our UI automation capabilities.
    3. **Extended Application Interaction:** UFO now goes beyond UI controls, allowing interaction with your application through keyboard inputs and native APIs! Presently, we support Word ([examples](/ufo/prompts/apps/word/api.yaml)), with more to come soon. Customize and build your own interactions.
    4. **Control Filtering:** Streamline LLM's action process by using control filters to remove irrelevant control items. Enable them in [config_dev.yaml](/ufo/config/config_dev.yaml) under the `control filtering` section at the bottom.
- 📅 2024-03-25: **New Release for v0.0.1!** Check out our exciting new features.
    1. We now support creating your help documents for each Windows application to become an app expert. Check the [documentation](https://microsoft.github.io/UFO/creating_app_agent/help_document_provision/) for more details!
    2. UFO now supports RAG from offline documents and online Bing search.
    3. You can save the task completion trajectory into its memory for UFO's reference, improving its future success rate!
    4. You can customize different GPT models for HostAgent and AppAgent. Text-only models (e.g., GPT-4) are now supported! -->
- 📅 ...
- 📅 2024-02-14: Our [technical report](https://arxiv.org/abs/2402.07939) is online!
- 📅 2024-02-10: UFO is released on GitHub🎈. Happy Chinese New year🐉!


## 🌐 Media Coverage 

UFO sightings have garnered attention from various media outlets, including:
- [Microsoft's UFO abducts traditional user interfaces for a smarter Windows experience](https://the-decoder.com/microsofts-ufo-abducts-traditional-user-interfaces-for-a-smarter-windows-experience/)
- [🚀 UFO & GPT-4-V: Sit back and relax, mientras GPT lo hace todo🌌](https://www.linkedin.com/posts/gutierrezfrancois_ai-ufo-microsoft-activity-7176819900399652865-pLoo?utm_source=share&utm_medium=member_desktop)
- [The AI PC - The Future of Computers? - Microsoft UFO](https://www.youtube.com/watch?v=1k4LcffCq3E)
- [下一代Windows系统曝光：基于GPT-4V，Agent跨应用调度，代号UFO](https://baijiahao.baidu.com/s?id=1790938358152188625&wfr=spider&for=pc)
- [下一代智能版 Windows 要来了？微软推出首个 Windows Agent，命名为 UFO！](https://blog.csdn.net/csdnnews/article/details/136161570)
- [Microsoft発のオープンソース版「UFO」登場！　Windowsを自動操縦するAIエージェントを試す](https://internet.watch.impress.co.jp/docs/column/shimizu/1570581.html)
- ...

These sources provide insights into the evolving landscape of technology and the implications of UFO phenomena on various platforms.


## 💥 Highlights

- [x] **First Windows Agent** - UFO is the pioneering agent framework capable of translating user requests in natural language into actionable operations on Windows OS.
- [x] **Agent as an Expert** - UFO is enhanced by Retrieval Augmented Generation (RAG) from heterogeneous sources, including offline help documents, online search engines, and human demonstrations, making the agent an application "expert".
- [x] **Rich Skill Set** - UFO is equipped with a diverse set of skills to support comprehensive automation, such as mouse, keyboard, native API, and "Copilot".
- [x] **Interactive Mode** - UFO facilitates multiple sub-requests from users within the same session, enabling the seamless completion of complex tasks.
- [x] **Agent Customization** - UFO allows users to customize their own agents by providing additional information. The agent will proactively query users for details when necessary to better tailor its behavior.
- [x] **Scalable AppAgent Creation** - UFO offers extensibility, allowing users and app developers to create their own AppAgents in an easy and scalable way.


## ✨ Getting Started


### 🛠️ Step 1: Installation
UFO requires **Python >= 3.10** running on **Windows OS >= 10**. It can be installed by running the following command:
```bash
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


#### OpenAI
```bash
VISUAL_MODE: True, # Whether to use the visual mode
API_TYPE: "openai" , # The API type, "openai" for the OpenAI API.  
API_BASE: "https://api.openai.com/v1/chat/completions", # The the OpenAI API endpoint.
API_KEY: "sk-",  # The OpenAI API key, begin with sk-
API_VERSION: "2024-02-15-preview", # "2024-02-15-preview" by default
API_MODEL: "gpt-4-vision-preview",  # The only OpenAI model
```

#### Azure OpenAI (AOAI)
```bash
VISUAL_MODE: True, # Whether to use the visual mode
API_TYPE: "aoai" , # The API type, "aoai" for the Azure OpenAI.  
API_BASE: "YOUR_ENDPOINT", #  The AOAI API address. Format: https://{your-resource-name}.openai.azure.com
API_KEY: "YOUR_KEY",  # The aoai API key
API_VERSION: "2024-02-15-preview", # "2024-02-15-preview" by default
API_MODEL: "gpt-4-vision-preview",  # The only OpenAI model
API_DEPLOYMENT_ID: "YOUR_AOAI_DEPLOYMENT", # The deployment id for the AOAI API
```
You can also non-visial model (e.g., GPT-4) for each agent, by setting `VISUAL_MODE: False` and proper `API_MODEL` (openai) and `API_DEPLOYMENT_ID` (aoai). You can also optionally set an backup LLM engine in the field of `BACKUP_AGENT` if the above engines failed during the inference.


####  Non-Visual Model Configuration
You can utilize non-visual models (e.g., GPT-4) for each agent by configuring the following settings in the `config.yaml` file:

- ```VISUAL_MODE: False # To enable non-visual mode.```
- Specify the appropriate `API_MODEL` (OpenAI) and `API_DEPLOYMENT_ID` (AOAI) for each agent.

Optionally, you can set a backup language model (LLM) engine in the `BACKUP_AGENT` field to handle cases where the primary engines fail during inference. Ensure you configure these settings accurately to leverage non-visual models effectively.

#### NOTE 💡 
UFO also supports other LLMs and advanced configurations, such as customize your own model, please check the [documents](https://microsoft.github.io/UFO/supported_models/overview/) for more details. Because of the limitations of model input, a lite version of the prompt is provided to allow users to experience it, which is configured in `config_dev.yaml`.

### 📔 Step 3: Additional Setting for RAG (optional).
If you want to enhance UFO's ability with external knowledge, you can optionally configure it with an external database for retrieval augmented generation (RAG) in the `ufo/config/config.yaml` file. 

We provide the following options for RAG to enhance UFO's capabilities:
- [Offline Help Document](https://microsoft.github.io/UFO/advanced_usage/reinforce_appagent/learning_from_help_document/) Enable UFO to retrieve information from offline help documents.
- [Online Bing Search Engine](https://microsoft.github.io/UFO/advanced_usage/reinforce_appagent/learning_from_bing_search/): Enhance UFO's capabilities by utilizing the most up-to-date online search results.
- [Self-Experience](https://microsoft.github.io/UFO/advanced_usage/reinforce_appagent/experience_learning/): Save task completion trajectories into UFO's memory for future reference.
- [User-Demonstration](https://microsoft.github.io/UFO/advanced_usage/reinforce_appagent/learning_from_demonstration/): Boost UFO's capabilities through user demonstration.

Consult their respective documentation for more information on how to configure these settings.

<!-- #### RAG from Offline Help Document
Before enabling this function, you need to create an offline indexer for your help document. Please refer to the [README](./learner/README.md) to learn how to create an offline vectored database for retrieval. You can enable this function by setting the following configuration:
```bash
## RAG Configuration for the offline docs
RAG_OFFLINE_DOCS: True  # Whether to use the offline RAG.
RAG_OFFLINE_DOCS_RETRIEVED_TOPK: 1  # The topk for the offline retrieved documents
```
Adjust `RAG_OFFLINE_DOCS_RETRIEVED_TOPK` to optimize performance.


####  RAG from Online Bing Search Engine
Enhance UFO's ability by utilizing the most up-to-date online search results! To use this function, you need to obtain a Bing search API key. Activate this feature by setting the following configuration:
```bash
## RAG Configuration for the Bing search
BING_API_KEY: "YOUR_BING_SEARCH_API_KEY"  # The Bing search API key
RAG_ONLINE_SEARCH: True  # Whether to use the online search for the RAG.
RAG_ONLINE_SEARCH_TOPK: 5  # The topk for the online search
RAG_ONLINE_RETRIEVED_TOPK: 1 # The topk for the online retrieved documents
```
Adjust `RAG_ONLINE_SEARCH_TOPK` and `RAG_ONLINE_RETRIEVED_TOPK` to get better performance.


#### RAG from Self-Demonstration
Save task completion trajectories into UFO's memory for future reference. This can improve its future success rates based on its previous experiences!

After completing a task, you'll see the following message:
```
Would you like to save the current conversation flow for future reference by the agent?
[Y] for yes, any other key for no.
```
Press `Y` to save it into its memory and enable memory retrieval via the following configuration:
```bash
## RAG Configuration for experience
RAG_EXPERIENCE: True  # Whether to use the RAG from its self-experience.
RAG_EXPERIENCE_RETRIEVED_TOPK: 5  # The topk for the offline retrieved documents
```

#### RAG from User-Demonstration
Boost UFO's capabilities through user demonstration! Utilize Microsoft Steps Recorder to record step-by-step processes for achieving specific tasks. With a simple command processed by the record_processor (refer to the [README](./record_processor/README.md)), UFO can store these trajectories in its memory for future reference, enhancing its learning from user interactions.

You can enable this function by setting the following configuration:
```bash
## RAG Configuration for demonstration
RAG_DEMONSTRATION: True  # Whether to use the RAG from its user demonstration.
RAG_DEMONSTRATION_RETRIEVED_TOPK: 5  # The topk for the demonstration examples.
``` -->


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
#### ⚠️Reminder:  ####
- Before UFO executing your request, please make sure the targeted applications are active on the system.
- The GPT-V accepts screenshots of your desktop and application GUI as input. Please ensure that no sensitive or confidential information is visible or captured during the execution process. For further information, refer to [DISCLAIMER.md](./DISCLAIMER.md).


###  Step 5 🎥: Execution Logs 

You can find the screenshots taken and request & response logs in the following folder:
```
./ufo/logs/<your_task_name>/
```
You may use them to debug, replay, or analyze the agent output.


## ❓Get help 
* Please first check our our documentation [here](https://microsoft.github.io/UFO/).
* ❔GitHub Issues (prefered)
* For other communications, please contact [ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com).
---


<!-- ## 🎬 Demo Examples

We present two demo videos that complete user request on Windows OS using UFO. For more case study, please consult our [technical report](https://arxiv.org/abs/2402.07939).

#### 1️⃣🗑️ Example 1: Deleting all notes on a PowerPoint presentation.
In this example, we will demonstrate how to efficiently use UFO to delete all notes on a PowerPoint presentation with just a few simple steps. Explore this functionality to enhance your productivity and work smarter, not harder!


https://github.com/microsoft/UFO/assets/11352048/cf60c643-04f7-4180-9a55-5fb240627834



#### 2️⃣📧 Example 2: Composing an email using text from multiple sources.
In this example, we will demonstrate how to utilize UFO to extract text from Word documents, describe an image, compose an email, and send it seamlessly. Enjoy the versatility and efficiency of cross-application experiences with UFO!


https://github.com/microsoft/UFO/assets/11352048/aa41ad47-fae7-4334-8e0b-ba71c4fc32e0 -->





## 📊 Evaluation

Please consult the [WindowsBench](https://arxiv.org/pdf/2402.07939.pdf) provided in Section A of the Appendix within our technical report. Here are some tips (and requirements) to aid in completing your request:

- Prior to UFO execution of your request, ensure that the targeted application is active (though it may be minimized).
- Please note that the output of GPT-V may not consistently align with the same request. If unsuccessful with your initial attempt, consider trying again.



## 📚 Citation
Our technical report paper can be found [here](https://arxiv.org/abs/2402.07939). Note that previous AppAgent and ActAgent in the paper are renamed to HostAgent and AppAgent in the code base to better reflect their functions.
If you use UFO in your research, please cite our paper:
```
@article{ufo,
  title={{UFO: A UI-Focused Agent for Windows OS Interaction}},
  author={Zhang, Chaoyun and Li, Liqun and He, Shilin and Zhang, Xu and Qiao, Bo and  Qin, Si and Ma, Minghua and Kang, Yu and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei and  Zhang, Qi},
  journal={arXiv preprint arXiv:2402.07939},
  year={2024}
}
```

## 📝 Todo List
- [x] RAG enhanced UFO.
- [x] Support more control using Win32 API.
- [x] [Documentation](https://microsoft.github.io/UFO/).
- [ ] Support local host GUI interaction model.
- [ ] Chatbox GUI for UFO.



## 🎨 Related Projects
1. If you're interested in data analytics agent frameworks, check out [TaskWeaver](https://github.com/microsoft/TaskWeaver?tab=readme-ov-file), a code-first LLM agent framework designed for seamlessly planning and executing data analytics tasks.

2. For more information on GUI agents, refer to our survey paper: [Large Language Model-Brained GUI Agents: A Survey](https://arxiv.org/abs/2411.18279). You can also explore the survey through:
- [Paper](https://arxiv.org/abs/2411.18279)
- [GitHub Repository](https://github.com/vyokky/LLM-Brained-GUI-Agents-Survey)
- [Searchable Website](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)

## ⚠️ Disclaimer
By choosing to run the provided code, you acknowledge and agree to the following terms and conditions regarding the functionality and data handling practices in [DISCLAIMER.md](./DISCLAIMER.md)


## <img src="./assets/ufo_blue.png" alt="logo" width="30"> Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
