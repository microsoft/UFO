# Introduction

This repository contains the implementation of the **Data Collection** process for training the **Large Action Models** (LAMs) in the paper of [Large Action Models: From Inception to Implementation](https://arxiv.org/abs/2412.10047). The **Data Collection** process is designed to streamline task processing, ensuring that all necessary steps are seamlessly integrated from initialization to execution. This module is part of the [**UFO**](https://arxiv.org/abs/2402.07939) project.

# Dataflow

Dataflow uses UFO to implement `instantiation`, `execution`, and `dataflow` for a given task, with options for batch processing and single processing.

1. **[Instantiation](./instantiation.md)**:  Instantiation refers to the process of setting up and preparing a task for execution. This step typically involves `choosing template`, `prefill` and `filter`.
2. **[Execution](./execution.md)**: Execution is the actual process of running the task. This step involves carrying out the actions or operations specified by the `Instantiation`. And after execution, an evaluate agent will evaluate the quality of the whole execution process.
3. **Dataflow**: Dataflow is the overarching process that combines **instantiation** and **execution** into a single pipeline. It provides an end-to-end solution for processing tasks, ensuring that all necessary steps (from initialization to execution) are seamlessly integrated.

You can use `instantiation` and `execution` independently if you only need to perform one specific part of the process. When both steps are required for a task, the `dataflow` process streamlines them, allowing you to execute tasks from start to finish in a single pipeline.

The overall processing of dataflow is as below. Given a task-plan data, the LLMwill instantiatie the task-action data, including choosing template, prefill, filter.

<h1 align="center">
    <img src="../../img/overview.png">
</h1>

## How To Use

### 1. Install Packages

You should install the necessary packages in the UFO root folder:

```bash
pip install -r requirements.txt
```

### 2. Configure the LLMs

Before running dataflow, you need to provide your LLM configurations **individually for PrefillAgent and FilterAgent**. You can create your own config file `dataflow/config/config.yaml`, by copying the `dataflow/config/config.yaml.template` and editing config for **PREFILL_AGENT** and **FILTER_AGENT** as follows:

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

You can also non-visial model (e.g., GPT-4) for each agent, by setting `VISUAL_MODE: False` and proper `API_MODEL` (openai) and `API_DEPLOYMENT_ID` (aoai).

#### Non-Visual Model Configuration

You can utilize non-visual models (e.g., GPT-4) for each agent by configuring the following settings in the `config.yaml` file:

- ``VISUAL_MODE: False # To enable non-visual mode.``
- Specify the appropriate `API_MODEL` (OpenAI) and `API_DEPLOYMENT_ID` (AOAI) for each agent.

Ensure you configure these settings accurately to leverage non-visual models effectively.

#### Other Configurations

`config_dev.yaml` specifies the paths of relevant files and contains default settings. The match strategy for the window match and control filter supports options:  `'contains'`, `'fuzzy'`, and `'regex'`, allowing flexible matching strategy for users. The `MAX_STEPS` is the max step for the execute_flow, which can be set by users.

!!!note
    The specific implementation and invocation method of the matching strategy can refer to [windows_app_env](./windows_app_env.md).

!!!note
    **BE CAREFUL!** If you are using GitHub or other open-source tools, do not expose your `config.yaml` online, as it contains your private keys.

### 3. Prepare Files

Certain files need to be prepared before running the task.

#### 3.1. Tasks as JSON

The tasks that need to be instantiated should be organized in a folder of JSON files, with the default folder path set to dataflow `/tasks `. This path can be changed in the `dataflow/config/config.yaml` file, or you can specify it in the terminal, as mentioned in **4. Start Running**. For example, a task stored in `dataflow/tasks/prefill/` may look like this:

```json
{
    // The app you want to use
    "app": "word",
    // A unique ID to distinguish different tasks 
    "unique_id": "1",
    // The task and steps to be instantiated
    "task": "Type 'hello' and set the font type to Arial",
    "refined_steps": [
        "Type 'hello'",
        "Set the font to Arial"
    ]
}
```

#### 3.2. Templates and Descriptions

You should place an app file as a reference for instantiation in a folder named after the app.

For example, if you have `template1.docx` for Word, it should be located at `dataflow/templates/word/template1.docx`.

Additionally, for each app folder, there should be a `description.json` file located at `dataflow/templates/word/description.json`, which describes each template file in detail. It may look like this:

```json
{
    "template1.docx": "A document with a rectangle shape",
    "template2.docx": "A document with a line of text"
}
```

If a `description.json` file is not present, one template file will be selected at random.

#### 3.3. Final Structure

Ensure the following files are in place:

- [X] JSON files to be instantiated
- [X] Templates as references for instantiation
- [X] Description file in JSON format

The structure of the files can be:

```txt
dataflow/
|
├── tasks
│   └── prefill
│       ├── bulleted.json
│       ├── delete.json
│       ├── draw.json
│       ├── macro.json
│       └── rotate.json
├── templates
│   └── word
│       ├── description.json
│       ├── template1.docx
│       ├── template2.docx
│       ├── template3.docx
│       ├── template4.docx
│       ├── template5.docx
│       ├── template6.docx
│       └── template7.docx
└── ...
```

### 4. Start Running

After finishing the previous steps, you can use the following commands in the command line. We provide single / batch process, for which you need to give the single file path / folder path. Determine the type of path provided by the user and automatically decide whether to process a single task or batch tasks.

Also, you can choose to use `instantiation` / `execution` sections individually, or use them as a whole section, which is named as `dataflow`.

The default task hub is set to be `"TASKS_HUB"` in `dataflow/config_dev.yaml`.

* Dataflow Task:

```bash
python -m dataflow -dataflow --task_path path_to_task_file
```

* Instantiation Task:

```bash
python -m dataflow -instantiation --task_path path_to_task_file
```

* Execution Task:

```bash
python -m dataflow -execution --task_path path_to_task_file
```

!!! note

    1. Users should be careful to save the original files while using this project; otherwise, the files will be closed when the app is shut down.
    2. After starting the project, users should not close the app window while the program is taking screenshots.

## Workflow

### Instantiation

There are three key steps in the instantiation process:

1. `Choose a template` file according to the specified app and instruction.
2. `Prefill` the task using the current screenshot.
3. `Filter` the established task.

Given the initial task, the dataflow first choose a template (`Phase 1`), the prefill the initial task based on word envrionment to obtain task-action data (`Phase 2`). Finnally, it will filter the established task to evaluate the quality of task-action data. (`Phase 3`)

!!! note
    The more detailed code design documentation for instantiation can be found in [instantiation](./instantiation.md).

### Execution

The instantiated plans will be executed by a execute task. After execution, evalution agent will evaluation the quality of the entire execution process.

!!! note
    The more detailed code design documentation for execution can be found in [execution](./execution.md).

## Result

The results will be saved in the `results\` directory under `instantiation`, `execution`, and `dataflow`, and will be further stored in subdirectories based on the execution outcomes.

!!! note
    The more detailed information of result can be found in [result](./result.md).

## Quick Start

We prepare two cases to show the dataflow, which can be found in `dataflow\tasks\prefill`. So after installing required packages, you can type the following command in the command line:

```
python -m dataflow -dataflow
```

And you can see the hints showing in the terminal, which means the dataflow is working.

### Structure of related files

After the two tasks are finished, the task and output files would appear as follows:

```bash
UFO/
├── dataflow/
│   └── results/
│       ├── saved_document/       	# Directory for saved documents
│       │   ├── bulleted.docx     	# Result of the "bulleted" task
│       │   └── rotate.docx       	# Result of the "rotate" task
│       ├── dataflow/            		 # Dataflow results directory
│       │   ├── execution_pass/   	# Successfully executed tasks
│       │   │   ├── bulleted.json 	# Execution result for the "bulleted" task
│       │   │   ├── rotate.json  	 # Execution result for the "rotate" task
│       │   │   └── ...
└── ...
```

The specific results can be referenced in the [result](./result.md) in JSON format along with example data.

### Log files

The corresponding logs can be found in the directories `logs/bulleted` and `logs/rotate`, as shown below. Detailed logs for each workflow are recorded, capturing every step of the execution process.

<h1 align="center">
    <img src="../../img/result_example.png"/> 
</h1>

# Reference

### AppEnum

::: data_flow_controller.AppEnum

### TaskObject

::: data_flow_controller.TaskObject

### DataFlowController

::: data_flow_controller.DataFlowController
