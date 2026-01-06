# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Trajectory Parser

Optimized parser for Galaxy agent logs with constellation visualization support.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import networkx as nx
from rich.console import Console

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

logger = logging.getLogger(__name__)
console = Console()


class GalaxyTrajectory:
    """
    A class to structure and visualize Galaxy trajectory data with constellation support.

    This class parses Galaxy response logs (JSONL format) and generates comprehensive
    Markdown documentation including:
    - Constellation evolution (before/after states)
    - Task execution details
    - Dependency graph visualization
    - Agent actions and results
    """

    _response_file = "response.log"
    _evaluation_file = "evaluation.log"

    def __init__(self, folder_path: str) -> None:
        """
        Initialize Galaxy trajectory parser.

        :param folder_path: Path to the Galaxy log directory (e.g., logs/galaxy/task_1)
        """
        self.folder_path = Path(folder_path)
        self._response_file_path = self.folder_path / self._response_file

        if not self._response_file_path.exists():
            raise ValueError(
                f"Response file '{self._response_file_path}' does not exist."
            )

        self._step_log = self._load_response_data()
        self._evaluation_log = self._load_evaluation_data()
        self.logger = logging.getLogger(__name__)

    def _load_response_data(self) -> List[Dict[str, Any]]:
        """Load JSONL response data from log file."""
        step_data = []

        with open(self._response_file_path, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, 1):
                try:
                    line = line.strip()
                    if not line:
                        continue
                    step_log = json.loads(line)
                    step_log["_line_number"] = (
                        line_num  # Track line number for debugging
                    )
                    step_data.append(step_log)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {line_num}: {e}")
                    continue

        return step_data

    def _load_evaluation_data(self) -> Dict[str, Any]:
        """Load evaluation data if available."""
        evaluation_log_path = self.folder_path / self._evaluation_file

        if evaluation_log_path.exists():
            try:
                with open(evaluation_log_path, "r", encoding="utf-8") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to parse evaluation log at {evaluation_log_path}"
                )
                return {}
        else:
            return {}

    @property
    def step_log(self) -> List[Dict[str, Any]]:
        """Get all step logs."""
        return self._step_log

    @property
    def evaluation_log(self) -> Dict[str, Any]:
        """Get evaluation results."""
        return self._evaluation_log

    @property
    def request(self) -> Optional[str]:
        """Get the original user request."""
        if len(self.step_log) == 0:
            return None
        return self.step_log[0].get("request")

    @property
    def total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.step_log)

    @property
    def total_cost(self) -> float:
        """Calculate total LLM cost."""
        return sum(step.get("cost", 0.0) for step in self.step_log)

    @property
    def total_time(self) -> float:
        """Calculate total execution time."""
        return sum(step.get("total_time", 0.0) for step in self.step_log)

    def _parse_constellation(
        self, constellation_json: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Safely parse constellation JSON string with compatibility for string-serialized tasks.

        This method handles both:
        1. Properly formatted constellation JSON (new format after fix)
        2. Legacy format where tasks/dependencies are Python string representations

        :param constellation_json: JSON string of constellation data or dict
        :return: Parsed constellation dict (may include 'parse_error' key) or None
        """
        if not constellation_json:
            return None

        try:
            # Handle case where constellation_json might already be a dict
            # (happens when reading from logs created after the fix)
            if isinstance(constellation_json, dict):
                constellation = constellation_json
            else:
                constellation = json.loads(constellation_json)

            # Compatibility fix: Handle tasks field as string (legacy format)
            if "tasks" in constellation and isinstance(constellation["tasks"], str):
                # Mark as parse error but keep basic info
                constellation["parse_error"] = {
                    "field": "tasks",
                    "error_type": "legacy_serialization_bug",
                    "message": "Tasks field contains Python object representations (not pure JSON). "
                    "This is due to a serialization bug in older versions. "
                    "Cannot reliably parse. Fix is in place for future logs.",
                    "raw_preview": (
                        str(constellation["tasks"])[:200] + "..."
                        if len(constellation["tasks"]) > 200
                        else constellation["tasks"]
                    ),
                }
                logger.warning(
                    "Detected tasks field as Python string representation (legacy format with serialization bug). "
                    "Marking with parse_error in constellation data."
                )
                # Keep the constellation with error info for display
                return constellation

            # Compatibility fix: Handle dependencies field as string (legacy format)
            if "dependencies" in constellation and isinstance(
                constellation["dependencies"], str
            ):
                logger.warning(
                    "Detected dependencies field as Python string representation (legacy format). "
                    "Using empty dependencies for this constellation."
                )
                constellation["dependencies"] = {}

            return constellation

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse constellation JSON: {e}")
            # Return error info instead of None
            return {
                "parse_error": {
                    "field": "constellation",
                    "error_type": "json_decode_error",
                    "message": f"Failed to parse constellation JSON: {str(e)}",
                    "raw_preview": (
                        str(constellation_json)[:200] + "..."
                        if len(str(constellation_json)) > 200
                        else str(constellation_json)
                    ),
                }
            }
        except Exception as e:
            logger.warning(f"Unexpected error parsing constellation: {e}")
            return {
                "parse_error": {
                    "field": "constellation",
                    "error_type": "unexpected_error",
                    "message": f"Unexpected error: {str(e)}",
                }
            }

    def _format_task_table(self, tasks: Dict[str, Any]) -> str:
        """
        Generate markdown table for tasks.

        :param tasks: Dictionary of task_id -> task_data
        :return: Markdown table string
        """
        if not tasks:
            return "_No tasks_\n\n"

        table = "| Task ID | Name | Status | Device | Duration |\n"
        table += "|---------|------|--------|--------|----------|\n"

        for task_id, task in tasks.items():
            name = task.get("name", "N/A")
            status = task.get("status", "N/A")
            device = task.get("target_device_id", "N/A")

            # Calculate duration if available
            duration = "N/A"
            if task.get("execution_duration"):
                duration = f"{task['execution_duration']:.2f}s"

            # Truncate long names
            if len(name) > 40:
                name = name[:37] + "..."

            table += f"| {task_id} | {name} | {status} | {device} | {duration} |\n"

        return table + "\n"

    def _generate_topology_image(
        self,
        dependencies: Dict[str, Any],
        tasks: Dict[str, Any],
        constellation_id: str,
        step_number: int,
        state: str = "before",
    ) -> Optional[str]:
        """
        Generate a beautiful topology graph image using networkx and matplotlib.

        :param dependencies: Dictionary of line_id -> dependency_data
        :param tasks: Dictionary of task_id -> task_data
        :param constellation_id: Constellation ID for unique filename
        :param step_number: Step number for unique filename
        :param state: 'before' or 'after'
        :return: Relative path to the generated image, or None if no tasks
        """
        if not tasks:
            return None

        # Create directed graph
        G = nx.DiGraph()

        # Add all tasks as nodes first (even if no dependencies)
        for task_id in tasks.keys():
            G.add_node(task_id)

        # Add edges with attributes
        satisfied_edges = []
        pending_edges = []

        for line_id, dep in dependencies.items():
            from_task = dep.get("from_task_id", "")
            to_task = dep.get("to_task_id", "")
            is_satisfied = dep.get("is_satisfied", False)

            G.add_edge(from_task, to_task)

            if is_satisfied:
                satisfied_edges.append((from_task, to_task))
            else:
                pending_edges.append((from_task, to_task))

        # Define color scheme for different task statuses
        status_colors = {
            "completed": "#28A745",  # Green - success
            "running": "#17A2B8",  # Cyan - in progress
            "pending": "#6C757D",  # Gray - waiting
            "failed": "#DC3545",  # Red - error
            "error": "#DC3545",  # Red - error
            "cancelled": "#FFC107",  # Yellow - cancelled
        }

        status_border_colors = {
            "completed": "#1E7E34",  # Dark green
            "running": "#117A8B",  # Dark cyan
            "pending": "#495057",  # Dark gray
            "failed": "#BD2130",  # Dark red
            "error": "#BD2130",  # Dark red
            "cancelled": "#E0A800",  # Dark yellow
        }

        # Get node colors based on task status
        node_colors = []
        border_colors = []
        for node in G.nodes():
            task_info = tasks.get(node, {})
            status = str(task_info.get("status", "pending")).lower()
            node_colors.append(status_colors.get(status, "#4A90E2"))  # Default blue
            border_colors.append(
                status_border_colors.get(status, "#2E5C8A")
            )  # Default dark blue

        # Create figure with space for external legend
        fig, ax = plt.subplots(figsize=(9, 4.5), dpi=120)  # Wider to accommodate legend

        # Use hierarchical layout for better visualization
        try:
            # Increase k for more spacing, use more iterations for better layout
            pos = nx.spring_layout(G, k=1.5, iterations=100, seed=42)
        except:
            pos = nx.spring_layout(G, seed=42)

        # Draw nodes with status-based colors using ellipses that adapt to text length
        from matplotlib.patches import Ellipse

        for i, node in enumerate(G.nodes()):
            # Calculate ellipse size based on text length
            text_length = len(str(node))
            # More moderate width scaling with better proportions
            width = max(0.18, 0.035 * text_length)  # Reduced scaling factor
            height = 0.15  # Slightly reduced height for better aspect ratio

            # Create ellipse patch
            ellipse = Ellipse(
                pos[node],
                width=width,
                height=height,
                facecolor=node_colors[i],
                edgecolor=border_colors[i],
                linewidth=2.5,
                alpha=0.95,
                zorder=2,
            )
            ax.add_patch(ellipse)

        # Draw satisfied edges (solid green with better styling)
        if satisfied_edges:
            nx.draw_networkx_edges(
                G,
                pos,
                ax=ax,
                edgelist=satisfied_edges,
                edge_color="#28A745",  # Bootstrap success green
                width=3,
                alpha=0.85,
                arrows=True,
                arrowsize=18,
                arrowstyle="-|>",
                connectionstyle="arc3,rad=0.15",
                min_source_margin=20,
                min_target_margin=20,
            )

        # Draw pending edges (dashed orange with better styling)
        if pending_edges:
            nx.draw_networkx_edges(
                G,
                pos,
                ax=ax,
                edgelist=pending_edges,
                edge_color="#FFA726",  # Warm orange
                width=3,
                alpha=0.85,
                style="dashed",
                arrows=True,
                arrowsize=18,
                arrowstyle="-|>",
                connectionstyle="arc3,rad=0.15",
                min_source_margin=20,
                min_target_margin=20,
            )

        # Draw labels with better styling
        nx.draw_networkx_labels(
            G,
            pos,
            ax=ax,
            font_size=8,  # Reduced to fit better in ellipses
            font_weight="bold",
            font_color="white",
            font_family="sans-serif",
        )

        # Set axis limits to show all nodes properly
        ax.set_xlim(
            [
                min(x for x, y in pos.values()) - 0.2,
                max(x for x, y in pos.values()) + 0.2,
            ]
        )
        ax.set_ylim(
            [
                min(y for x, y in pos.values()) - 0.2,
                max(y for x, y in pos.values()) + 0.2,
            ]
        )
        ax.axis("off")

        # Add title with better styling
        plt.title(
            "Task Dependency Topology",
            fontsize=15,
            fontweight="bold",
            pad=15,
            color="#2C3E50",
        )

        # Create custom legend with better styling
        from matplotlib.lines import Line2D
        from matplotlib.patches import Circle

        # Collect unique statuses present in the graph
        statuses_present = set()
        for node in G.nodes():
            task_info = tasks.get(node, {})
            status = str(task_info.get("status", "pending")).lower()
            statuses_present.add(status)

        # Build legend elements dynamically
        legend_elements = []

        # Add task status legend (nodes)
        status_legend_items = [
            ("completed", "Completed", "#28A745"),
            ("running", "Running", "#17A2B8"),
            ("pending", "Pending", "#6C757D"),
            ("failed", "Failed/Error", "#DC3545"),
        ]

        for status_key, label, color in status_legend_items:
            if status_key in statuses_present or (
                status_key == "failed"
                and ("failed" in statuses_present or "error" in statuses_present)
            ):
                legend_elements.append(
                    Line2D(
                        [0],
                        [0],
                        marker="o",
                        color="w",
                        markerfacecolor=color,
                        markersize=10,
                        label=label,
                        markeredgecolor="black",
                        markeredgewidth=1.5,
                    )
                )

        # Add separator
        if legend_elements:
            legend_elements.append(
                Line2D([0], [0], color="none", label="")
            )  # Empty line

        # Add edge legend (dependencies)
        legend_elements.extend(
            [
                Line2D(
                    [0],
                    [0],
                    color="#28A745",
                    linewidth=3,
                    label="Dependency: Satisfied",
                ),
                Line2D(
                    [0],
                    [0],
                    color="#FFA726",
                    linewidth=3,
                    linestyle="--",
                    label="Dependency: Pending",
                ),
            ]
        )

        ax.legend(
            handles=legend_elements,
            loc="upper left",
            bbox_to_anchor=(1.02, 1),  # Place legend outside the plot area
            fontsize=9,
            framealpha=0.95,
            edgecolor="#CCCCCC",
            ncol=1,
        )

        plt.tight_layout()

        # Save image with optimized settings
        image_dir = self.folder_path / "topology_images"
        image_dir.mkdir(exist_ok=True)

        # Clean constellation_id for filename
        clean_id = constellation_id.replace(":", "_").replace("/", "_")
        image_filename = f"step{step_number}_{state}_{clean_id}.png"
        image_path = image_dir / image_filename

        # Use higher DPI for clarity but smaller figure size keeps file size reasonable
        plt.savefig(
            image_path,
            dpi=120,  # Reduced from 150 for smaller file size
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
            pad_inches=0.3,
        )
        plt.close("all")  # Close all figures to free memory

        # Return relative path from markdown file location
        return f"topology_images/{image_filename}"

    def _format_dependency_graph(
        self,
        dependencies: Dict[str, Any],
        tasks: Dict[str, Any],
        constellation_id: str = "",
        step_number: int = 0,
        state: str = "before",
    ) -> str:
        """
        Generate dependency graph visualization with image.

        :param dependencies: Dictionary of line_id -> dependency_data
        :param tasks: Dictionary of task_id -> task_data
        :param constellation_id: Constellation ID for image filename
        :param step_number: Step number for image filename
        :param state: 'before' or 'after'
        :return: Markdown with embedded image
        """
        if not tasks:
            return "_No tasks_\n\n"

        md = ""

        # Generate topology image (even if no dependencies, show task nodes)
        image_path = self._generate_topology_image(
            dependencies, tasks, constellation_id, step_number, state
        )

        if image_path:
            # Use HTML img tag with width control for better display sizing
            md += f'<img src="{image_path}" alt="Topology Graph" width="600">\n\n'
        else:
            md += "_Failed to generate topology image_\n\n"

        return md

    def _format_dependency_details(self, dependencies: Dict[str, Any]) -> str:
        """
        Generate detailed dependency/edge information.

        :param dependencies: Dictionary of line_id -> dependency_data
        :return: Formatted markdown string
        """
        if not dependencies:
            return ""

        # Summary table
        md = "| Line ID | From Task | To Task | Type | Satisfied | Condition |\n"
        md += "|---------|-----------|---------|------|-----------|----------|\n"

        for line_id, dep in dependencies.items():
            from_task = dep.get("from_task_id", "N/A")
            to_task = dep.get("to_task_id", "N/A")
            dep_type = dep.get("dependency_type", "N/A")
            is_satisfied = "[OK]" if dep.get("is_satisfied", False) else "[PENDING]"
            condition = dep.get("condition_description", "N/A")

            # Truncate long condition descriptions in table
            if len(condition) > 50:
                condition = condition[:47] + "..."

            md += f"| {line_id} | {from_task} | {to_task} | {dep_type} | {is_satisfied} | {condition} |\n"

        md += "\n"

        # Detailed information for each dependency
        md += "<details>\n<summary>Detailed Dependency Information (click to expand)</summary>\n\n"

        for line_id, dep in dependencies.items():
            md += f"#### Dependency {line_id}: {dep.get('from_task_id', 'N/A')} → {dep.get('to_task_id', 'N/A')}\n\n"

            # Basic info
            md += f"- **Type**: {dep.get('dependency_type', 'N/A')}\n"
            md += f"- **Satisfied**: {'Yes' if dep.get('is_satisfied', False) else 'No'}\n"

            # Full condition description (no truncation)
            if condition_desc := dep.get("condition_description"):
                # Handle multiline condition descriptions
                condition_lines = str(condition_desc).split("\n")
                if len(condition_lines) == 1:
                    md += f"- **Condition**: {condition_desc}\n"
                else:
                    md += f"- **Condition**:\n"
                    for line in condition_lines:
                        md += f"  {line}\n"

            # Evaluation info
            if last_eval := dep.get("last_evaluation_result"):
                md += f"- **Last Evaluation**: {last_eval}\n"
            if last_eval_time := dep.get("last_evaluation_time"):
                md += f"- **Last Evaluation Time**: {last_eval_time}\n"

            # Metadata
            if metadata := dep.get("metadata"):
                if metadata:  # Only show if not empty
                    md += f"- **Metadata**: {metadata}\n"

            # Timestamps
            if created := dep.get("created_at"):
                md += f"- **Created**: {created}\n"
            if updated := dep.get("updated_at"):
                md += f"- **Updated**: {updated}\n"

            md += "\n"

        md += "</details>\n\n"

        return md

    def _format_task_details(self, tasks: Dict[str, Any]) -> str:
        """
        Generate detailed task information.

        :param tasks: Dictionary of task_id -> task_data
        :return: Formatted markdown string
        """
        if not tasks:
            return ""

        md = ""
        for task_id, task in tasks.items():
            md += f"#### Task {task_id}: {task.get('name', 'Unnamed Task')}\n\n"
            md += f"- **Status**: {task.get('status', 'N/A')}\n"
            md += f"- **Target Device**: {task.get('target_device_id', 'N/A')}\n"
            md += f"- **Priority**: {task.get('priority', 'N/A')}\n"

            # Description - handle multiline text
            if desc := task.get("description"):
                # Indent continuation lines to maintain list structure
                desc_lines = str(desc).split("\n")
                if len(desc_lines) == 1:
                    md += f"- **Description**: {desc}\n"
                else:
                    md += f"- **Description**: {desc_lines[0]}\n"
                    for line in desc_lines[1:]:
                        md += f"  {line}\n"

            # Tips - handle multiline text in each tip
            if tips := task.get("tips"):
                md += f"- **Tips**:\n"
                for tip in tips[:3]:  # Show max 3 tips
                    # Indent continuation lines of each tip
                    tip_lines = str(tip).split("\n")
                    if len(tip_lines) == 1:
                        md += f"  - {tip}\n"
                    else:
                        md += f"  - {tip_lines[0]}\n"
                        for line in tip_lines[1:]:
                            md += f"    {line}\n"

            # Result
            if result := task.get("result"):
                md += f"- **Result**: \n"
                if isinstance(result, dict):
                    if result_data := result.get("result"):
                        # Handle list of results
                        if isinstance(result_data, list) and len(result_data) > 0:
                            for r in result_data:
                                if isinstance(r, dict) and "result" in r:
                                    # Indent each line of the result
                                    indented = "\n  ".join(str(r["result"]).split("\n"))
                                    md += f"  ```\n  {indented}\n  ```\n"
                        else:
                            # Indent each line of the result
                            indented = "\n  ".join(str(result_data).split("\n"))
                            md += f"  ```\n  {indented}\n  ```\n"
                else:
                    # Indent each line of the result
                    indented = "\n  ".join(str(result).split("\n"))
                    md += f"  ```\n  {indented}\n  ```\n"

            # Error - handle multiline text
            if error := task.get("error"):
                # Keep error in code block to preserve formatting
                error_lines = str(error).split("\n")
                if len(error_lines) == 1:
                    md += f"- **Error**: `{error}`\n"
                else:
                    md += f"- **Error**:\n"
                    md += f"  ```\n"
                    for line in error_lines:
                        md += f"  {line}\n"
                    md += f"  ```\n"

            # Timing
            if start_time := task.get("execution_start_time"):
                md += f"- **Started**: {start_time}\n"
            if end_time := task.get("execution_end_time"):
                md += f"- **Ended**: {end_time}\n"
            if duration := task.get("execution_duration"):
                md += f"- **Duration**: {duration:.2f}s\n"

            md += "\n"

        return md

    def to_markdown(
        self,
        output_path: str,
        include_constellation_details: bool = True,
        include_task_details: bool = True,
        include_device_info: bool = True,
    ) -> None:
        """
        Export trajectory to a comprehensive Markdown file.

        :param output_path: Path to save the markdown file
        :param include_constellation_details: Include detailed constellation evolution
        :param include_task_details: Include detailed task information
        :param include_device_info: Include device connection information
        """

        if len(self.step_log) == 0:
            logger.warning("No step data to export. Creating empty report.")
            with open(output_path, "w", encoding="utf-8") as file:
                file.write("# Galaxy Trajectory Report\n\n")
                file.write("[WARN] No trajectory data found\n\n")
                file.write("The response.log file contains no valid JSON entries.\n")
            return

        with open(output_path, "w", encoding="utf-8") as file:
            # Header
            file.write("# Galaxy Trajectory Report\n\n")
            file.write(f"**Log Directory**: `{self.folder_path}`\n\n")
            file.write("---\n\n")

            # Executive Summary
            file.write("## Executive Summary\n\n")
            file.write(f"- **User Request**: {self.request or 'Not specified'}\n")
            file.write(f"- **Total Steps**: {self.total_steps}\n")
            file.write(f"- **Total Time**: {self.total_time:.2f}s\n\n")

            # Evaluation Results
            if self.evaluation_log:
                file.write("## Evaluation Results\n\n")
                for key, value in self.evaluation_log.items():
                    file.write(f"- **{key.replace('_', ' ').title()}**: {value}\n")
                file.write("\n")

            # Step-by-step breakdown
            file.write("---\n\n")
            file.write("## Step-by-Step Execution\n\n")

            for idx, step in enumerate(self.step_log, 1):
                file.write(f"### Step {idx}\n\n")

                # Basic step info
                file.write(
                    f"- **Agent**: {step.get('agent_name', 'N/A')} ({step.get('agent_type', 'N/A')})\n"
                )
                file.write(f"- **Status**: {step.get('status', 'N/A')}\n")
                file.write(
                    f"- **Round**: {step.get('round_num', 'N/A')} | **Round Step**: {step.get('round_step', 'N/A')}\n"
                )

                # Timing and cost
                if total_time := step.get("total_time"):
                    file.write(f"- **Execution Time**: {total_time:.2f}s\n")
                if cost := step.get("cost"):
                    file.write(f"- **Cost**: ${cost:.4f}\n")

                # Execution time breakdown
                if exec_times := step.get("execution_times"):
                    file.write(f"- **Time Breakdown**:\n")
                    for key, value in exec_times.items():
                        if value > 0:
                            file.write(f"  - {key}: {value:.2f}s\n")

                file.write("\n")

                # Actions
                if actions := step.get("action"):
                    file.write("#### Actions Performed\n\n")
                    for action in actions:
                        function = action.get("function", "unknown")
                        file.write(f"**Function**: `{function}`\n\n")

                        # Show arguments in collapsible format
                        if arguments := action.get("arguments"):
                            file.write(
                                "<details>\n<summary>Arguments (click to expand)</summary>\n\n"
                            )
                            file.write("```json\n")
                            file.write(
                                json.dumps(arguments, indent=2, ensure_ascii=False)
                            )
                            file.write("\n```\n\n")
                            file.write("</details>\n\n")

                # Constellation Evolution
                if include_constellation_details:
                    constellation_before = self._parse_constellation(
                        step.get("constellation_before")
                    )
                    constellation_after = self._parse_constellation(
                        step.get("constellation_after")
                    )

                    if constellation_before or constellation_after:
                        file.write("#### Constellation Evolution\n\n")

                        # Before state
                        if constellation_before:
                            file.write(
                                "<details>\n<summary>Constellation BEFORE (click to expand)</summary>\n\n"
                            )
                            file.write(
                                f"**Constellation ID**: {constellation_before.get('constellation_id', 'N/A')}\n"
                            )
                            file.write(
                                f"**State**: {constellation_before.get('state', 'N/A')}\n\n"
                            )

                            # Check for parse errors
                            if "parse_error" in constellation_before:
                                error_info = constellation_before["parse_error"]
                                file.write("##### ⚠️ Parse Error\n\n")
                                file.write(
                                    f"**Error Type**: `{error_info.get('error_type', 'unknown')}`\n\n"
                                )
                                file.write(
                                    f"**Message**: {error_info.get('message', 'N/A')}\n\n"
                                )

                                if "raw_preview" in error_info:
                                    file.write(
                                        "<details>\n<summary>Raw Data Preview (first 200 chars)</summary>\n\n"
                                    )
                                    file.write("```\n")
                                    file.write(error_info["raw_preview"])
                                    file.write("\n```\n\n")
                                    file.write("</details>\n\n")

                                file.write(
                                    "**Note**: This constellation cannot be fully parsed. "
                                    "Basic metadata shown above. "
                                    "This issue is fixed in newer versions.\n\n"
                                )
                            else:
                                # Normal parsing - show full details
                                tasks = constellation_before.get("tasks", {})
                                deps = constellation_before.get("dependencies", {})

                                # Show topology graph first (at the top) - show even if no dependencies
                                if tasks and isinstance(tasks, dict):
                                    file.write("##### Dependency Graph (Topology)\n\n")
                                    file.write(
                                        self._format_dependency_graph(
                                            deps,
                                            tasks,
                                            constellation_before.get(
                                                "constellation_id", "unknown"
                                            ),
                                            idx,
                                            "before",
                                        )
                                    )

                                if tasks and isinstance(tasks, dict):
                                    file.write("##### Task Summary Table\n\n")
                                    file.write(self._format_task_table(tasks))

                                    file.write("##### Detailed Task Information\n\n")
                                    file.write(self._format_task_details(tasks))

                                    # Dependency details (table and detailed info)
                                    if deps:
                                        file.write("##### Dependency Details\n\n")
                                        file.write(
                                            self._format_dependency_details(deps)
                                        )

                            file.write("</details>\n\n")

                        # After state
                        if constellation_after:
                            file.write(
                                "<details>\n<summary>Constellation AFTER (click to expand)</summary>\n\n"
                            )
                            file.write(
                                f"**Constellation ID**: {constellation_after.get('constellation_id', 'N/A')}\n"
                            )
                            file.write(
                                f"**State**: {constellation_after.get('state', 'N/A')}\n\n"
                            )

                            # Check for parse errors
                            if "parse_error" in constellation_after:
                                error_info = constellation_after["parse_error"]
                                file.write("##### ⚠️ Parse Error\n\n")
                                file.write(
                                    f"**Error Type**: `{error_info.get('error_type', 'unknown')}`\n\n"
                                )
                                file.write(
                                    f"**Message**: {error_info.get('message', 'N/A')}\n\n"
                                )

                                if "raw_preview" in error_info:
                                    file.write(
                                        "<details>\n<summary>Raw Data Preview (first 200 chars)</summary>\n\n"
                                    )
                                    file.write("```\n")
                                    file.write(error_info["raw_preview"])
                                    file.write("\n```\n\n")
                                    file.write("</details>\n\n")

                                file.write(
                                    "**Note**: This constellation cannot be fully parsed. "
                                    "Basic metadata shown above. "
                                    "This issue is fixed in newer versions.\n\n"
                                )
                            else:
                                # Normal parsing - show full details
                                tasks = constellation_after.get("tasks", {})
                                deps = constellation_after.get("dependencies", {})

                                # Show topology graph first (at the top) - show even if no dependencies
                                if tasks and isinstance(tasks, dict):
                                    file.write("##### Dependency Graph (Topology)\n\n")
                                    file.write(
                                        self._format_dependency_graph(
                                            deps,
                                            tasks,
                                            constellation_after.get(
                                                "constellation_id", "unknown"
                                            ),
                                            idx,
                                            "after",
                                        )
                                    )

                                if tasks and isinstance(tasks, dict):
                                    file.write("##### Task Summary Table\n\n")
                                    file.write(self._format_task_table(tasks))

                                    file.write("##### Detailed Task Information\n\n")
                                    file.write(self._format_task_details(tasks))

                                    # Dependency details (table and detailed info)
                                    if deps:
                                        file.write("##### Dependency Details\n\n")
                                        file.write(
                                            self._format_dependency_details(deps)
                                        )

                            file.write("</details>\n\n")

                # Device Information
                if include_device_info and (device_info := step.get("device_info")):
                    file.write("<details>\n<summary>Connected Devices</summary>\n\n")
                    file.write("| Device ID | OS | Status | Last Heartbeat |\n")
                    file.write("|-----------|----|---------|--------------|\n")

                    for device_id, device in device_info.items():
                        device_os = device.get("os", "N/A")
                        status = device.get("status", "N/A")
                        heartbeat = device.get("last_heartbeat", "N/A")
                        if len(heartbeat) > 19:
                            heartbeat = heartbeat[:19]  # Truncate timestamp
                        file.write(
                            f"| {device_id} | {device_os} | {status} | {heartbeat} |\n"
                        )

                    file.write("\n</details>\n\n")

                file.write("---\n\n")

            # Final Constellation State (if available)
            if self.step_log:
                last_step = self.step_log[-1]
                final_constellation = self._parse_constellation(
                    last_step.get("constellation_after")
                )

                if final_constellation and include_task_details:
                    file.write("## Final Constellation State\n\n")
                    file.write(
                        f"**ID**: {final_constellation.get('constellation_id', 'N/A')}\n"
                    )
                    file.write(
                        f"**State**: {final_constellation.get('state', 'N/A')}\n"
                    )
                    file.write(
                        f"**Created**: {final_constellation.get('created_at', 'N/A')}\n"
                    )
                    file.write(
                        f"**Updated**: {final_constellation.get('updated_at', 'N/A')}\n\n"
                    )

                    tasks = final_constellation.get("tasks", {})
                    if tasks and isinstance(tasks, dict):
                        file.write("### Task Details\n\n")
                        file.write(self._format_task_details(tasks))

                        file.write("### Task Summary Table\n\n")
                        file.write(self._format_task_table(tasks))

                        # Show final topology graph - even if no dependencies
                        deps = final_constellation.get("dependencies", {})
                        file.write("### Final Dependency Graph\n\n")
                        file.write(
                            self._format_dependency_graph(
                                deps,
                                tasks,
                                final_constellation.get("constellation_id", "final"),
                                999,  # Use 999 for final summary
                                "final",
                            )
                        )

        console.print(f"[OK] Markdown report saved to {output_path}", style="green")


if __name__ == "__main__":
    """Process all Galaxy task logs and generate markdown reports."""

    console.print(
        "[BOLD BLUE] Galaxy Trajectory Parser - Batch Mode", style="blue bold"
    )

    import sys
    from pathlib import Path

    # Get all task directories
    galaxy_logs_dir = Path("logs/galaxy")
    if not galaxy_logs_dir.exists():
        console.print(f"[FAIL] Directory not found: {galaxy_logs_dir}", style="red")
        sys.exit(1)

    task_dirs = sorted([d for d in galaxy_logs_dir.iterdir() if d.is_dir()])

    if not task_dirs:
        console.print(
            f"[FAIL] No task directories found in {galaxy_logs_dir}", style="red"
        )
        sys.exit(1)

    console.print(f"Found {len(task_dirs)} task directories\n", style="cyan")

    success_count = 0
    error_count = 0
    skipped_count = 0

    for task_dir in task_dirs:
        task_name = task_dir.name
        console.print(f"Processing {task_name}...", style="yellow", end=" ")

        try:
            # Check if response.log exists
            response_log = task_dir / "response.log"
            if not response_log.exists():
                console.print("[SKIP] No response.log", style="dim")
                skipped_count += 1
                continue

            trajectory = GalaxyTrajectory(str(task_dir))

            # Generate markdown
            output_path = task_dir / "trajectory_report.md"
            trajectory.to_markdown(str(output_path))

            console.print("[OK]", style="green")
            success_count += 1

        except Exception as e:
            console.print(f"[FAIL] {str(e)[:50]}", style="red")
            error_count += 1

    # Summary
    console.print("\n" + "=" * 60, style="cyan")
    console.print(f"[BOLD] Summary:", style="cyan bold")
    console.print(f"  Total: {len(task_dirs)}", style="white")
    console.print(f"  Success: {success_count}", style="green")
    console.print(f"  Skipped: {skipped_count}", style="yellow")
    console.print(f"  Failed: {error_count}", style="red")
    console.print("=" * 60, style="cyan")
