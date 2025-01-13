<h1 align="center">
    Large Action Models: From Inception to Implementation
</h1>


<div align="center">

[![arxiv](https://img.shields.io/badge/Paper-arXiv:2412.10047-b31b1b.svg)](https://arxiv.org/abs/2412.10047)&ensp;
![Python Version](https://img.shields.io/badge/Python-3776AB?&logo=python&logoColor=white-blue&label=3.10%20%7C%203.11)&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)&ensp;
[![Documentation](https://img.shields.io/badge/Documentation-%230ABAB5?style=flat&logo=readthedocs&logoColor=black)](https://microsoft.github.io/UFO/dataflow/overview/)&ensp;
<!-- [![YouTube](https://img.shields.io/badge/YouTube-white?logo=youtube&logoColor=%23FF0000)](https://www.youtube.com/watch?v=QT_OhygMVXU)&ensp; -->
<!-- [![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/UFO_Agent)](https://twitter.com/intent/follow?screen_name=UFO_Agent) -->
<!-- ![Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)&ensp; -->

</div>


# Introduction

This repository contains the implementation of the **Data Collection** process for training the **Large Action Models** (LAMs) in the [**paper**](https://arxiv.org/abs/2412.10047). The **Data Collection** process is designed to streamline task processing, ensuring that all necessary steps are seamlessly integrated from initialization to execution. This module is part of the [**UFO**](https://arxiv.org/abs/2402.07939) project.

If you find this project useful, please give a star ⭐, and consider to cite our paper:

```bibtex
@misc{wang2024largeactionmodelsinception,
      title={Large Action Models: From Inception to Implementation}, 
      author={Lu Wang and Fangkai Yang and Chaoyun Zhang and Junting Lu and Jiaxu Qian and Shilin He and Pu Zhao and Bo Qiao and Ray Huang and Si Qin and Qisheng Su and Jiayi Ye and Yudi Zhang and Jian-Guang Lou and Qingwei Lin and Saravan Rajmohan and Dongmei Zhang and Qi Zhang},
      year={2024},
      eprint={2412.10047},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2412.10047}, 
}
```



# Dataflow

Dataflow uses UFO to implement `instantiation`, `execution`, and `dataflow` for a given task, with options for batch processing and single processing.

1. **Instantiation**:  Instantiation refers to the process of setting up and preparing a task for execution. This step typically involves `choosing template`, `prefill` and `filter`.
2. **Execution**: Execution is the actual process of running the task. This step involves carrying out the actions or operations specified by the `Instantiation`. And after execution, an evaluate agent will evaluate the quality of the whole execution process.
3. **Dataflow**: Dataflow is the overarching process that combines **instantiation** and **execution** into a single pipeline. It provides an end-to-end solution for processing tasks, ensuring that all necessary steps (from initialization to execution) are seamlessly integrated.

You can use `instantiation` and `execution` independently if you only need to perform one specific part of the process. When both steps are required for a task, the `dataflow` process streamlines them, allowing you to execute tasks from start to finish in a single pipeline.

The overall processing of dataflow is as below. Given a task-plan data, the LLMwill instantiatie the task-action data, including choosing template, prefill, filter.

<h1 align="center">
    <img src="../assets/dataflow/overview.png"/> 
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

#### NOTE 💡

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

You can use `"TEMPLATE_METHOD"` in `dataflow/config_dev.yaml` to choose `LLM` or `SemanticSimilarity` as the backend for the template selection function. If you choose `LLM`, since the visual version is being used, you need to manually generate screenshots in the `templates/"YOUR_APP"/images` directory, and the filenames should match the template name and the screenshots should in `PNG` format.

* Dataflow Task:

  ```bash
  python -m dataflow --dataflow --task_path path_to_task_file
  ```

* Instantiation Task:

  ```bash
  python -m dataflow --instantiation --task_path path_to_task_file
  ```
* Execution Task:

  ```bash
  python -m dataflow --execution --task_path path_to_task_file
  ```

## Workflow

### Instantiation

There are three key steps in the instantiation process:

1. `Choose a template` file according to the specified app and instruction.
2. `Prefill` the task using the current screenshot.
3. `Filter` the established task.

Given the initial task, the dataflow first choose a template (`Phase 1`), the prefill the initial task based on word envrionment to obtain task-action data (`Phase 2`). Finnally, it will filter the established task to evaluate the quality of task-action data.

<h1 align="center">
    <img src="../assets/dataflow/instantiation.png"/> 
</h1>

#### 1. Choose Template File

Templates for your app must be defined and described in `dataflow/templates/app`. For instance, if you want to instantiate tasks for the Word application, place the relevant `.docx` files in dataflow `/templates/word `, along with a `description.json` file.

The appropriate template will be selected based on how well its description matches the instruction.

#### 2. Prefill the Task

After selecting the template file, it will be opened, and a screenshot will be taken. If the template file is currently in use, errors may occur.

The screenshot will be sent to the action prefill agent, which will return a modified task.

#### 3. Filter Task

The completed task will be evaluated by a filter agent, which will assess it and provide feedback.

### Execution

The instantiated plans will be executed by a execute task. After execution, evalution agent will evaluation the quality of the entire execution process.

In this phase, given the task-action data, the execution process will match the real controller based on word environment and execute the plan step by step.

<h1 align="center">
    <img src="../assets/dataflow/execution.png"/> 
</h1>


## Result

The structure of the results of the task is as below:

```txt
UFO/
├── dataflow/                       # Root folder for dataflow
│   └── results/                    # Directory for storing task processing results
│       ├── saved_document/         # Directory for final document results
│       ├── instantiation/          # Directory for instantiation results
│       │   ├── instantiation_pass/ # Tasks successfully instantiated
│       │   └── instantiation_fail/ # Tasks that failed instantiation
│       ├── execution/              # Directory for execution results
│       │   ├── execution_pass/     # Tasks successfully executed
│       │   ├── execution_fail/     # Tasks that failed execution
│       │   └── execution_unsure/   # Tasks with uncertain execution results
│       ├── dataflow/               # Directory for dataflow results
│       │   ├── execution_pass/     # Tasks successfully executed
│       │   ├── execution_fail/     # Tasks that failed execution
│       │   └── execution_unsure/   # Tasks with uncertain execution results
│       └── ...
└── ...
```

1. **General Description:**

   This directory structure organizes the results of task processing into specific categories, including instantiation, execution, and dataflow outcomes.
2. **Instantiation:**

   The `instantiation` directory contains subfolders for tasks that were successfully instantiated (`instantiation_pass`) and those that failed during instantiation (`instantiation_fail`).
3. **Execution:**

   Results of task execution are stored under the `execution` directory, categorized into successful tasks (`execution_pass`), failed tasks (`execution_fail`), and tasks with uncertain outcomes (`execution_unsure`).
4. **Dataflow Results:**

   The `dataflow` directory similarly holds results of tasks based on execution success, failure, or uncertainty, providing a comprehensive view of the data processing pipeline.
5. **Saved Documents:**

   Instantiated results are separately stored in the `saved_document` directory for easy access and reference.

### Description

his section illustrates the structure of the result of the task, organized in a hierarchical format to describe the various fields and their purposes. The result data include `unique_id`，``app``, `original`, `execution_result`, `instantiation_result`, `time_cost`.

#### 1. **Field Descriptions**

- **Hierarchy**: The data is presented in a hierarchical manner to allow for a clearer understanding of field relationships.
- **Type Description**: The type of each field (e.g., `string`, `array`, `object`) clearly specifies the format of the data.
- **Field Purpose**: Each field has a brief description outlining its function.

#### 2. **Execution Results and Errors**

- **execution_result**: Contains the results of task execution, including subtask performance, completion status, and any encountered errors.
- **instantiation_result**: Describes the process of task instantiation, including template selection, prefilled tasks, and instantiation evaluation.
- **error**: If an error occurs during task execution, this field will contain the relevant error information.

#### 3. **Time Consumption**

- **time_cost**: The time spent on each phase of the task, from template selection to task execution, is recorded to analyze task efficiency.

### Example Data

```json
{
    "unique_id": "102",
    "app": "word",
    "original": {
        "original_task": "Find which Compatibility Mode you are in for Word",
        "original_steps": [
            "1.Click the **File** tab.",
            "2.Click **Info**.",
            "3.Check the **Compatibility Mode** indicator at the bottom of the document preview pane."
        ]
    },
    "execution_result": {
        "result": {
            "reason": "The agent successfully identified the compatibility mode of the Word document.",
            "sub_scores": {
                "correct identification of compatibility mode": "yes"
            },
            "complete": "yes"
        },
        "error": null
    },
    "instantiation_result": {
        "choose_template": {
            "result": "dataflow\\results\\saved_document\\102.docx",
            "error": null
        },
        "prefill": {
            "result": {
                "instantiated_request": "Identify the Compatibility Mode of the Word document.",
                "instantiated_plan": [
                    {
                        "Step": 1,
                        "Subtask": "Identify the Compatibility Mode",
                        "Function": "summary",
                        "Args": {
                            "text": "The document is in '102 - Compatibility Mode'."
                        },
                        "Success": true
                    }
                ]
            },
            "error": null
        },
        "instantiation_evaluation": {
            "result": {
                "judge": true,
                "thought": "Identifying the Compatibility Mode of a Word document is a task that can be executed locally within Word."
            },
            "error": null
        }
    },
    "time_cost": {
        "choose_template": 0.017,
        "prefill": 11.304,
        "instantiation_evaluation": 2.38,
        "total": 34.584,
        "execute": 0.946,
        "execute_eval": 10.381
    }
}
```

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

### Result files

The result stucture of bulleted task is shown as below. This document provides a detailed breakdown of the task execution process for turning lines of text into a bulleted list in Word. It includes the original task description, execution results, and time analysis for each step.

* **`unique_id`** : The identifier for the task, in this case, `"5"`.
* **`app`** : The application being used, which is `"word"`.
* **`original`** : Contains the original task description and the steps.

  * **`original_task`** : Describes the task in simple terms (turning text into a bulleted list).
  * **`original_steps`** : Lists the steps required to perform the task.
* **`execution_result`** : Provides the result of executing the task.

  * **`result`** : Describes the outcome of the execution, including a success message and sub-scores for each part of the task. The `complete: "yes"` means the evaluation agent think the execution process is successful! The `sub_score` is the evaluation of each subtask, corresponding to the ` instantiated_plan` in the  `prefill`.
  * **`error`** : If any error occurred during execution, it would be reported here, but it's `null` in this case.
* **`instantiation_result`** : Details the instantiation of the task (setting up the task for execution).

  * **`choose_template`** : Path to the template or document created during the task (in this case, the bulleted list document).
  * **`prefill`** : Describes the `instantiated_request` and  `instantiated_plan` and the steps involved, such as selecting text and clicking buttons, which is the result of prefill flow. The `Success` and `MatchedControlText` is added in the execution process. **`Success`** indicates whether the subtask was executed successfully. **`MatchedControlText`** refers to the control text that was matched during the execution process based on the plan.
  * **`instantiation_evaluation`** : Provides feedback on the task's feasibility and the evaluation of the request, which is result of the filter flow. **`"judge": true`** : This indicates that the evaluation of the task was positive, meaning the task is considered valid or successfully judged. And the `thought ` is the detailed reason.
* **`time_cost`** : The time spent on different parts of the task, including template selection, prefill, instantiation evaluation, and execution. Total time is also given.

This structure follows your description and provides the necessary details in a consistent format.

```json
{
    "unique_id": "5",
    "app": "word",
    "original": {
        "original_task": "Turning lines of text into a bulleted list in Word",
        "original_steps": [
            "1. Place the cursor at the beginning of the line of text you want to turn into a bulleted list",
            "2. Click the Bullets button in the Paragraph group on the Home tab and choose a bullet style"
        ]
    },
    "execution_result": {
        "result": {
            "reason": "The agent successfully selected the text 'text to edit' and then clicked on the 'Bullets' button in the Word application. The final screenshot shows that the text 'text to edit' has been converted into a bulleted list.",
            "sub_scores": {
                "text selection": "yes",
                "bulleted list conversion": "yes"
            },
            "complete": "yes"
        },
        "error": null
    },
    "instantiation_result": {
        "choose_template": {
            "result": "dataflow\\results\\saved_document\\bulleted.docx",
            "error": null
        },
        "prefill": {
            "result": {
                "instantiated_request": "Turn the line of text 'text to edit' into a bulleted list in Word.",
                "instantiated_plan": [
                    {
                        "Step": 1,
                        "Subtask": "Place the cursor at the beginning of the text 'text to edit'",
                        "ControlLabel": null,
                        "ControlText": "",
                        "Function": "select_text",
                        "Args": {
                            "text": "text to edit"
                        },
                        "Success": true,
                        "MatchedControlText": null
                    },
                    {
                        "Step": 2,
                        "Subtask": "Click the Bullets button in the Paragraph group on the Home tab",
                        "ControlLabel": "61",
                        "ControlText": "Bullets",
                        "Function": "click_input",
                        "Args": {
                            "button": "left",
                            "double": false
                        },
                        "Success": true,
                        "MatchedControlText": "Bullets"
                    }
                ]
            },
            "error": null
        },
        "instantiation_evaluation": {
            "result": {
                "judge": true,
                "thought": "The task is specific and involves a basic function in Word that can be executed locally without any external dependencies.",
                "request_type": "None"
            },
            "error": null
        }
    },
    "time_cost": {
        "choose_template": 0.012,
        "prefill": 15.649,
        "instantiation_evaluation": 2.469,
        "execute": 5.824,
        "execute_eval": 8.702,
        "total": 43.522
    }
}
```

### Log files

The corresponding logs can be found in the directories `logs/bulleted` and `logs/rotate`, as shown below. Detailed logs for each workflow are recorded, capturing every step of the execution process.

<h1 align="center">
    <img src="../assets/dataflow/result_example.png"/> 
</h1>

## Notes

1. Users should be careful to save the original files while using this project; otherwise, the files will be closed when the app is shut down.
2. After starting the project, users should not close the app window while the program is taking screenshots.
