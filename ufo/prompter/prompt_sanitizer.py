# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Prompt input sanitization utilities.

Mitigates prompt injection attacks (CWE-77) by sanitizing user-controlled
inputs before they are interpolated into LLM prompt templates. This is a
defense-in-depth measure: it does not replace proper authorization checks
or confirmation gates, but significantly raises the difficulty of injecting
rogue instructions through template placeholders.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Maximum character length for a single user-supplied field.
# Inputs exceeding this are truncated with a warning.
_MAX_INPUT_LENGTH = 10_000

# Patterns that attempt to impersonate system-level or role-level prompt
# directives.  Matched case-insensitively.
# Catches both [SYSTEM]: (colon after bracket) and [SYSTEM: ...] (colon inside).
_INJECTION_ROLE_PATTERN = re.compile(
    r"(?i)\[\s*(?:SYSTEM|ADMIN|ASSISTANT|USER|DEVELOPER)\s*(?:UPDATE|OVERRIDE|INSTRUCTION|MESSAGE|PROMPT|NOTE)?\s*(?:\]\s*:|\s*:\s*)",
)

# Matches lines that look like markdown/YAML role headers injected inside
# user content, e.g.  "## SYSTEM:", "SYSTEM UPDATE:", "role: system", etc.
# Allows optional modifier words (UPDATE, OVERRIDE, etc.) between the role
# keyword and the colon.
_INJECTION_ROLE_HEADER_PATTERN = re.compile(
    r"(?im)^(?:#{1,4}\s+)?(?:role|system|assistant|user|developer)\s*(?:(?:update|override|instruction|message|prompt|note)\s*)?:\s*",
)

# Detects phrases that try to trick the model into skipping confirmation.
_CONFIRMATION_BYPASS_PATTERN = re.compile(
    r"(?i)(?:user\s+has\s+(?:already\s+)?confirmed|proceed\s+(?:immediately|without\s+(?:user\s+)?confirm)|skip\s+confirm|bypass\s+(?:safety|security|confirm))",
)

# Detects attempts to override or cancel previous instructions.
_INSTRUCTION_OVERRIDE_PATTERN = re.compile(
    r"(?i)(?:ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions|new\s+(?:priority|instructions?|directive)|previous\s+instructions?\s+cancelled|disregard\s+(?:all|previous|prior))",
)

# Valid field name pattern: alphanumeric characters and underscores only.
_VALID_FIELD_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# All filter patterns with their replacement text, used for logging.
_FILTER_PATTERNS = [
    (_INJECTION_ROLE_PATTERN, "[filtered-role-marker]:"),
    (_INJECTION_ROLE_HEADER_PATTERN, "[filtered-header] "),
    (_CONFIRMATION_BYPASS_PATTERN, "[filtered-bypass-attempt]"),
    (_INSTRUCTION_OVERRIDE_PATTERN, "[filtered-override-attempt]"),
]


def sanitize_user_input(value: str, field_name: str = "input") -> str:
    """Sanitize a single user-controlled string before prompt interpolation.

    The function applies several layers of defence:

    1. **Length limiting** – truncates inputs that exceed ``_MAX_INPUT_LENGTH``
       to prevent denial-of-service via context overflow.
    2. **Injection marker neutralization** – replaces characters/sequences that
       could be interpreted as prompt role boundaries (``[SYSTEM]:``, etc.) with
       visually similar but semantically inert alternatives.
    3. **Delimiter wrapping** – encloses the value in clear ``<user_input>``
       XML-style tags so the LLM can distinguish data from instructions.

    Parameters
    ----------
    value : str
        The raw, untrusted input string.
    field_name : str
        A label for the field (used in log messages and the delimiter tag).
        Must match ``[a-zA-Z_][a-zA-Z0-9_]*``.

    Returns
    -------
    str
        The sanitized string, safe for interpolation into a prompt template.
    """
    if not isinstance(value, str):
        logger.warning(
            "sanitize_user_input called with non-string value (type=%s) for field '%s'",
            type(value).__name__,
            field_name,
        )
        return value

    if not value:
        return value

    # Validate field_name to prevent attribute injection in the XML tag.
    if not _VALID_FIELD_NAME.match(field_name):
        logger.warning(
            "Invalid field_name '%s' replaced with 'input'",
            field_name,
        )
        field_name = "input"

    original_length = len(value)

    # 1. Length-limit
    if len(value) > _MAX_INPUT_LENGTH:
        logger.warning(
            "Prompt input '%s' truncated from %d to %d characters",
            field_name,
            original_length,
            _MAX_INPUT_LENGTH,
        )
        value = value[:_MAX_INPUT_LENGTH] + "... [truncated]"

    # 2. Apply all filter patterns and log when they trigger.
    for pattern, replacement in _FILTER_PATTERNS:
        if pattern.search(value):
            logger.warning(
                "Prompt input '%s' matched filter pattern %s",
                field_name,
                pattern.pattern[:60],
            )
            value = pattern.sub(replacement, value)

    # 3. Wrap in delimiters so the LLM can clearly identify data boundaries
    value = f"<user_input name=\"{field_name}\">{value}</user_input>"

    return value
