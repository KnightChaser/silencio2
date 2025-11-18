# src/silencio2/automaton.py
from __future__ import annotations

from typing import List, Tuple
from dataclasses import dataclass
import ahocorasick

@dataclass
class Match:
    start: int
    end: int        # exclusive
    item_id: int
    code: str
    desc: str
    surface: str
    variant: str    # "c" for canonical, "a" for alias
    alias_id: int | None

def build_automaton(patterns: List[Tuple[int, str, str, str, int | None, str]]) -> ahocorasick.Automaton:
    """
    Build an Aho-Corasick automaton from the given patterns.

    Args:
        patterns: A list of tuples, each containing:
            - item_id (int): The ID of the item.
            - code (str): The code of the item.
            - desc (str): The description of the item.
            - variant (str): "c" for canonical, "a" for alias.
            - alias_id (int | None): The ID of the alias, or None for canonical
            - surface (str): The surface string to match.

    Returns:
        ahocorasick.Automaton: The constructed Aho-Corasick automaton.
    """
    A = ahocorasick.Automaton()
    for item_id, code, desc, variant, alias_id, surface in patterns:
        if not surface:
            continue
        A.add_word(surface, (item_id, code, desc, variant, alias_id, surface))
    A.make_automaton()
    return A

def collect_matches(A: ahocorasick.Automaton, text: str) -> List[Match]:
    """
    Collect all matches of the patterns in the given text using the Aho-Corasick automaton.

    Args:
        A: The Aho-Corasick automaton.
        text: The text to search for patterns.

    Returns:
        List[Match]: A list of Match objects representing the found patterns.
    """
    out: List[Match] = []
    for end_index, payload in A.iter(text):
        item_id, code, desc, variant, alias_id, surface = payload
        start_idx = end_index - len(surface) + 1  # inclusive
        out.append(
            Match(
                start=start_idx,
                end=end_index + 1,
                item_id=item_id,
                code=code,
                desc=desc,
                surface=surface,
                variant=variant,
                alias_id=alias_id,
            )
        )
    return out

def select_leftmost_longest(matches: List[Match]) -> List[Match]:
    """
    Select non-overlapping matches using leftmost-longest strategy.

    Args:
        matches: A list of Match objects.

    Returns:
        List[Match]: A list of selected non-overlapping Match objects.
    """

    # NOTE:
    # Sorts by the start position (ascending). Earlier matches come first.
    # Then, sorts by match length (descending). Longer matches come first if they start at the same position.
    matches = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))

    selected: List[Match] = []
    last_end = -1
    for match in matches:
        if match.start >= last_end:
            selected.append(match)
            last_end = match.end

    return selected
