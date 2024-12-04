# Dataflow

Dataflow uses UFO to implement `instantiation`, `execution`, and `dataflow` for a given task, with options for batch processing and single processing.

1. **Instantiation**:  Instantiation refers to the process of setting up and preparing a task for execution. This step typically involves `choosing template`, `prefill` and `filter`.
2. **Execution**: Execution is the actual process of running the task. This step involves carrying out the actions or operations specified by the `Instantiation`. And after execution, an evaluate agent will evaluate the quality of the whole execution process.
3. **Dataflow**: Dataflow is the overarching process that combines **instantiation** and **execution** into a single pipeline. It provides an end-to-end solution for processing tasks, ensuring that all necessary steps (from initialization to execution) are seamlessly integrated.

You can use `instantiation` and `execution` independently if you only need to perform one specific part of the process. When both steps are required for a task, the `dataflow` process streamlines them, allowing you to execute tasks from start to finish in a single pipeline.

## HOW TO USE

### 1. Install Packages

You should install the necessary packages in the UFO root folder:

```bash
pip install -r requirements.txt
```

### 2. Configure the LLMs

Before using the instantiation section, you need to provide your LLM configurations in `config.yaml` and `config_dev.yaml` located in the dataflow `/config ` folder.

- `config_dev.yaml` specifies the paths of relevant files and contains default settings. The match strategy for the window match and control filter supports options: `'contains'`, `'fuzzy'`, and `'regex'`, allowing flexible matching strategy for users.
- `config.yaml` stores the agent information. You should copy the `config.yaml.template` file and fill it out according to the provided hints.

You will configure the prefill agent and the filter agent individually. The prefill agent is used to prepare the task, while the filter agent evaluates the quality of the prefilled task. You can choose different LLMs for each.

**BE CAREFUL!** If you are using GitHub or other open-source tools, do not expose your `config.yaml` online, as it contains your private keys.

Once you have filled out the template, rename it to `config.yaml` to complete the LLM configuration.

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
    "template2.docx": "A document with a line of text",
    "template3.docx": "A document with a chart"
}
```

If a `description.json` file is not present, one template file will be selected at random.

#### 3.3. Final Structure

Ensure the following files are in place:

- [X] JSON files to be instantiated
- [X] Templates as references for instantiation
- [X] Description file in JSON format

The structure of the files can be:

```bash
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

### 4. How To Use

After finishing the previous steps, you can use the following commands in the command line. We provide single / batch process, for which you need to give the single file path / folder path.

Also, you can choose to use `instantiation` / `execution` sections individually, or use them as a whole section, which is named as `dataflow`.

1. **Single Task Processing**

- Dataflow Task:
  ```bash
  python -m dataflow single dataflow /task_dir/task_file_name
  ```

* Instantiation Task:
  ```bash
  python -m dataflow single instantiation /task_dir/task_file_name
  ```
* Execution Task:
  ```bash
  python -m dataflow single execution /task_dir/task_file_name
  ```

2. **Batch Task Processing**

* Dataflow Task Batch:
  ```bash
  python -m dataflow batch dataflow /path/to/task_dir/
  ```
* Instantiation Task Batch:
  ```bash
  python -m dataflow batch instantiation /path/to/task_dir/
  ```
* Execution Task Batch:
  ```bash
  python -m dataflow batch execution /path/to/task_dir/
  ```

## Workflow

### Instantiation

There are four key steps in the instantiation process:

1. `Choose a template` file according to the specified app and instruction.
2. `Prefill` the task using the current screenshot.
3. `Filter` the established task.

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

## Result

The structure of the results of the task is as below:

```
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

## Notes

1. Users should be careful to save the original files while using this project; otherwise, the files will be closed when the app is shut down.
2. After starting the project, users should not close the app window while the program is taking screenshots.
