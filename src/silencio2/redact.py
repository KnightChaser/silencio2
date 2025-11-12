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
    # Build Aho-Corasick automaton with alias
    patterns = []
    for item in inventory.items:
        patterns.append((item.id, item.code, item.desc, "c", None, item.surface)) # canonical surface
        for alias in item.aliases:
            if alias:
                patterns.append((item.id, item.code, item.desc, "a", alias.id, alias.surface)) # alias surface
    if not patterns:
        return text, []
    A = build_automaton(patterns)

    # Segment markdown; skip code fences
    segments = segment(text)
    rebuilt: List[str] = []
    all_matches: List[Match] = []

    for chunk, redactable in segments:
        if not redactable:
            # Exclude unredactable segments (such as code fences (as a default))
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

            # NOTE:
            # variant marker: "c" for canonical, "a" for alias
            # e.g., [REDACTED(#1|var=a2): (3)(A)(b), Description]
            v = "c" if match.variant == 'c' else f"a{match.alias_id}"

            out.append(f"[REDACTED(#{match.item_id}|var={v}): {match.code}, {match.desc}]")
            out.append(chunk[match.start:match.start])
            cursor = match.start
        out.append(chunk[:cursor])
        rebuilt.append("".join(reversed(out)))
        all_matches.extend(selected)

    return "".join(rebuilt), all_matches
