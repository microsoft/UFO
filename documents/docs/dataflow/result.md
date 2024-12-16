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

| **Field**                                             | **Description**                                                                                             |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **`unique_id`**                                     | A unique identifier for the task.                                                                                 |
| **`app`**                                           | The name of the application that processes the task.                                                              |
| **`original`**                                      | Contains details about the original task, including:                                                              |
| **`original.original_task`**                        | A description of the original task.                                                                               |
| **`original.original_steps`**                       | A list of steps involved in the original task.                                                                    |
| **`execution_result`**                              | Stores the result of task `execution`, including any errors encountered and execution evaluation.               |
| **`instantiation_result`**                          | Provides details of the `instantiation`process, including:                                                      |
| **`instantiation_result.choose_template`**          | The template selection result and any associated errors.                                                          |
| **`instantiation_result.prefill`**                  | Information about pre-filled task, including the instantiated request and plan.                                   |
| **`instantiation_result.instantiation_evaluation`** | Evaluation results of the instantiated task, including judgments and feedback.                                    |
| **`time_cost`**                                     | Tracks the time taken for various stages of the process, such as template selection, pre-filling, and evaluation. |

## Instantiation Result Schema

The instantiation schema in `"dataflow/schema/instantiation_schema.json"` defines the structure of a JSON object that is used to validate the results of task `instantiation`.

---

### **Schema Tabular Description**

| **Field**                                                                   | **Description**                                                                                             |
| --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **`unique_id`**                                                           | A unique identifier for the task.                                                                                 |
| **`app`**                                                                 | The name of the application that processes the task.                                                              |
| **`original`**                                                            | Contains details about the original task, including:                                                              |
| **`original.original_task`**                                              | A description of the original task.                                                                               |
| **`original.original_steps`**                                             | A list of steps involved in the original task.                                                                    |
| **`execution_result`**                                                    | Stores the result of task execution, including any errors encountered and execution evaluation.                   |
| **`execution_result.result`**                                             | Indicates the execution result (or null if not applicable).                                                       |
| **`execution_result.error`**                                              | Details any errors encountered during task execution.                                                             |
| **`instantiation_result`**                                                | Provides details of the instantiation process, including:                                                         |
| **`instantiation_result.choose_template`**                                | The template selection result and any associated errors.                                                          |
| **`instantiation_result.prefill`**                                        | Information about pre-filled tasks, including the instantiated request and plan.                                  |
| **`instantiation_result.prefill.result`**                                 | Contains details of instantiated requests and plans.                                                              |
| **`instantiation_result.prefill.result.instantiated_request`**            | The instantiated task request.                                                                                    |
| **`instantiation_result.prefill.result.instantiated_plan`**               | Contains details of the instantiated steps.                                                                       |
| **`instantiation_result.prefill.result.instantiated_plan.step`**          | The step sequence number.                                                                                         |
| **`instantiation_result.prefill.result.instantiated_plan.subtask`**       | The description of the subtask.                                                                                   |
| **`instantiation_result.prefill.result.instantiated_plan.control_label`** | Control label for the step (or null if not applicable).                                                           |
| **`instantiation_result.prefill.result.instantiated_plan.control_text`**  | Contextual text for the step.                                                                                     |
| **`instantiation_result.prefill.result.instantiated_plan.function`**      | The function executed in this step.                                                                               |
| **`instantiation_result.prefill.result.instantiated_plan.args`**          | Parameters required for the function.                                                                             |
| **`instantiation_result.prefill.error`**                                  | Errors, if any, during the prefill process.                                                                       |
| **`instantiation_result.instantiation_evaluation`**                       | Evaluation results of the instantiated task, including judgments and feedback.                                    |
| **`instantiation_result.instantiation_evaluation.result`**                | Contains detailed evaluation results.                                                                             |
| **`instantiation_result.instantiation_evaluation.result.judge`**          | Indicates whether the evaluation passed.                                                                          |
| **`instantiation_result.instantiation_evaluation.result.thought`**        | Feedback or observations from the evaluator.                                                                      |
| **`instantiation_result.instantiation_evaluation.result.request_type`**   | Classification of the request type.                                                                               |
| **`instantiation_result.instantiation_evaluation.error`**                 | Errors, if any, during the evaluation.                                                                            |
| **`time_cost`**                                                           | Tracks the time taken for various stages of the process, such as template selection, pre-filling, and evaluation. |
| **`time_cost.choose_template`**                                           | Time taken for the template selection stage.                                                                      |
| **`time_cost.prefill`**                                                   | Time taken for the prefill stage.                                                                                 |
| **`time_cost.instantiation_evaluation`**                                  | Time taken for the evaluation stage.                                                                              |
| **`time_cost.total`**                                                     | Total time taken for the task.                                                                                    |

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

---

### **Schema Tabular Description**

| **Field**                                                                        | **Description**                                                                               |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **`unique_id`**                                                                | A unique identifier for the task.                                                                   |
| **`app`**                                                                      | The name of the application that processes the task.                                                |
| **`original`**                                                                 | Contains details about the original task, including:                                                |
| **`original.original_task`**                                                   | A description of the original task.                                                                 |
| **`original.original_steps`**                                                  | A list of steps involved in the original task.                                                      |
| **`execution_result`**                                                         | Represents the result of task execution, including any errors encountered and execution evaluation. |
| **`execution_result.result`**                                                  | Indicates the result of the task execution.                                                         |
| **`execution_result.error`**                                                   | Indicates any errors that occurred during execution.                                                |
| **`instantiation_result`**                                                     | Provides details about the task instantiation, including:                                           |
| **`instantiation_result.choose_template.result`**                              | The template selection result.                                                                      |
| **`instantiation_result.choose_template.error`**                               | Errors, if any, during template selection.                                                          |
| **`instantiation_result.prefill.result.instantiated_request`**                 | The instantiated task request.                                                                      |
| **`instantiation_result.prefill.result.instantiated_plan.Step`**               | The step sequence number.                                                                           |
| **`instantiation_result.prefill.result.instantiated_plan.Subtask`**            | The description of the subtask.                                                                     |
| **`instantiation_result.prefill.result.instantiated_plan.ControlLabel`**       | Control label for the step.                                                                         |
| **`instantiation_result.prefill.result.instantiated_plan.ControlText`**        | Contextual text for the step.                                                                       |
| **`instantiation_result.prefill.result.instantiated_plan.Function`**           | The function executed in this step.                                                                 |
| **`instantiation_result.prefill.result.instantiated_plan.Args`**               | Parameters required for the function.                                                               |
| **`instantiation_result.prefill.result.instantiated_plan.Success`**            | Indicates if the step was executed successfully without errors.                                     |
| **`instantiation_result.prefill.result.instantiated_plan.MatchedControlText`** | The final matched control text in the execution flow.                                               |
| **`instantiation_result.prefill.error`**                                       | Errors, if any, during the prefill process.                                                         |
| **`instantiation_result.instantiation_evaluation.result.judge`**               | Indicates whether the evaluation passed.                                                            |
| **`instantiation_result.instantiation_evaluation.result.thought`**             | Feedback or observations from the evaluator.                                                        |
| **`instantiation_result.instantiation_evaluation.result.request_type`**        | Classification of the request type.                                                                 |
| **`instantiation_result.instantiation_evaluation.error`**                      | Errors, if any, during the evaluation.                                                              |
| **`time_cost`**                                                                | Tracks the time taken for various stages of the process, including:                                 |
| **`time_cost.choose_template`**                                                | Time taken for the template selection stage.                                                        |
| **`time_cost.prefill`**                                                        | Time taken for the prefill stage.                                                                   |
| **`time_cost.instantiation_evaluation`**                                       | Time taken for the evaluation stage.                                                                |
| **`time_cost.execute`**                                                        | Time taken for the execute stage.                                                                   |
| **`time_cost.execute_eval`**                                                   | Time taken for the execute evaluation stage.                                                        |
| **`time_cost.total`**                                                          | Total time taken for the task.                                                                      |

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
