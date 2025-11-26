# Screenshot Logs

UFO captures screenshots at every step for debugging and evaluation purposes. All screenshots are stored in the `logs/{task_name}/` directory.

## Screenshot Types

### 1. Clean Screenshots

Unmodified screenshots of the desktop or application window.

**File naming:**

- Step screenshots: `action_step{step_number}.png`
- Subtask completion: `action_round_{round_id}_sub_round_{sub_task_id}_final.png`
- Round completion: `action_round_{round_id}_final.png`
- Session completion: `action_step_final.png`

**Example:**

<h1 align="center">
    <img src="../../img/action_step2.png" alt="Clean Screenshot" width="100%">
</h1>

### 2. Annotated Screenshots

Screenshots with UI controls labeled using the [Set-of-Mark](https://arxiv.org/pdf/2310.11441) paradigm. Each interactive control is marked with a number for reference.

**File naming:** `action_step{step_number}_annotated.png`

**Example:**

<h1 align="center">
    <img src="../../img/action_step2_annotated.png" alt="Annotated Screenshot" width="100%">
</h1>

Only control types configured in `CONTROL_LIST` (in `config_dev.yaml`) are annotated. Different control types use different colors, configurable via `ANNOTATION_COLORS`.

### 3. Concatenated Screenshots

Clean and annotated screenshots placed side-by-side for comparison.

**File naming:** `action_step{step_number}_concat.png`

**Example:**

<h1 align="center">
    <img src="../../img/action_step2_concat.png" alt="Concatenated Screenshot" width="100%">
</h1>

Configure whether to feed concatenated or separate screenshots to LLMs using `CONCAT_SCREENSHOT` in `config_dev.yaml`.

### 4. Selected Control Screenshots

Close-up view of the control element selected for interaction in the previous step.

**File naming:** `action_step{step_number}_selected_controls.png`

**Example:**

<h1 align="center">
    <img src="../../img/action_step2_selected_controls.png" alt="Selected Control Screenshot" width="100%">
</h1>

Enable/disable sending selected control screenshots to LLM using `INCLUDE_LAST_SCREENSHOT` in `config_dev.yaml`.