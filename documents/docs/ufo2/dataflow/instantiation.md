# Instantiation

There are three key steps in the instantiation process:

1. `Choose a template` file according to the specified app and instruction.
2. `Prefill` the task using the current screenshot.
3. `Filter` the established task.

Given the initial task, the dataflow first choose a template (`Phase 1`), the prefill the initial task based on word envrionment to obtain task-action data (`Phase 2`). Finnally, it will filter the established task to evaluate the quality of task-action data.

<h1 align="center">
    <img src="../../img/instantiation.png"/> 
</h1>

## 1. Choose Template File

Templates for your app must be defined and described in `dataflow/templates/app`. For instance, if you want to instantiate tasks for the Word application, place the relevant `.docx` files in dataflow `/templates/word `, along with a `description.json` file. The appropriate template will be selected based on how well its description matches the instruction.

The `ChooseTemplateFlow` uses semantic matching, where task descriptions are compared with template descriptions using embeddings and FAISS for efficient nearest neighbor search. If semantic matching fails, a random template is chosen from the available files.

## 2. Prefill the Task

### PrefillFlow

The `PrefillFlow` class orchestrates the refinement of task plans and UI interactions by leveraging `PrefillAgent` for task planning and action generation. It automates UI control updates, captures screenshots, and manages logs for messages and responses during execution.

### PrefillAgent

The `PrefillAgent` class facilitates task instantiation and action sequence generation by constructing tailored prompt messages using the `PrefillPrompter`. It integrates system, user, and dynamic context to generate actionable inputs for down-stream workflows.

## 3. Filter Task

### FilterFlow

The `FilterFlow` class is designed to process and refine task plans by leveraging a `FilterAgent`. The `FilterFlow` class acts as a bridge between the instantiation of tasks and the execution of a filtering process, aiming to refine task steps and prefill task-related files based on predefined filtering criteria.

### FilterAgent

The `FilterAgent` class is a specialized agent used to evaluate whether an instantiated task is correct. It inherits from the BasicAgent class and includes several methods and attributes to handle its functionality.

# Reference

## ChooseTemplateFlow

::: instantiation.workflow.choose_template_flow.ChooseTemplateFlow

## PrefillFlow

::: instantiation.workflow.prefill_flow.PrefillFlow

## PrefillAgent

::: instantiation.agent.prefill_agent.PrefillAgent

## FilterFlow

::: instantiation.workflow.filter_flow.FilterFlow

## FilterAgent

::: instantiation.agent.filter_agent.FilterAgent
