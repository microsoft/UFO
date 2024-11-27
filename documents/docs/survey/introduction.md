
# Large Language Model-Brained GUI Agents: A Survey

[![Agent-Powered](https://img.shields.io/badge/Agent-Powered-0ABAB5?logo=robot-framework&logoColor=white)](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)
[![Paper](https://img.shields.io/badge/Paper-arXiv%3A2202.00000-B31B1B.svg)](https://arxiv.org/) 
[![Website](https://img.shields.io/badge/Website-Searchable%20List-blue.svg)](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)
[![github](https://img.shields.io/github/stars/microsoft/UFO)](https://github.com/microsoft/UFO)&ensp;

Welcome to the repository accompanying our survey paper on **Large Language Model-Brained GUI Agents**. This repository contains the code for the searchable paper page and the assets used in the paper. **LLM-Brained GUI Agents** are:

!!! abstract "Definition"
    Intelligent agents that operate within GUI environments, leveraging Large Language Models (LLMs) as their core inference and cognitive engine to generate, plan, and execute actions in a flexible and adaptive manner.

## 📖 Read the [Paper:](https://arxiv.org/)

<h1 align="center">
    <img src="/img/gui_agent.png"/> 
</h1>

---

## 🔍 Explore the **[Searchable Paper Page](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)**

<h1 align="center">
    <img src="/img/webpage.png"/> 
</h1>


The **[Searchable Paper Page](https://vyokky.github.io/LLM-Brained-GUI-Agents-Survey/)** is a web-based interface that allows you to search and filter through the papers in our survey. You can also view the papers by category, platform, and date.

---


## 🙌 Contributing

🤝**Contributions Welcome!**

We encourage the community to contribute to this repository. If you have suggestions for new papers, resources, or improvements, please open an issue or submit a pull request.

To contribute, follow these steps:

1. Go to the `survey` (important) branch of this repository.

1. Find the `documents/docs/survey/data/*.json` file which matches the category of the paper you want to add in the `/data` folder. It should be either `survey`, `framework`, `dataset`, `model`, `benchmark`, `gui-testing`, or `visual-assistant`.

    - `survey`: Papers that provide a survey of the LLM-Powered GUI Agents.
    - `framework`: Papers that introduce a new framework or architecture for LLM-Powered GUI Agents.
    - `dataset`: Papers that introduce a new dataset for optimizing models for LLM-Powered GUI Agents.
    - `model`: Papers that introduce a new optimized model for LLM-Powered GUI Agents.
    - `benchmark`: Papers that introduce a new benchmark for evaluating LLM-Powered GUI Agents.
    - `gui-testing`: Papers that uses LLM-powered agents for GUI testing. It is mainly focused on the testing applications aspect.
    - `visual-assistant`: Papers, open-source projects, or products that use LLM-powered agents for visual assistance, such as voice assistants, produtized web agents, etc. It is mainly focused on the applications aspect.

2. In the corresponding json file, add the paper details in the following format to the existing list of papers:

```json
{
    "Name": "Paper Title",
    "Platform": "Device or OS Platform, e.g. Mobile, Web, Desktop, Android, Windows, etc.",
    "Date": "Month Year",
    "Paper_Url": "The paper link of the paper",
    "Highlight": "A brief highlight of the paper, up to 2 sentences.",
    "Code_Url": "The project or code link of the paper",
}
```

---

## 📝 Related Repositories

Here are some other repositories that you might find useful:

- [GUI-Agents-Paper-List](https://github.com/boyugou/GUI-Agents-Paper-List)
- [Awesome-GUI-Agent](https://github.com/showlab/Awesome-GUI-Agent/tree/main)
- [Awesome-LLM-based-Web-Agent-and-Tools](https://github.com/albzni/Awesome-LLM-based-Web-Agent-and-Tools)
- [awesome-ui-agents](https://github.com/opendilab/awesome-ui-agents/)

---

## 🫶 Support Us

⭐ **If you find this repository helpful, please condiser to cite our paper and give it a star!**

---