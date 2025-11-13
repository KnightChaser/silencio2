# src/silencio2/mdseg.py
from __future__ import annotations

from typing import List, Tuple

from .patterns import MD_CODE_FENCE_RE as FENCE, REDACTED_TAG_BLOCK_RE as TAG_BLOCK

def segment(text: str) -> List[Tuple[str, bool]]:
    """
    Returns segments as (chunk, redactable) tuples.
    `redactable` is True if the chunk is normal text, False if it's inside a code fence.

    Args:
        text (str): The input markdown text.

    Returns:
        List[Tuple[str, bool]]: A list of tuples containing text segments and their redact
    """
    out: List[Tuple[str, bool]] = []
    pos = 0
    for match in FENCE.finditer(text):
        if match.start() > pos:
            out.append((text[pos:match.start()], True))
        out.append((match.group(0), False))
        pos = match.end()

    if pos < len(text):
        out.append((text[pos:], True))

    return out

def mask_existing_tags(text: str) -> str:
    """
    To prevent dobule-redaction, mask existing REDACTED tags 
    in the text with black squares(\u25a0),
    so Aho-Corasick won't match them.

    Args:
        text (str): The input text.

    Returns:
        str: The text with existing REDACTED tags masked.
    """
    def repl(m):
        return "\u25A0" * (m.end() - m.start())

    return TAG_BLOCK.sub(repl, text)
