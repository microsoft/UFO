# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Path validation utilities for preventing path traversal attacks (CWE-22).

Provides functions to validate and sanitize file paths, ensuring they
stay within allowed directories and don't traverse to sensitive locations.
"""

import ntpath
import os
import posixpath
import re
from pathlib import Path
from typing import Optional, Sequence


# System-sensitive directories that should never be written to
_SENSITIVE_DIRS_WINDOWS = [
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
]

_SENSITIVE_DIRS_LINUX = [
    "/bin",
    "/sbin",
    "/usr/bin",
    "/usr/sbin",
    "/etc",
    "/boot",
    "/dev",
    "/proc",
    "/sys",
    "/var/run",
    "/lib",
    "/lib64",
]

_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *{f"COM{index}" for index in range(1, 10)},
    *{f"LPT{index}" for index in range(1, 10)},
}


def _path_module_for(*path_strs: str):
    for path_str in path_strs:
        if not path_str:
            continue
        if path_str.startswith("/"):
            return ntpath if os.name == "nt" else posixpath
        if path_str.startswith("\\\\"):
            return ntpath
        if ":" in path_str[:3] or "\\" in path_str:
            return ntpath
    return ntpath if os.name == "nt" else posixpath


def _resolve_path(path_str: str, path_module, base_directory: Optional[str] = None) -> str:
    if path_module is ntpath and os.name == "nt":
        path = Path(path_str)
        if path.is_absolute():
            return str(path.resolve())
        if base_directory is None:
            return str(Path(path_str).resolve())
        return str((Path(base_directory).resolve() / path_str).resolve())

    if path_module is posixpath and os.name != "nt":
        path = Path(path_str)
        if path.is_absolute():
            return str(path.resolve())
        if base_directory is None:
            return str(Path(path_str).resolve())
        return str((Path(base_directory).resolve() / path_str).resolve())

    if base_directory is None:
        return path_module.abspath(path_str)
    if path_module.isabs(path_str):
        return path_module.normpath(path_str)
    return path_module.normpath(path_module.join(base_directory, path_str))


def _is_path_within_base(path_str: str, base_directory: str) -> bool:
    path_module = _path_module_for(base_directory, path_str)
    try:
        common = path_module.commonpath([base_directory, path_str])
    except ValueError:
        return False
    return path_module.normcase(common) == path_module.normcase(base_directory)


def _ensure_path_within_base(
    path_str: str,
    base_directory: str,
    path_module,
) -> None:
    try:
        common = path_module.commonpath([base_directory, path_str])
    except ValueError as exc:
        raise ValueError(
            f"Path '{path_str}' resolves outside the allowed base directory '{base_directory}'"
        ) from exc

    if path_module.normcase(common) != path_module.normcase(base_directory):
        raise ValueError(
            f"Path '{path_str}' resolves outside the allowed base directory '{base_directory}'"
        )


def _validate_file_component(component: str, component_name: str) -> None:
    if not component:
        raise ValueError(f"{component_name} cannot be empty")
    if component in {".", ".."}:
        raise ValueError(f"{component_name} cannot be '.' or '..'")
    if any(ord(char) < 32 for char in component):
        raise ValueError(
            f"{component_name} cannot contain ASCII control characters"
        )
    if "/" in component or "\\" in component:
        raise ValueError(f"{component_name} cannot contain path separators")
    if re.search(r"[<>:\"|?*]", component):
        raise ValueError(f"{component_name} contains invalid filename characters")
    if component != component.rstrip(" ."):
        raise ValueError(f"{component_name} cannot end with spaces or dots")

    stem = component.split(".", 1)[0].rstrip(" .").upper()
    if stem in _WINDOWS_RESERVED_NAMES:
        raise ValueError(f"{component_name} cannot use reserved device names")


def _sensitive_directories_for(path_module) -> Sequence[str]:
    if path_module is ntpath:
        return _SENSITIVE_DIRS_WINDOWS
    return _SENSITIVE_DIRS_LINUX


def _validate_path_not_sensitive_with_module(path_str: str, path_module) -> str:
    resolved = _resolve_path(path_str, path_module)

    for sensitive_dir in _sensitive_directories_for(path_module):
        sensitive_resolved = _resolve_path(sensitive_dir, path_module)
        if _is_path_within_base(resolved, sensitive_resolved):
            raise ValueError(
                f"Path '{path_str}' targets a sensitive system directory: {sensitive_dir}"
            )

    return resolved


def validate_path_within_base(
    path_str: str,
    base_directory: str,
) -> str:
    """
    Resolve a path and ensure it stays within the base directory.

    :param path_str: The path to validate (absolute or relative)
    :param base_directory: The allowed base directory
    :return: The resolved absolute path as a string
    :raises ValueError: If the path resolves outside the base directory
    """
    base = Path(base_directory).resolve()
    if Path(path_str).is_absolute():
        resolved = Path(path_str).resolve()
    else:
        resolved = (base / path_str).resolve()

    if not (str(resolved).startswith(str(base) + os.sep) or resolved == base):
        raise ValueError(
            f"Path '{path_str}' resolves outside the allowed base directory '{base}'"
        )
    return str(resolved)


def validate_path_not_sensitive(path_str: str) -> str:
    """
    Validate that a path does not point to a sensitive system directory.

    :param path_str: The path to validate
    :return: The resolved absolute path as a string
    :raises ValueError: If the path targets a sensitive directory
    """
    path_module = _path_module_for(path_str)
    return _validate_path_not_sensitive_with_module(path_str, path_module)


def validate_save_path(
    file_dir: str,
    document_dir: Optional[str] = None,
) -> str:
    """
    Validate a directory path for file save operations.

    Ensures the path:
    - Does not contain path traversal sequences
    - Does not target sensitive system directories
    - Is within the document's directory or a user-writable location

    :param file_dir: The target directory for saving
    :param document_dir: The directory of the source document (optional)
    :return: The resolved absolute directory path
    :raises ValueError: If the path is not safe for saving
    """
    path_module = _path_module_for(document_dir or "", file_dir)

    if not file_dir:
        if document_dir:
            resolved_document_dir = _resolve_path(document_dir, path_module)
            _validate_path_not_sensitive_with_module(
                resolved_document_dir, path_module
            )
            return resolved_document_dir
        return os.getcwd()

    if document_dir is None and ".." in Path(file_dir).parts:
        raise ValueError(f"Path '{file_dir}' contains directory traversal sequences")

    resolved = _resolve_path(file_dir, path_module, document_dir)

    if document_dir:
        base_directory = _resolve_path(document_dir, path_module)
        if not _is_path_within_base(resolved, base_directory):
            raise ValueError(
                f"Path '{file_dir}' resolves outside the allowed base directory '{base_directory}'"
            )

    # Block sensitive directories
    _validate_path_not_sensitive_with_module(resolved, path_module)

    return str(resolved)


def validate_save_file_path(
    file_dir: str,
    file_name: str,
    file_ext: str,
    document_dir: str,
) -> str:
    _validate_file_component(file_name, "file_name")
    _validate_file_component(file_ext, "file_ext")
    if not file_ext.startswith(".") or file_ext == ".":
        raise ValueError("file_ext must be a file extension beginning with '.'")

    validated_dir = validate_save_path(file_dir, document_dir)
    path_module = _path_module_for(document_dir, validated_dir)
    base = _resolve_path(document_dir, path_module)
    candidate = _resolve_path(
        path_module.join(validated_dir, file_name + file_ext), path_module
    )
    _ensure_path_within_base(candidate, base, path_module)
    return candidate
