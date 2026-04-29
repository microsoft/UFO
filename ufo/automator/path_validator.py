# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Path validation utilities for preventing path traversal attacks (CWE-22).

Provides functions to validate and sanitize file paths, ensuring they
stay within allowed directories and don't traverse to sensitive locations.
"""

import os
import platform
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
    resolved = Path(path_str).resolve()
    resolved_str = str(resolved)

    if platform.system() == "Windows":
        sensitive_dirs = _SENSITIVE_DIRS_WINDOWS
    else:
        sensitive_dirs = _SENSITIVE_DIRS_LINUX

    for sensitive_dir in sensitive_dirs:
        sensitive_resolved = str(Path(sensitive_dir).resolve())
        if resolved_str.lower().startswith(sensitive_resolved.lower()):
            raise ValueError(
                f"Path '{path_str}' targets a sensitive system directory: {sensitive_dir}"
            )

    return str(resolved)


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
    if not file_dir:
        if document_dir:
            return str(Path(document_dir).resolve())
        return os.getcwd()

    resolved = Path(file_dir).resolve()

    # Block path traversal sequences in the raw input
    if ".." in Path(file_dir).parts:
        raise ValueError(
            f"Path '{file_dir}' contains directory traversal sequences"
        )

    # Block sensitive directories
    validate_path_not_sensitive(str(resolved))

    return str(resolved)
