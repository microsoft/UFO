#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from galaxy.constellation.editor import ConstellationEditor


def test_only_undo():
    """Test only the undo functionality."""
    print("Testing ONLY undo functionality...")

    editor = ConstellationEditor()
    print(f"Editor created - History enabled: {editor.invoker._enable_history}")
    print(f"Editor history exists: {editor.invoker._history is not None}")

    # Add a task
    print("Creating and adding task...")
    task1 = editor.create_and_add_task("task1", "Test task")
    print(f"Task created: {task1.task_id}")

    print(f"Tasks count: {len(editor.list_tasks())}")
    print(f"History size: {editor.invoker.history_size}")
    print(f"Execution count: {editor.invoker.execution_count}")
    print(f"Can undo: {editor.can_undo()}")

    if editor.can_undo():
        print("Attempting undo...")
        success = editor.undo()
        print(f"Undo successful: {success}")
        print(f"Tasks after undo: {len(editor.list_tasks())}")
    else:
        print("Cannot undo - history issue!")


if __name__ == "__main__":
    test_only_undo()
