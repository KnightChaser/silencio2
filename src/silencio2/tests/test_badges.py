# src/silencio2/tests/test_badges.py

import pytest
from silencio2.badges import parse_badge_lines, parse_badges

def test_parse_badge_lines_arrow_format():
    line = "[REDACTED: (3)(A)(b), API key] => ABC123"
    result = parse_badge_lines(line)
    assert result is not None
    code, desc, surface = result

    assert code == "(3)(A)(b)"
    assert desc == "API key"
    assert surface == "ABC123"

def test_parse_badge_lines_pipe_format():
    line = "(3)(A)(b) | API key | ABC123"
    result = parse_badge_lines(line)
    assert result is not None
    code, desc, surface = result

    assert code == "(3)(A)(b)"
    assert desc == "API key"
    assert surface == "ABC123"

def test_parse_badges_skips_comments_and_blank():
    lines = [
        "# comment here",
        "",
        "(1)(A)(c) | email address | bob@example.com"
    ]
    results = list(parse_badges(lines))
    assert len(results) == 1
    code, desc, surface = results[0]

    assert code == "(1)(A)(c)"
    assert desc == "email address"
    assert surface == "bob@example.com"

def test_parse_badge_lines_invalid_format_raises():
    with pytest.raises(ValueError):
        parse_badge_lines("invalid line format")

