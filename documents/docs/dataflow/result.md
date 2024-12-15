# Result

The results will be saved in the `"dataflow/results"` directory under `instantiation`, `execution`, and `dataflow`, and will be further stored in subdirectories based on the result.

The results are saved by validating the task information against a `schema` (`instantiation_schema` or `execution_schema.json` in the `"dataflow/schema"`) and determining the target directory based on the `task type` and its `evaluation status`, then storing the result in the appropriate location. The structure of the storage and the specific meaning of the schema are as follows.

## Overall Result Struction

The structure of the results of the task is as below:

```bash
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
   This directory structure organizes the results of task processing into specific categories, including `instantiation`, `execution`, and `dataflow` outcomes.
2. **Instantiation:**

   - The `instantiation` directory contains subfolders for tasks that were successfully instantiated (`instantiation_pass`) and those that failed during instantiation (`instantiation_fail`).
   - This corresponds to the result of `instantiation_evaluation`, with the field name `"judge"`.
3. **Execution:**

   - Results of task `execution` are stored under the `execution` directory, categorized into successful tasks (`execution_pass`), failed tasks (`execution_fail`), and tasks with uncertain outcomes (`execution_unsure`).
   - This corresponds to the `evaluation` result of `execute_flow`, with the field name `"complete"`.
4. **Dataflow Results:**

   - The `dataflow` directory similarly stores the results of tasks based on the execution outcome: `execution_pass` for success, `execution_fail` for failure, or `execution_unsure` for uncertainty.
   - This corresponds to the `evaluation` result of `execute_flow`, with the field name `"complete"`.
5. **Saved Documents:**
   Instantiated results are separately stored in the `saved_document` directory for easy access and reference.

### Overall Description

The result data include `unique_id`，``app``, `original`, `execution_result`, `instantiation_result`, `time_cost`.

The result data includes the following fields:

| **Field**                           | **Description**                                                                                             |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **`unique_id`**                   | A unique identifier for the task.                                                                                 |
| **`app`**                         | The name of the application that processes the task.                                                              |
| **`original`**                    | Contains details about the original task, including:                                                              |
| ---**`original_task`**            | A description of the original task.                                                                               |
| ---**`original_steps`**           | A list of steps involved in the original task.                                                                    |
| **`execution_result`**            | Stores the result of task `execution`, including any errors encountered and execution evaluation.               |
| **`instantiation_result`**        | Provides details of the `instantiation`process, including:                                                      |
| ---**`choose_template`**          | The template selection result and any associated errors.                                                          |
| ---**`prefill`**                  | Information about pre-filled task, including the instantiated request and plan.                                   |
| ---**`instantiation_evaluation`** | Evaluation results of the instantiated task, including judgments and feedback.                                    |
| **`time_cost`**                   | Tracks the time taken for various stages of the process, such as template selection, pre-filling, and evaluation. |

## Instantiation Result Schema

The instantiation schema in `"dataflow/schema/instantiation_schema.json"` defines the structure of a JSON object that is used to validate the results of task `instantiation`.

---

### **Schema Tabular Description**

| Field Name                                     | Type                | Description                                          | Required |
| ---------------------------------------------- | ------------------- | ---------------------------------------------------- | -------- |
| **unique_id**                            | `string`          | A unique identifier for the task.                    | Yes      |
| **app**                                  | `string`          | The application name executing the task.             | Yes      |
| **original**                             | `object`          | Contains details of the original task.               | Yes      |
| ├──**original_task**                  | `string`          | The main task described as a text.                   | Yes      |
| └──**original_steps**                 | `array[string]`   | Steps of the task in sequence.                       | Yes      |
| **execution_result**                     | `object`/`null` | Represents the result of the task execution.         | Yes      |
| ├──**result**                         | `null`            | Indicates the execution result is null.              | No       |
| └──**error**                          | `null`            | Indicates the execution error is null.               | No       |
| **instantiation_result**                 | `object`          | Contains details about the task instantiation.       | Yes      |
| ├──**choose_template**                | `object`          | The result of template selection.                    | Yes      |
| │   ├──**result**                    | `string`/`null` | The result of the template selection.                | Yes      |
| │   └──**error**                     | `string`/`null` | Errors, if any, during template selection.           | Yes      |
| ├──**prefill**                        | `object`/`null` | Results from the prefill stage.                      | Yes      |
| │   ├──**result**                    | `object`/`null` | Contains details of instantiated requests and plans. | Yes      |
| │   │   ├──**instantiated_request** | `string`          | The instantiated task request.                       | Yes      |
| │   │   └──**instantiated_plan**    | `array[object]`   | Contains details of the instantiated steps.          | Yes      |
| │   │       ├──**Step**             | `integer`         | The step sequence number.                            | Yes      |
| │   │       ├──**Subtask**          | `string`          | The description of the subtask.                      | Yes      |
| │   │       ├──**ControlLabel**     | `string`/`null` | Control label for the step.                          | No       |
| │   │       ├──**ControlText**      | `string`          | Contextual text for the step.                        | Yes      |
| │   │       ├──**Function**         | `string`          | The function executed in this step.                  | Yes      |
| │   │       └──**Args**             | `object`          | Parameters required for the function.                | Yes      |
| │   └──**error**                     | `string`/`null` | Errors, if any, during the prefill process.          | Yes      |
| ├──**instantiation_evaluation**       | `object`          | The result of instantiation evaluation.              | Yes      |
| │   ├──**result**                    | `object`/`null` | Contains detailed evaluation results.                | Yes      |
| │   │   ├──**judge**                | `boolean`         | Indicates whether the evaluation passed.             | Yes      |
| │   │   ├──**thought**              | `string`          | Feedback or observations from the evaluator.         | Yes      |
| │   │   └──**request_type**         | `string`          | Classification of the request type.                  | Yes      |
| │   └──**error**                     | `string`/`null` | Errors, if any, during the evaluation.               | Yes      |
| **time_cost**                            | `object`          | Contains timing information for task stages.         | Yes      |
| ├──**choose_template**                | `number`/`null` | Time taken for the template selection stage.         | Yes      |
| ├──**prefill**                        | `number`/`null` | Time taken for the prefill stage.                    | Yes      |
| ├──**instantiation_evaluation**       | `number`/`null` | Time taken for the evaluation stage.                 | Yes      |
| └──**total**                          | `number`/`null` | Total time taken for the task.                       | Yes      |

---

### Example Data

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
        "result": null,
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
                        }
                    },
                    {
                        "Step": 2,
                        "Subtask": "Click the Bullets button in the Paragraph group on the Home tab",
                        "ControlLabel": null,
                        "ControlText": "Bullets",
                        "Function": "click_input",
                        "Args": {
                            "button": "left",
                            "double": false
                        }
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
        "execute": null,
        "execute_eval": null,
        "total": 18.130
    }
}
```

## Execution Result Schema

The execution result schema in the `"dataflow/schema/execution_schema.json"` defines the structure of a JSON object that is used to validate the results of task `execution` or `dataflow`.

The **execution result schema** provides **comprehensive feedback on execution**, emphasizing key success metrics (`reason`, `sub_scores`, `complete`) recorded in the `result` field of `execution_result`.

Key enhancements include:

1. Each step in the `instantiated_plan` has been augmented with:
    - **`Success`**: Indicates if the step executed successfully (no errors).
    - **`MatchedControlText`**: Records the name of the last matched control.
    - **`ControlLabel`:** Be updated to reflect the final selected control.

2. The **`execute`**、**`execute_eval`** and **`total`** in the  **`time_cost`** field is updated.

These additions ensure precise tracking of execution outcomes and step-by-step control alignment.

---

### **Schema Tabular Description**

| Field Name                                       | Type                | Description                                           | Required |
| ------------------------------------------------ | ------------------- | ----------------------------------------------------- | -------- |
| **unique_id**                              | `string`          | A unique identifier for the task.                     | Yes      |
| **app**                                    | `string`          | The application name executing the task.              | Yes      |
| **original**                               | `object`          | Contains details of the original task.                | Yes      |
| ├──**original_task**                    | `string`          | The main task described as a text.                    | Yes      |
| └──**original_steps**                   | `array[string]`   | Steps of the task in sequence.                        | Yes      |
| **execution_result**                       | `object`/`null` | Represents the result of the task execution.          | Yes      |
| ├──**result**                           | `null`            | Indicates the execution result is null.               | No       |
| └──**error**                            | `null`            | Indicates the execution error is null.                | No       |
| **instantiation_result**                   | `object`          | Contains details about the task instantiation.        | Yes      |
| ├──**choose_template**                  | `object`          | The result of template selection.                     | Yes      |
| │   ├──**result**                      | `string`/`null` | The result of the template selection.                 | Yes      |
| │   └──**error**                       | `string`/`null` | Errors, if any, during template selection.            | Yes      |
| ├──**prefill**                          | `object`/`null` | Results from the prefill stage.                       | Yes      |
| │   ├──**result**                      | `object`/`null` | Contains details of instantiated requests and plans.  | Yes      |
| │   │   ├──**instantiated_request**   | `string`          | The instantiated task request.                        | Yes      |
| │   │   └──**instantiated_plan**      | `array[object]`   | Contains details of the instantiated steps.           | Yes      |
| │   │       ├──**Step**               | `integer`         | The step sequence number.                             | Yes      |
| │   │       ├──**Subtask**            | `string`          | The description of the subtask.                       | Yes      |
| │   │       ├──**ControlLabel**       | `string`/`null` | Control label for the step.                           | No       |
| │   │       ├──**ControlText**        | `string`          | Contextual text for the step.                         | Yes      |
| │   │       ├──**Function**           | `string`          | The function executed in this step.                   | Yes      |
| │   │       └──**Args**               | `object`          | Parameters required for the function.                 | Yes      |
| │   │       └──**Success**            | `object`          | If the step is executed sucessfully without errors.   | Yes      |
| │   │       └──**MatchedControlText** | `object`          | The final matched control text in the execution flow. | Yes      |
| │   └──**error**                       | `string`/`null` | Errors, if any, during the prefill process.           | Yes      |
| ├──**instantiation_evaluation**         | `object`          | The result of instantiation evaluation.               | Yes      |
| │   ├──**result**                      | `object`/`null` | Contains detailed evaluation results.                 | Yes      |
| │   │   ├──**judge**                  | `boolean`         | Indicates whether the evaluation passed.              | Yes      |
| │   │   ├──**thought**                | `string`          | Feedback or observations from the evaluator.          | Yes      |
| │   │   └──**request_type**           | `string`          | Classification of the request type.                   | Yes      |
| │   └──**error**                       | `string`/`null` | Errors, if any, during the evaluation.                | Yes      |
| **time_cost**                              | `object`          | Contains timing information for task stages.          | Yes      |
| ├──**choose_template**                  | `number`/`null` | Time taken for the template selection stage.          | Yes      |
| ├──**prefill**                          | `number`/`null` | Time taken for the prefill stage.                     | Yes      |
| ├──**instantiation_evaluation**         | `number`/`null` | Time taken for the evaluation stage.                  | Yes      |
| ├──**execute**                          | `number`/`null` | Time taken for the execute stage.                     | Yes      |
| ├──**execute_eval**                     | `number`/`null` | Time taken for the execute evaluation stage.          | Yes      |
| └──**total**                            | `number`/`null` | Total time taken for the task.                        | Yes      |

### Example Data

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
