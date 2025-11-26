# Execution

The instantiated plans will be executed by a `execute` task. In this phase, given the task-action data, the execution process will match the real controller based on word environment and execute the plan step by step. After execution, `evalution` agent will evaluation the quality of the entire execution process.

<h1 align="center">
    <img src="../../img/execution.png"/> 
</h1>

## ExecuteFlow

The `ExecuteFlow` class is designed to facilitate the execution and evaluation of tasks in a Windows application environment. It provides functionality to interact with the application's UI, execute predefined tasks, capture screenshots, and evaluate the results of the execution. The class also handles logging and error management for the tasks.

### Task Execution

The **task execution** in the `ExecuteFlow` class follows a structured sequence to ensure accurate and traceable task performance:

1. **Initialization**:

   - Load configuration settings and log paths.
   - Find the application window matching the task.
   - Retrieve or create an `ExecuteAgent` for executing the task.
2. **Plan Execution**:

   - Loop through each step in the `instantiated_plan`.
   - Parse the step to extract information like subtasks, control text, and the required operation.
3. **Action Execution**:

   - Find the control in the application window that matches the specified control text.
   - If no matching control is found, raise an error.
   - Perform the specified action (e.g., click, input text) using the agent's Puppeteer framework.
   - Capture screenshots of the application window and selected controls for logging and debugging.
4. **Result Logging**:

   - Log details of the step execution, including control information, performed action, and results.
5. **Finalization**:

   - Save the final state of the application window.
   - Quit the application client gracefully.

---

## Evaluation

The **evaluation** process in the `ExecuteFlow` class is designed to assess the performance of the executed task based on predefined prompts:

1. **Start Evaluation**:

   - Evaluation begins immediately after task execution.
   - It uses an `ExecuteEvalAgent` initialized during class construction.
2. **Perform Evaluation**:

   - The `ExecuteEvalAgent` evaluates the task using a combination of input prompts (e.g., main prompt and API prompt) and logs generated during task execution.
   - The evaluation process outputs a result summary (e.g., quality flag, comments, and task type).
3. **Log and Output Results**:

   - Display the evaluation results in the console.
   - Return the evaluation summary alongside the executed plan for further analysis or reporting.

# Reference

## ExecuteFlow

::: execution.workflow.execute_flow.ExecuteFlow

## ExecuteAgent

::: execution.agent.execute_agent.ExecuteAgent

## ExecuteEvalAgent

::: execution.agent.execute_eval_agent.ExecuteEvalAgent
