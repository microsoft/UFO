
## Introduction of Instantiation

**The instantiation process aims to filter and modify instructions according to the current environment.**

By using this process, we can obtain clearer and more specific instructions, making them more suitable for the execution of the UFO.

## How to use

The tasks that need instantiation should exist as a folder of JSON files, with the default folder path set to `instantiation/tasks`. This path can be changed in the `.yaml` file. For example, a task stored in `instantiation/tasks/action_prefill/` may look like this:

```json
{
    "app": "word",
    "task": "Type in hello and set font type as Arial",
    "unique_id": "1",
    "refined_steps": [
        "type in 'hello'",
        "Set the font to Arial"
    ]
}
```

You can instantiate the tasks by running the following command in the terminal:

```
python instantiation/action_prefill.py
```

After the process is completed, a new folder will be created alongside the original one, named `action_prefill_new`, containing the instantiated task, which will look like:

```json
{
    "unique_id": "1",
    "instantial_template_path": "cached template file path",
    "instantiated_request": "Type 'hello' and set the font type to Arial in the Word document.",
    "instantiated_plan": [
        {
            "step 1": "select the target text 'text to edit'",
            "controlLabel": "",
            "controlText": "",
            "function": "select_text",
            "args": {
                "text": "text to edit"
            }
        },
        {
            "step 2": "type in 'hello'",
            "controlLabel": "101",
            "controlText": "Edit",
            "function": "type_keys",
            "args": {
                "text": "hello"
            }
        },
        {
            "step 3": "select the typed text 'hello'",
            "controlLabel": "",
            "controlText": "",
            "function": "select_text",
            "args": {
                "text": "hello"
            }
        },
        {
            "step 4": "click the font dropdown",
            "controlLabel": "",
            "controlText": "Consolas",
            "function": "click_input",
            "args": {
                "button": "left",
                "double": false
            }
        },
        {
            "step 5": "set the font to Arial",
            "controlLabel": "",
            "controlText": "Arial",
            "function": "click_input",
            "args": {
                "button": "left",
                "double": false
            }
        }
    ],
    "request_comment": "The task involves typing a specific string 'hello' and setting the font type to Arial, which can be executed locally within Word."
}
```

## Workflow

There are three key steps in the instantiation process:

1. Choose a template file according to the specified app and instruction.
2. Prefill the task using the current screenshot.
3. Filter the established task.

##### 1. Choose template file

Templates for your app must be defined and described in `instantiation/templates/app`. For example, if you want to instantiate tasks for the Word application, place the relevant `.docx` files in `instantiation/templates/word`, along with a `description.json` file.

The appropriate template will be selected based on how well its description matches the instruction.

##### 2. Prefill the task

After selecting the template file, it will be opened, and a snapshot will be taken. If the template file is currently in use, errors may occur.

The screenshot will be sent to the action prefill agent, which will provide a modified task in return.

##### 3. Filter task

The completed task will be evaluated by a filter agent, which will assess it and return feedback. If the task is deemed a good instance, it will be saved in `instantiation/tasks/your_folder_name_new/good_instances`; otherwise, it will follow the same process for poor instances.
