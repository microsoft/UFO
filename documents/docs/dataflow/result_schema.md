# Result schema

## Instantiation Result Schema

This schema defines the structure of a JSON object that might be used to represent the results of task `instantiation`. 

#### **Root Structure**
- The schema is an object with the following key fields:
  - **`unique_id`**: A string serving as the unique identifier for the task.
  - **`app`**: A string representing the application where the task is being executed.
  - **`original`**: An object containing details about the original task.

#### **Field Descriptions**

1. **`unique_id`**  
   - Type: `string`  
   - Purpose: Provides a globally unique identifier for the task.

2. **`app`**  
   - Type: `string`  
   - Purpose: Specifies the application associated with the task execution.

3. **`original`**  
   - Type: `object`  
   - Contains the following fields:
     - **`original_task`**:  
       - Type: `string`  
       - Purpose: Describes the main task in textual form.  
     - **`original_steps`**:  
       - Type: `array` of `string`  
       - Purpose: Lists the sequential steps required for the task.

   - Required fields: `original_task`, `original_steps`

4. **`execution_result`**  
   - Type: `object` or `null`  
   - Contains fields describing the results of task execution:
     - **`result`**: Always `null`, indicating no execution results are included.  
     - **`error`**: Always `null`, implying execution errors are not tracked in this schema.  
   - Purpose: Simplifies the structure by omitting detailed execution results.

5. **`instantiation_result`**  
   - Type: `object`  
   - Contains fields detailing the results of task instantiation:
     - **`choose_template`**:  
       - Type: `object`  
       - Fields:  
         - **`result`**: A string or `null`, representing the outcome of template selection.  
         - **`error`**: A string or `null`, detailing any errors during template selection.  
       - Required fields: `result`, `error`
     - **`prefill`**:  
       - Type: `object` or `null`  
       - Contains results of pre-filling instantiation:
         - **`result`**:  
           - Type: `object` or `null`  
           - Fields:  
             - **`instantiated_request`**: A string, representing the generated request.  
             - **`instantiated_plan`**: An array or `null`, listing instantiation steps:
               - **`Step`**: An integer representing the sequence of the step.  
               - **`Subtask`**: A string describing the subtask.  
               - **`ControlLabel`**: A string or `null`, representing the control label.  
               - **`ControlText`**: A string, providing context for the step.  
               - **`Function`**: A string, specifying the function executed at this step.  
               - **`Args`**: An object, containing any arguments required by the function.  
             - Required fields: `Step`, `Subtask`, `Function`, `Args`
         - Required fields: `instantiated_request`, `instantiated_plan`  
         - **`error`**: A string or `null`, describing errors encountered during prefill.  
       - Required fields: `result`, `error`
     - **`instantiation_evaluation`**:  
       - Type: `object`  
       - Fields:  
         - **`result`**:  
           - Type: `object` or `null`  
           - Contains:  
             - **`judge`**: A boolean, indicating whether the instantiation is valid.  
             - **`thought`**: A string, providing reasoning or observations.  
             - **`request_type`**: A string, classifying the request type.  
           - Required fields: `judge`, `thought`, `request_type`  
         - **`error`**: A string or `null`, indicating errors during evaluation.  
       - Required fields: `result`, `error`

6. **`time_cost`**  
   - Type: `object`  
   - Tracks time metrics for various stages of task instantiation:
     - **`choose_template`**: A number or `null`, time spent selecting a template.  
     - **`prefill`**: A number or `null`, time used for pre-filling.  
     - **`instantiation_evaluation`**: A number or `null`, time spent on evaluation.  
     - **`total`**: A number or `null`, total time cost for all processes.  
   - Required fields: `choose_template`, `prefill`, `instantiation_evaluation`, `total`


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

This schema defines the structure of a JSON object that might be used to represent the results of task `execution` or `dataflow`. Below are the main fields and their detailed descriptions.

Unlike the instantiation result, the execution result schema provides detailed feedback on execution, including success metrics (`reason`, `sub_scores`). Additionally, based on the original instantiated_plan, each step has been enhanced with the fields `Success` and `MatchedControlText`, which represent whether the step executed successfully (success is indicated by no errors) and the name of the last matched control, respectively. The `ControlLabel` will also be updated to reflect the final selected ControlLabel.

---

### **Top-Level Fields**

1. **`unique_id`**

   - **Type**: `string`
   - **Description**: A unique identifier for the task or record.
2. **`app`**

   - **Type**: `string`
   - **Description**: The name of the application associated with the task.
3. **`original`**

   - **Type**: `object`
   - **Description**: Contains the original definition of the task.
   - **Properties**:
     - **`original_task`**:
       - **Type**: `string`
       - **Description**: The original description of the task.
     - **`original_steps`**:
       - **Type**: `array`
       - **Description**: An array of strings representing the steps of the task.
4. **`execution_result`**

   - **Type**: `object` or `null`
   - **Description**: Represents the results of the task execution.
   - **Properties**:
     - **`result`**:
       - **Type**: `object` or `null`
       - **Description**: Contains the details of the execution result.
       - **Sub-properties**:
         - **`reason`**: The reason for the execution result, type `string`.
         - **`sub_scores`**: A set of sub-scores, represented as key-value pairs (`.*` allows any key pattern).
         - **`complete`**: Indicates the completion status, type `string`.
     - **`error`**:
       - **Type**: `object` or `null`
       - **Description**: Represents any error information encountered during execution.
       - **Sub-properties**:
         - **`type`**: The type of error, type `string`.
         - **`message`**: The error message, type `string`.
         - **`traceback`**: The error traceback, type `string`.
5. **`instantiation_result`**

   - **Type**: `object`
   - **Description**: Contains results related to task instantiation.
   - **Properties**:
     - **`choose_template`**:
       - **Type**: `object`
       - **Description**: Results of template selection.
       - **Sub-properties**:
         - **`result`**: The result of template selection, type `string` or `null`.
         - **`error`**: Error information, type `null` or `string`.
     - **`prefill`**:
       - **Type**: `object` or `null`
       - **Description**: Results of the prefill phase.
       - **Sub-properties**:
         - **`result`**:
           - **Type**: `object` or `null`
           - **Description**: Contains the instantiated request and plan.
           - **Sub-properties**:
             - **`instantiated_request`**: The instantiated task request, type `string`.
             - **`instantiated_plan`**: The instantiated task plan, type `array` or `null`.
               - Each item in the array is an object with:
                 - **`Step`**: Step number, type `integer`.
                 - **`Subtask`**: Description of the subtask, type `string`.
                 - **`ControlLabel`**: Control label, type `string` or `null`.
                 - **`ControlText`**: Control text, type `string`.
                 - **`Function`**: Function name, type `string`.
                 - **`Args`**: Arguments to the function, type `object`.
                 - **`Success`**: Whether the step succeeded, type `boolean` or `null`.
                 - **`MatchedControlText`**: Matched control text, type `string` or `null`.
         - **`error`**: Prefill error information, type `null` or `string`.
     - **`instantiation_evaluation`**:
       - **Type**: `object`
       - **Description**: Results of task instantiation evaluation.
       - **Sub-properties**:
         - **`result`**:
           - **Type**: `object` or `null`
           - **Description**: Contains evaluation information.
           - **Sub-properties**:
             - **`judge`**: Whether the evaluation succeeded, type `boolean`.
             - **`thought`**: Evaluator's thoughts, type `string`.
             - **`request_type`**: The type of request, type `string`.
         - **`error`**: Evaluation error information, type `null` or `string`.
6. **`time_cost`**

   - **Type**: `object`
   - **Description**: Represents the time costs for various phases.
   - **Properties**:
     - **`choose_template`**: Time spent selecting the template, type `number` or `null`.
     - **`prefill`**: Time spent in the prefill phase, type `number` or `null`.
     - **`instantiation_evaluation`**: Time spent in instantiation evaluation, type `number` or `null`.
     - **`total`**: Total time cost, type `number` or `null`.
     - **`execute`**: Time spent in execution, type `number` or `null`.
     - **`execute_eval`**: Time spent in execution evaluation, type `number` or `null`.

---

### **Required Fields**

The fields `unique_id`, `app`, `original`, `execution_result`, `instantiation_result`, and `time_cost` are required for the JSON object to be valid.

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
