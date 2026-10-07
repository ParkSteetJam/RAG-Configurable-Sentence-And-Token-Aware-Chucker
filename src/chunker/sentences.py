"""Sentence splitting."""

import re

# Split after . ! ? followed by whitespace, or at a blank line (paragraph break).
_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n\s*\n")


def split_sentences(text):
    """Return a list of non-empty, stripped sentences in original order."""
    parts = _SPLIT_RE.split(text.strip())
    # Collapse inner whitespace/newlines so each sentence is one clean line.
    return [" ".join(p.split()) for p in parts if p and p.strip()]
