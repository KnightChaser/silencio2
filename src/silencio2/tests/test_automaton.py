# src/silencio2/tests/test_automaton.py

from silencio2.automaton import build_automaton, collect_matches, select_leftmost_longest
from typing import List

def test_build_and_collect_matches_simple():
    patterns: List[tuple[int, str, str, str, int | None, str]] = [
        (1, "(1)(A)(c)", "email address", "c", 1, "alice@example.com")
    ]

    A = build_automaton(patterns)
    text = "Contact alice@example.com here."
    matches = collect_matches(A, text)
    assert len(matches) == 1
    m = matches[0]

    assert m.item_id == 1
    assert m.surface == "alice@example.com" # Is the match what I intended?
    assert text[m.start:m.end] == "alice@example.com" # Is the span correct?

def test_select_leftmost_longest_overlapping():
    patterns: List[tuple[int, str, str, str, int | None, str]] = [
        (1, "code1", "desc1", "c", 1, "foo"),
        (1, "code1", "desc1", "c", 2, "foobar"),
    ]

    A = build_automaton(patterns)
    text = "Something foobar in text"
    matches = collect_matches(A, text)
    selected = select_leftmost_longest(matches)

    assert len(selected) == 1
    assert selected[0].surface == "foobar" # expect longest match selected
