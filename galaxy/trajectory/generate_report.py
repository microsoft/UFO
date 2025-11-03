"""
Galaxy Trajectory Report Generator

Quick script to generate markdown reports for Galaxy task execution logs.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from galaxy.trajectory import GalaxyTrajectory
from rich.console import Console

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Generate Markdown report for Galaxy task execution logs"
    )
    parser.add_argument(
        "log_dir",
        type=str,
        help="Path to Galaxy log directory (e.g., logs/galaxy/task_1)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output markdown file path (default: <log_dir>/trajectory_report.md)",
    )
    parser.add_argument(
        "--no-constellation",
        action="store_true",
        help="Exclude constellation evolution details",
    )
    parser.add_argument(
        "--no-tasks",
        action="store_true",
        help="Exclude detailed task information",
    )
    parser.add_argument(
        "--no-devices",
        action="store_true",
        help="Exclude device connection information",
    )

    args = parser.parse_args()

    # Load trajectory
    console.print(f"[CYAN]Loading trajectory from: {args.log_dir}")

    try:
        trajectory = GalaxyTrajectory(args.log_dir)
    except Exception as e:
        console.print(f"[RED][FAIL] Failed to load trajectory: {e}")
        return 1

    # Display summary
    console.print("\n[BOLD]Trajectory Summary:")
    console.print(f"  - Steps: {trajectory.total_steps}")
    console.print(f"  - Cost: ${trajectory.total_cost:.4f}")
    console.print(f"  - Time: {trajectory.total_time:.2f}s")
    console.print(f"  - Request: {trajectory.request or 'N/A'}\n")

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = str(Path(args.log_dir) / "trajectory_report.md")

    # Generate report
    console.print(f"[CYAN]Generating report: {output_path}")

    try:
        trajectory.to_markdown(
            output_path=output_path,
            include_constellation_details=not args.no_constellation,
            include_task_details=not args.no_tasks,
            include_device_info=not args.no_devices,
        )
    except Exception as e:
        console.print(f"[RED][FAIL] Failed to generate report: {e}")
        import traceback

        traceback.print_exc()
        return 1

    console.print(f"\n[GREEN][OK] Report successfully generated!")
    console.print(f"[GREEN]    Location: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
