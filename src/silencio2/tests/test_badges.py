# src/silencio2/tests/test_badges.py

import pytest
from silencio2.badges import parse_badge_lines, parse_badges, validate_badge_lines

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

def test_validate_badge_lines_all_valid():
    lines = [
        "# comment here",                               # should be skipped
        "",                                             # should be skipped
        "(1)(A)(c) | email address | bob@example.com",  # valid
        "[REDACTED: (3)(B)(a), api key] => AKIA123"     # valid
    ]
    from silencio2.badges import validate_badge_lines
    n_valid, n_skipped = validate_badge_lines(lines)
    assert n_valid == 2
    assert n_skipped == 2

def test_validate_badge_lines_invalid_format_fails():
    lines = [
        "(1)(A)(c) | email address | bob@example.com",
        "bad line here",
        "(2)(C) | desc | value"
    ]
    from silencio2.badges import validate_badge_lines
    with pytest.raises(ValueError) as excinfo:
        validate_badge_lines(lines)
    # error message should include line number 2
    assert "line 2" in str(excinfo.value)

def test_validate_badge_lines_invalid_code_fails():
    lines = [
        "(9)(Z)(x) | weird | foo",
    ]
    from silencio2.badges import validate_badge_lines
    with pytest.raises(ValueError) as excinfo:
        validate_badge_lines(lines)
    assert "Invalid badge line" in str(excinfo.value)
