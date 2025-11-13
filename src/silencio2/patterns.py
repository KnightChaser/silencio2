# src/silencio2/patterns.py
"""
Central definitions for regular expressions used across silencio2.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Redaction code pattern (e.g. "(3)(A)(b)")
# ---------------------------------------------------------------------------

# Matches classification code tuples of the form:
#   (group)(subgroup)(optional fine-grain)
# Examples:
#   (1)(A)(c)
#   (3)(E)
#   (4)(X)(a)
#
# Capture groups are not used; this is mainly used by Pydantic's pattern=
CODE_RE = r"^\([1-4]\)\([A-EX]\)(?:\([a-ex]\))?$"

# ---------------------------------------------------------------------------
# Badge definitions (import_badges)
# ---------------------------------------------------------------------------

# ARROW badge lines:
#   [REDACTED: (3)(A)(b), api key] => AKIA....
#
# Groups:
#   1: code, e.g. "(3)(A)(b)"
#   2: description, e.g. "api key"
#   3: surface text, e.g. "AKIA..."
BADGE_ARROW_RE = re.compile(
    r"""
    ^\s*                          # optional leading whitespace
    \[REDACTED:                   # literal "[REDACTED:"
        \s*
        (\([1-4]\)\([A-EX]\)(?:\([a-ex]\))?)    # (1) code
        \s*,\s*
        ([^\]]+?)                 # (2) human description (up to ']')
    \]
    \s*=>\s*                      # "=>"
    (.+?)                         # (3) surface text (to end of line)
    \s*$
    """,
    re.VERBOSE,
)


# PIPE badge lines:
#   (3)(A)(b) | api key | AKIA....
#
# Groups:
#   1: code, e.g. "(3)(A)(b)"
#   2: description, e.g. "api key"
#   3: surface text, e.g. "AKIA..."
BADGE_PIPE_RE = re.compile(
    r"""
    ^\s*
    (\([1-4]\)\([A-EX]\)(?:\([a-ex]\))?)   # (1) code
    \s*\|\s*
    ([^|]+?)                               # (2) description
    \s*\|\s*
    (.+?)                                  # (3) surface text
    \s*$
    """,
    re.VERBOSE,
)

# ---------------------------------------------------------------------------
# Markdown segmentation: code fences and redacted tags
# ---------------------------------------------------------------------------

# Match triple backtick code fences, including their contents:
#
#   ```lang
#   code...
#   ```
#
# Groups:
#   1: opening fence line (```... )
#   2: inner content (lazy, multiline)
#   3: closing fence line (``` )
MD_CODE_FENCE_RE = re.compile(
    r"(^```.*?$)(.*?)(^```$)",
    re.MULTILINE | re.DOTALL,
)

# Match our own redaction tags that include ID + variant:
#
#   [REDACTED(#123|var=c): (1)(A)(b), api key]
#   [REDACTED(#12|var=a3): (3)(E), some desc]
#
# This is used to *mask existing tags* so Aho-Corasick does not re-match them.
#
# We don't capture groups here; we just need to identify the span.
REDACTED_TAG_BLOCK_RE = re.compile(
    r"""
    \[REDACTED
        \(
            \#\d+                     # "#<item_id>"
            \|var=(?:c|a\d+)          # "|var=c" or "|var=aN"
        \)
        :
        \s*
        \([^)]+\)                     # code "(1)(A)(b)" – anything until ')'
        ,\s*
        [^\]]+                        # description up to ']'
    \]
    """,
    re.VERBOSE,
)

# ---------------------------------------------------------------------------
# Unredaction: tags with explicit groups
# ---------------------------------------------------------------------------

# Same tag format as above, but with named capturing groups for:
#   - id: numeric item ID
#   - var: "c" or "aN" (alias indicator)
#
# Example:
#   [REDACTED(#1|var=c): (3)(A)(b), Description]
#   [REDACTED(#2|var=a5): (1)(B), employee ID]
REDACTED_TAG_WITH_VARIANT_RE = re.compile(
    r"""
    \[REDACTED
        \(
            \#(?P<id>\d+)             # item ID
            \|var=(?P<var>c|a\d+)     # variant marker
        \)
        :
        \s*
        [^,]+                         # code part until first comma
        ,\s*
        [^\]]+                        # description part until closing bracket
    \]
    """,
    re.VERBOSE,
)

