# src/silencio2/tests/test_mdseg.py

import pytest
from silencio2.mdseg import segment, mask_existing_tags

def test_segment_no_code_fence():
    text = "Regular text without code."
    segs = segment(text)

    assert len(segs) == 1
    chunk, redactable = segs[0]

    assert chunk == text
    assert redactable is True

def test_segment_with_code_fence():
    text = "Intro\n```python\ncode block\n```\nAfter"
    segs = segment(text)

    # expect 3 segments: before code, code fence, after code
    assert len(segs) == 3
    assert segs[0][1] is True   # "Intro\n"
    assert segs[1][1] is False  # "```python\ncode block\n```"
    assert segs[2][1] is True   # "\nAfter"

def test_mask_existing_tags_replaces_tags():
    text = "Here is [REDACTED(#1|var=c): (1)(A)(c), email address] in text."
    masked = mask_existing_tags(text)

    assert "[REDACTED" not in masked

    # The length of masked should match original
    assert len(masked) == len(text)

