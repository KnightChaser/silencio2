# src/silencio2/badges.py
from __future__ import annotations

import re
from typing import Iterable, Iterator, Tuple

from .patterns import BADGE_ARROW_RE, BADGE_PIPE_RE, CODE_RE

_CODE_RE = re.compile(CODE_RE)

def parse_badge_lines(line: str) -> Tuple[str, str, str] | None:
    """
    Parse a single badge line in either ARROW(=>) or PIPE(|) format.

    Supported format:

        [REDACTED: (3)(A)(b), API key] => AKIA...
        (3)(A)(b) | API key | AKIA...

    Args:
        line (str): The badge line to parse.

    Returns:
        Tuple[str, str, str] | None: 
            A tuple of (code, desc, surface) if a badge is found,
            else None for empty/comment lines.

    Raises:
        ValueError: If the line is non-empty/non-comment but does not match
                    any supported badge format, or the code does not match
                    the expected classification pattern.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # Attempt to match ARROW format
    m = BADGE_ARROW_RE.match(line)
    if m:
        code, desc, surface = m.group(1), m.group(2).strip(), m.group(3)
    else:
        # Attempt to match PIPE format then
        m = BADGE_PIPE_RE.match(line)
        if m:
            code, desc, surface = m.group(1), m.group(2).strip(), m.group(3)
        else:
            raise ValueError(f"Invalid badge line format: {line}")

    # Double-check that the code matches the expected classification pattern
    if not _CODE_RE.match(code):
            raise ValueError(f"Invalid badge code format: {code}")

    return code, desc, surface

def parse_badges(lines: Iterable[str]) -> Iterator[Tuple[str, str, str]]:
    """
    Parse multiple badge lines from an iterable of strings.

    It skips(ignores) the text if:
        - empty lines
        - lines starting with '#' (considered annotations)

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
