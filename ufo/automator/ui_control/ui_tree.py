# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import copy
import json
import os
import traceback
from typing import Any, Dict, List

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.automator.ui_control.screenshot import PhotographerDecorator


class UITree:
    """
    A class to represent the UI tree.
    """

    def __init__(self, root: UIAWrapper):
        """
        Initialize the UI tree with the root element.
        :param root: The root element of the UI tree.
        """
        self.root = root

        # The node counter to count the number of nodes in the UI tree.
        self.node_counter = 0

        try:
            self._ui_tree = self._get_ui_tree(self.root)
        except Exception as e:
            self._ui_tree = {"error": traceback.format_exc()}

    def _generate_node_id(self) -> str:
        """
        Generate a unique ID for each node.
        """
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        return node_id

    def _get_ui_tree(self, root: UIAWrapper, level: int = 0) -> Dict[str, Any]:
        """
        Get the UI tree.
        :param root: The root element of the UI tree.
        :param level: The level of the root element.
        """

        # Get the adjusted rectangle and relative rectangle, left, top, right, bottom
        adjusted_rect = PhotographerDecorator.coordinate_adjusted(
            self.root.element_info.rectangle, root.element_info.rectangle
        )

        # Get the relative rectangle in ratio, left, top, right, bottom
        relative_rect = PhotographerDecorator.coordinate_adjusted_to_relative(
            self.root.element_info.rectangle, root.element_info.rectangle
        )

        node_id = self._generate_node_id()

        ui_tree = {
            "id": node_id,
            "name": root.element_info.name,
            "control_type": root.element_info.control_type,
            "rectangle": {
                "left": root.element_info.rectangle.left,
                "top": root.element_info.rectangle.top,
                "right": root.element_info.rectangle.right,
                "bottom": root.element_info.rectangle.bottom,
            },
            "adjusted_rectangle": {
                "left": adjusted_rect[0],
                "top": adjusted_rect[1],
                "right": adjusted_rect[2],
                "bottom": adjusted_rect[3],
            },
            "relative_rectangle": {
                "left": relative_rect[0],
                "top": relative_rect[1],
                "right": relative_rect[2],
                "bottom": relative_rect[3],
            },
            "level": level,
            "children": [],
        }

        for child in root.children():
            try:
                ui_tree["children"].append(self._get_ui_tree(child, level + 1))
            except Exception as e:
                ui_tree["error"] = traceback.format_exc()

        return ui_tree

    @property
    def ui_tree(self) -> Dict[str, Any]:
        """
        The UI tree.
        """
        return self._ui_tree

    def save_ui_tree_to_json(self, file_path: str) -> None:
        """
        Save the UI tree to a JSON file.
        :param file_path: The file path to save the UI tree.
        """

        # Check if the file directory exists. If not, create it.
        save_dir = os.path.dirname(file_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        with open(file_path, "w") as file:
            json.dump(self.ui_tree, file, indent=4)

    def flatten_ui_tree(self) -> List[Dict[str, Any]]:
        """
        Flatten the UI tree into a list in width-first order.
        """

        def flatten_tree(tree: Dict[str, Any], result: List[Dict[str, Any]]):
            """
            Flatten the tree.
            :param tree: The tree to flatten.
            :param result: The result list.
            """

            tree_info = {
                "name": tree["name"],
                "control_type": tree["control_type"],
                "rectangle": tree["rectangle"],
                "adjusted_rectangle": tree["adjusted_rectangle"],
                "relative_rectangle": tree["relative_rectangle"],
                "level": tree["level"],
            }

            result.append(tree_info)
            for child in tree.get("children", []):
                flatten_tree(child, result)

        result = []
        flatten_tree(self.ui_tree, result)
        return result

    @staticmethod
    def ui_tree_diff(ui_tree_1: Dict[str, Any], ui_tree_2: Dict[str, Any]):
        """
        Compute the difference between two UI trees.
        :param ui_tree_1: The first UI tree.
        :param ui_tree_2: The second UI tree.
        :return: The difference between the two UI trees.
        """

        diff = {"added": [], "removed": [], "modified": []}

        def compare_nodes(node1, node2, path):
            # Note: `path` is a list of IDs. The last element corresponds to the current node.
            # If node1 doesn't exist and node2 does, it's an addition.
            if node1 is None and node2 is not None:
                diff["added"].append({"path": path, "node": copy.deepcopy(node2)})
                return

            # If node1 exists and node2 doesn't, it's a removal.
            if node1 is not None and node2 is None:
                diff["removed"].append({"path": path, "node": copy.deepcopy(node1)})
                return

            # If both don't exist, nothing to do.
            if node1 is None and node2 is None:
                return

            # Both nodes exist, check for modifications at this node
            fields_to_compare = [
                "name",
                "control_type",
                "rectangle",
                "adjusted_rectangle",
                "relative_rectangle",
                "level",
            ]

            changes = {}
            for field in fields_to_compare:
                if node1[field] != node2[field]:
                    changes[field] = (node1[field], node2[field])

            if changes:
                diff["modified"].append({"path": path, "changes": changes})

            # Compare children
            children1 = node1.get("children", [])
            children2 = node2.get("children", [])

            # We'll assume children order is stable. If not, differences will appear as adds/removes.
            max_len = max(len(children1), len(children2))
            for i in range(max_len):
                c1 = children1[i] if i < len(children1) else None
                c2 = children2[i] if i < len(children2) else None
                # Use the child's id if available from c2 (prefer new tree), else from c1
                if c2 is not None:
                    child_id = c2["id"]
                elif c1 is not None:
                    child_id = c1["id"]
                else:
                    # Both None shouldn't happen since max_len ensures one must exist
                    child_id = "unknown_child_id"

                compare_nodes(c1, c2, path + [child_id])

        # Initialize the path with the root node id if it exists
        if ui_tree_2 and "id" in ui_tree_2:
            root_id = ui_tree_2["id"]
        elif ui_tree_1 and "id" in ui_tree_1:
            root_id = ui_tree_1["id"]
        else:
            # If no root id is present, assume a placeholder
            root_id = "root"

        compare_nodes(ui_tree_1, ui_tree_2, [root_id])

        return diff

    @staticmethod
    def apply_ui_tree_diff(
        ui_tree_1: Dict[str, Any], diff: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply a UI tree diff to ui_tree_1 to get ui_tree_2.
        :param ui_tree_1: The original UI tree.
        :param diff: The diff to apply.
        :return: The new UI tree after applying the diff.
        """

        ui_tree_2 = copy.deepcopy(ui_tree_1)

        # Build an ID map for quick node lookups
        def build_id_map(node, id_map):
            id_map[node["id"]] = node
            for child in node.get("children", []):
                build_id_map(child, id_map)

        id_map = {}
        if "id" in ui_tree_2:
            build_id_map(ui_tree_2, id_map)

        def remove_node_by_path(path):
            # The path is a list of IDs from root to target node.
            # The target node is the last element. Its parent is the second to last element.
            if len(path) == 1:
                # Removing the root
                for k in list(ui_tree_2.keys()):
                    del ui_tree_2[k]
                id_map.clear()
                return

            target_id = path[-1]
            parent_id = path[-2]
            parent_node = id_map[parent_id]
            # Find and remove the child with target_id
            for i, c in enumerate(parent_node.get("children", [])):
                if c["id"] == target_id:
                    parent_node["children"].pop(i)
                    break

            # Remove target_id from id_map
            if target_id in id_map:
                del id_map[target_id]

        def add_node_by_path(path, node):
            # Add the node at the specified path. The parent is path[-2], the node is path[-1].
            # The path[-1] should be node["id"].
            if len(path) == 1:
                # Replacing the root node entirely
                for k in list(ui_tree_2.keys()):
                    del ui_tree_2[k]
                for k, v in node.items():
                    ui_tree_2[k] = v
                # Rebuild id_map
                id_map.clear()
                if "id" in ui_tree_2:
                    build_id_map(ui_tree_2, id_map)
                return

            target_id = path[-1]
            parent_id = path[-2]
            parent_node = id_map[parent_id]
            # Ensure children list exists
            if "children" not in parent_node:
                parent_node["children"] = []
            # Insert or append the node
            # We don't have a numeric index anymore, we just append, assuming order doesn't matter.
            # If order matters, we must store ordering info or do some heuristic.
            parent_node["children"].append(node)

            # Update the id_map with the newly added subtree
            build_id_map(node, id_map)

        def modify_node_by_path(path, changes):
            # Modify fields of the node at the given ID
            target_id = path[-1]
            node = id_map[target_id]
            for field, (old_val, new_val) in changes.items():
                node[field] = new_val

        # Apply removals first
        # Sort removals by length of path descending so we remove deeper nodes first.
        # This ensures we don't remove parents before children.
        for removal in sorted(
            diff["removed"], key=lambda x: len(x["path"]), reverse=True
        ):
            remove_node_by_path(removal["path"])

        # Apply additions
        # Additions can be applied directly.
        for addition in diff["added"]:
            add_node_by_path(addition["path"], addition["node"])

        # Apply modifications
        for modification in diff["modified"]:
            modify_node_by_path(modification["path"], modification["changes"])

        return ui_tree_2
