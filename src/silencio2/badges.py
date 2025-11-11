# src/silencio2/badges.py
from __future__ import annotations

import re
from typing import Iterable, Iterator, Tuple

# e.g., [REDACTED: (3)(A)(b), api key] => AKIA...
ARROW = re.compile(
    r"""^\s*\[REDACTED:\s*(\([1-4]\)\([A-EX]\)(?:\([a-ex]\))?)\s*,\s*([^\]]+?)\]\s*=>\s*(.+?)\s*$"""
)

# e.g., (3)(A)(b) | api key | AKIA...
PIPE = re.compile(
    r"""^\s*(\([1-4]\)\([A-EX]\)(?:\([a-ex]\))?)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*$"""
)

def parse_badge_lines(line: str) -> Tuple[str, str, str] | None:
    """
    Parse a single badge line in either ARROW or PIPE format.
    It assuems `line` has at least one valid badge.

    Args:
        line (str): The badge line to parse.

    Returns:
        Tuple[str, str, str] | None: A tuple of (code, desc, surface) if a badge is found, else None.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # Attempt to match ARROW format
    m = ARROW.match(line)
    if m:
        code, desc, surface = m.group(1), m.group(2).strip(), m.group(3)
        return code, desc, surface

    # Attempt to match PIPE format then
    m = PIPE.match(line)
    if m:
        code, desc, surface = m.group(1), m.group(2).strip(), m.group(3)
        return code, desc, surface

    raise ValueError(f"Invalid badge line format: {line}")


def parse_badges(lines: Iterable[str]) -> Iterator[Tuple[str, str, str]]:
    """
    Parse multiple badge lines from an iterable of strings.

    Args:
        lines (Iterable[str]): An iterable of badge lines.

    Returns:
        Iterator[Tuple[str, str, str]]: An iterator of tuples (code, desc, surface).
    """
    for index, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            result = parse_badge_lines(line)
            if result:
                yield result
        except ValueError as e:
            raise ValueError(f"Error parsing line {index}: {e}") from e
