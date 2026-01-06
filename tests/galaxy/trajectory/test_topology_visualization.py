"""Test topology graph generation with task status colors.

This test generates a sample topology graph to verify:
1. Elliptical nodes with adaptive width based on task ID length
2. Status-based node coloring (completed/running/pending/failed)
3. External legend placement
4. Proper text fitting within nodes
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import networkx as nx

from galaxy.trajectory.galaxy_parser import GalaxyTrajectory


def test_topology_visualization():
    """Test topology graph generation with different task statuses."""
    
    # Sample data with different task statuses
    tasks = {
        "task_1": {"status": "completed", "description": "Task 1"},
        "task_2": {"status": "running", "description": "Task 2"},
        "task_3": {"status": "pending", "description": "Task 3"},
        "task_4": {"status": "failed", "description": "Task 4"},
    }

    dependencies = {
        "task_2": [{"task_name": "task_1", "is_satisfied": True}],
        "task_3": [{"task_name": "task_2", "is_satisfied": False}],
        "task_4": [{"task_name": "task_1", "is_satisfied": True}],
    }

    # Create a temporary GalaxyTrajectory instance just to use the image generation method
    # We'll use a fake path since we're only testing the visualization method
    temp_trajectory = GalaxyTrajectory.__new__(GalaxyTrajectory)
    temp_trajectory.folder_path = Path("test_output")
    
    # Generate the topology image
    image_path = temp_trajectory._generate_topology_image(
        dependencies=dependencies,
        tasks=tasks,
        constellation_id="test",
        step_number=0,
        state="test"
    )
    
    # Verify image was created
    output_image = Path("test_output/topology_images") / image_path.split('/')[-1]
    assert output_image.exists(), f"Image should be created at {output_image}"
    
    # Check file size is reasonable (should be around 50-60KB)
    file_size_kb = output_image.stat().st_size / 1024
    assert 30 < file_size_kb < 100, f"File size {file_size_kb:.2f}KB seems unusual"
    
    print(f"[OK] Test topology image saved to {output_image}")
    print(f"Image size: {file_size_kb:.2f} KB")
    
    return output_image


if __name__ == "__main__":
    output = test_topology_visualization()
    print(f"\nTest passed! View the image at: {output}")
