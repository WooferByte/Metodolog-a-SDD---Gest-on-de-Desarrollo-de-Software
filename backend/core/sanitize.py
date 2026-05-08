"""
XSS / HTML sanitization utility for Food Store API.

PURPOSE
-------
This module provides a single helper function to strip HTML and script tags
from free-text user input (e.g., nombres, descripciones, observaciones).
It is used inside Pydantic v2 field_validators on every request schema that
accepts free-text to prevent stored-XSS attacks.

SQL INJECTION NOTE
------------------
SQL injection is NOT handled here. SQLModel (SQLAlchemy under the hood)
uses parametrized queries for all database interactions, which prevents
SQL injection at the ORM level. No manual SQL escaping is needed anywhere
in the application.
"""
import re

# Pass 1: Remove dangerous tag blocks entirely (script, style, iframe, etc.)
# including all content between the opening and closing tag.
_DANGEROUS_BLOCK_PATTERN = re.compile(
    r"<(script|style|iframe|object|embed|link|meta)[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)

# Pass 2: Remove any remaining HTML-like tags (open, close, or self-closing).
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>", re.IGNORECASE)


def sanitize_text(value: str | None) -> str | None:
    """
    Strip all HTML/script tags and dangerous block content from a string.

    Two-pass approach:
    1. Remove dangerous element blocks (script, style, etc.) *with* their content.
    2. Remove any remaining open/close tags.

    Usage in Pydantic v2 schemas::

        from core.sanitize import sanitize_text
        from pydantic import field_validator

        class MySchema(BaseModel):
            nombre: str

            @field_validator("nombre", mode="before")
            @classmethod
            def sanitize_nombre(cls, v):
                return sanitize_text(v)

    Args:
        value: Raw string from user input, or None / empty.

    Returns:
        The sanitized string with all HTML tags and dangerous content removed,
        or the original value if it is None or empty.
    """
    if not value:
        return value
    # Pass 1: strip dangerous blocks including their content
    result = _DANGEROUS_BLOCK_PATTERN.sub("", value)
    # Pass 2: strip any remaining tags
    result = _HTML_TAG_PATTERN.sub("", result)
    return result
