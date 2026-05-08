"""
Unit tests for backend/core/sanitize.py — sanitize_text function.
"""
import pytest

from core.sanitize import sanitize_text


class TestSanitizeText:
    """Tests for the sanitize_text utility."""

    def test_strips_script_tags(self):
        """Script tags and their content container should be removed."""
        result = sanitize_text("<script>alert('xss')</script>Hello")
        assert result == "Hello"

    def test_strips_html_tags(self):
        """Generic HTML tags like <b>, <i>, <div> should be stripped."""
        assert sanitize_text("<b>Bold</b>") == "Bold"
        assert sanitize_text("<div>Content</div>") == "Content"
        assert sanitize_text("<p>Paragraph</p>") == "Paragraph"

    def test_strips_img_tag(self):
        """Image tags (common XSS vector) should be stripped."""
        result = sanitize_text('<img src="x" onerror="evil()">')
        assert result == ""

    def test_strips_nested_tags(self):
        """Nested HTML tags should all be removed."""
        result = sanitize_text("<div><b>Hello</b></div>")
        assert result == "Hello"

    def test_passes_clean_text_unchanged(self):
        """Plain text with no HTML should be returned as-is."""
        text = "Manzana roja fresca"
        assert sanitize_text(text) == text

    def test_handles_none(self):
        """None input should be returned as None without error."""
        assert sanitize_text(None) is None

    def test_handles_empty_string(self):
        """Empty string should be returned as empty string."""
        assert sanitize_text("") == ""

    def test_handles_text_with_angle_brackets_in_content(self):
        """
        Text with < > that spans like a tag pattern will have the span removed.

        Our regex treats '<content>' patterns aggressively for security.
        '2 < 3 and 5 > 4' contains '< 3 and 5 >' which looks like a tag —
        it is stripped. This is the intentional conservative behavior.
        If users need comparison operators in text, they should use &lt;/&gt;.
        """
        result = sanitize_text("2 < 3 and 5 > 4")
        # '< 3 and 5 >' is treated as a tag-like pattern and stripped
        assert result == "2  4"

    def test_strips_uppercase_tags(self):
        """HTML tags with uppercase should also be stripped (IGNORECASE flag)."""
        result = sanitize_text("<SCRIPT>evil()</SCRIPT>safe")
        assert result == "safe"

    def test_strips_self_closing_tags(self):
        """Self-closing tags like <br/> should be stripped."""
        result = sanitize_text("line1<br/>line2")
        assert result == "line1line2"
