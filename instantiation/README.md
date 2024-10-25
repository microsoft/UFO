## Introduction of Instantiation

**The instantiation process aims to filter and modify instructions according to the current environment.**

By using this process, we can obtain clearer and more specific instructions, making them more suitable for the execution of the UFO.

## How to Use

### 1. Install Packages

You should install the necessary packages in the UFO root folder:

```bash
pip install -r requirements.txt
```

### 2. Configure the LLMs

Before using the instantiation section, you need to provide your LLM configurations in `config.yaml` and `config_dev.yaml` located in the `instantiation/config` folder.

- `config_dev.yaml` specifies the paths of relevant files and contains default settings. The match strategy for the control filter supports options: `'contains'`, `'fuzzy'`, and `'regex'`, allowing flexible matching between application windows and target files.

- `config.yaml` stores the agent information. You should copy the `config.yaml.template` file and fill it out according to the provided hints.

You will configure the prefill agent and the filter agent individually. The prefill agent is used to prepare the task, while the filter agent evaluates the quality of the prefilled task. You can choose different LLMs for each.

**BE CAREFUL!** If you are using GitHub or other open-source tools, do not expose your `config.yaml` online, as it contains your private keys.

Once you have filled out the template, rename it to `config.yaml` to complete the LLM configuration.

### 3. Prepare Files

Certain files need to be prepared before running the task.

#### 3.1. Tasks as JSON

The tasks that need to be instantiated should be organized in a folder of JSON files, with the default folder path set to `instantiation/tasks`. This path can be changed in the `instantiation/config/config.yaml` file, or you can specify it in the terminal, as mentioned in **4. Start Running**. For example, a task stored in `instantiation/tasks/prefill/` may look like this:

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

For example, if you have `template1.docx` for Word, it should be located at `instantiation/templates/word/template1.docx`.

Additionally, for each app folder, there should be a `description.json` file located at `instantiation/templates/word/description.json`, which describes each template file in detail. It may look like this:

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
instantiation/
|
├── tasks/
│   ├── action_prefill/
│   │   ├── task1.json
│   │   ├── task2.json
│   │   └── task3.json
│   └── ...
|   
├── templates/
│   ├── word/
│   │   ├── template1.docx
│   │   ├── template2.docx
│   │   ├── template3.docx
│   │   └── description.json
│   └── ...
└── ...
```

### 4. Start Running

Run the `instantiation/action_prefill.py` file in module mode. You can do this by typing the following command in the terminal:

```bash
python -m instantiation
```

You can use `--task` to specify the task folder you want to use; the default is `action_prefill`:

```bash
python -m instantiation --task your_task_folder_name
```

After the process is completed, a new folder named `prefill_instantiated` will be created alongside the original one. This folder will contain the instantiated task, which will look like:

```json
{
    // A unique ID to distinguish different tasks 
    "unique_id": "1",
    // The chosen template path
    "instantial_template_path": "copied template file path",
    // The instantiated task and steps
    "instantiated_request": "Type 'hello' and set the font type to Arial in the Word document.",
    "instantiated_plan": [
        {
            "step 1": "Select the target text 'text to edit'",
            "controlLabel": "",
            "controlText": "",
            "function": "select_text",
            "args": {
                "text": "text to edit"
            }
        },
        {
            "step 2": "Type 'hello'",
            "controlLabel": "101",
            "controlText": "Edit",
            "function": "type_keys",
            "args": {
                "text": "hello"
            }
        },
        {
            "step 3": "Select the typed text 'hello'",
            "controlLabel": "",
            "controlText": "",
            "function": "select_text",
            "args": {
                "text": "hello"
            }
        },
        {
            "step 4": "Click the font dropdown",
            "controlLabel": "",
            "controlText": "Consolas",
            "function": "click_input",
            "args": {
                "button": "left",
                "double": false
            }
        },
        {
            "step 5": "Set the font to Arial",
            "controlLabel": "",
            "controlText": "Arial",
            "function": "click_input",
            "args": {
                "button": "left",
                "double": false
            }
        }
    ],
    "result": {
        "filter": "Drawing or writing a signature using the drawing tools in the Word desktop app is a task that can be executed locally within the application."
    },
    "execution_time": {
        "choose_template": 10.650701761245728,
        "prefill": 44.23913502693176,
        "filter": 3.746831178665161,
        "total": 58.63666796684265
    }
}
```

Additionally, a `prefill_templates` folder will be created, which stores the copied chosen templates for each task.

## Workflow

There are three key steps in the instantiation process:

1. Choose a template file according to the specified app and instruction.
2. Prefill the task using the current screenshot.
3. Filter the established task.

#### 1. Choose Template File

Templates for your app must be defined and described in `instantiation/templates/app`. For instance, if you want to instantiate tasks for the Word application, place the relevant `.docx` files in `instantiation/templates/word`, along with a `description.json` file.

The appropriate template will be selected based on how well its description matches the instruction.

#### 2. Prefill the Task

After selecting the template file, it will be opened, and a screenshot will be taken. If the template file is currently in use, errors may occur.

The screenshot will be sent to the action prefill agent, which will return a modified task.

#### 3. Filter Task

The completed task will be evaluated by a filter agent, which will assess it and provide feedback. If the task is deemed a good instance, it will be saved in `instantiation/tasks/your_folder_name_instantiated/instances_pass/`; otherwise, it will be saved in `instantiation/tasks/your_folder_name_instantiated/instances_fail/`.

All encountered error messages and tracebacks are saved in `instantiation/tasks/your_folder_name_instantiated/instances_error/`.

## Notes

1. Users should be careful to save the original files while using this project; otherwise, the files will be closed when the app is shut down.

2. After starting the project, users should not close the app window while the program is taking screenshots.
