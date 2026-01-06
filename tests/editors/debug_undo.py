#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from galaxy.constellation.editor import ConstellationEditor
from galaxy.constellation.editor.command_interface import IUndoableCommand
from galaxy.constellation.editor.commands import AddTaskCommand
from galaxy.constellation.task_star import TaskStar


def test_simple_undo():
    """Test simple undo functionality."""
    print("Testing simple undo...")

    editor = ConstellationEditor()
    print(
        f"Initial state: tasks={len(editor.list_tasks())}, can_undo={editor.can_undo()}"
    )

    # Create command directly
    task = TaskStar(task_id="test_task", description="Direct test")
    command = AddTaskCommand(editor.constellation, task)

    print(f"Command is IUndoableCommand: {isinstance(command, IUndoableCommand)}")
    print(f"Command can execute: {command.can_execute()}")

    # Execute directly through invoker
    result = editor.invoker.execute(command)
    print(
        f"After direct execution: tasks={len(editor.list_tasks())}, can_undo={editor.can_undo()}"
    )
    print(f"History size: {editor.invoker.history_size}")
    print(f"Command executed: {command.is_executed}")
    print(f"Command can_undo: {command.can_undo()}")


if __name__ == "__main__":
    test_simple_undo()
