# src/silencio2/redact.py
from __future__ import annotations

from typing import Tuple, List
from .models import Inventory
from .automaton import build_automaton, collect_matches, select_leftmost_longest, Match
from .mdseg import segment, mask_existing_tags


def apply_redactions(text: str, inventory: Inventory) -> Tuple[str, List[Match]]:
    """
    Apply redactions to the given markdown text based on the inventory.

    Args:
        text (str): The input markdown text.
        inventory (Inventory): The inventory containing items to redact.

    Returns:
        Tuple[str, List[Match]]: A tuple containing the redacted text and a list
    """
    # Build Aho-Corasick automaton
    patterns = [(item.id, item.code, item.desc, item.surface) for item in inventory.items]
    if not patterns:
        return text, []
    A = build_automaton(patterns)

    # Segment markdown; skip code fences
    segments = segment(text)
    rebuilt: List[str] = []
    all_matches: List[Match] = []

    for chunk, redactable in segments:
        if not redactable:
            rebuilt.append(chunk)
            continue
        
        safe = mask_existing_tags(chunk)
        matches = collect_matches(A, safe)
        selected = select_leftmost_longest(matches)
        if not selected:
            # No matches; append as-is
            rebuilt.append(chunk)
            continue

        # Right-to-left replacement
        out: List[str] = []
        cursor = len(chunk)
        for match in reversed(selected):
            out.append(chunk[match.end:cursor])
            out.append(f"[REDACTED(#{match.item_id}): {match.code}, {match.desc}]")
            out.append(chunk[match.start:match.start])  # noop slice
            cursor = match.start
        out.append(chunk[:cursor])
        rebuilt.append("".join(reversed(out)))
        all_matches.extend(selected)

    return "".join(rebuilt), all_matches
