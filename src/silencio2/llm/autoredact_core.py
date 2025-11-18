# src/silencio2/llm/autoredact_core.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

from rich import print as rprint

from ..models import Inventory
from ..store import load_inventory, save_inventory
from ..badges import parse_badges
from ..redact import apply_redactions, build_automaton_for_inventory
from .engine import Qwen3ChatEngine, Qwen3Config, ChatMessage

# TODO:
# File types considered "text" for initial autoredact
# Maybe add more pure text types later
DEFAULT_TEXT_EXTS: tuple[str, ...] = (
    ".md",        # Markdown
    ".markdown",  # Markdown
    ".txt"        # Plain text
    ".0",         # Plain text (usually for License files)
    ".asc",       # ASCII armored files
    ".csv",       # Comma-separated values
    ".odt",       # OpenDocument Text
    ".rtf",       # Rich Text Format
)

@dataclass
class AutoredactStats:
    """
    Summary statistics for a full autoredact run.
    """
    files_processed: int
    badges_generated: int
    new_items_created: int
    total_items_after: int

# ---------------------------------------------
# Helper functions for inventory and files
# ---------------------------------------------

def _iter_source_files(src_dir: Path, text_exts: Iterable[str]) -> List[Path]:
    """
    Enumerate source text files under src_dir matching the given extensions

    Args:
        src_dir: Directory to search
        text_exts: Iterable of text file extensions to considered

    Returns:
        Sorted list of Path objects for text files found
    """
    exts = {ext.lower() for ext in text_exts}
    files: List[Path] = []
    for p in src_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return sorted(files)

def _render_inventory_for_prompt(inventory: Inventory, max_items: int = 200) -> str:
    """
    Produce a compact, human-readable inventory snapshopf or the LLM.

    We keep it intentionally light to avoid blowing up context size.

    Args:
        inventory: Inventory object to render
        max_items: Maximum number of items to include in the output

    Returns:
        A string representation of the inventory
    """
    if not inventory.items:
        return "(empty inventory)"

    lines: List[str] = []
    for item in sorted(inventory.items,
                       key=lambda it: (it.code, it.surface))[:max_items]:
        # TODO:
        # For now, we only show canonical surfce to keep noise low.
        # Later, we have to add aliases too.
        lines.append(
            f"- #{item.id} {item.code} :: {item.desc} :: {item.surface}"
        )
    if len(inventory.items) > max_items:
        lines.append(f"... (truncated; {len(inventory.items) - max_items} more items)")

    return "\n".join(lines)

# ---------------------------------------------
# Prompt construction
# ---------------------------------------------

_DEFAULT_ALIAS_AND_FORMAT_GUIDANCE: str = """
You are a redaction badge extractor.

IMPORTANT ABOUT FORMAT:

- The policy text above may describe "lists", "fields", or "tables"
  such as: item, code, desc, aliases, notes.
- Those are ONLY for your internal reasoning.
- For this tool, you MUST IGNORE any instructions about returning lists,
  tables, JSON, or free-form explanations.

For YOUR ACTUAL OUTPUT in this tool, you MUST OBEY THESE RULES EXACTLY:

1) Output format

- Output ONLY badge lines, one per line, using EXACTLY this format:
    [REDACTED: (code), desc] => surface
  Examples:
    [REDACTED: (1)(A)(c), email address] => alice@example.com
    [REDACTED: (3)(B)(a), project codename] => Project Phoenix

- Do NOT output:
    - bullet lists
    - numbered lists
    - Markdown formatting
    - prose explanations
    - JSON
    - extra commentary before or after the badge lines

- If you output anything other than badge lines in the exact format above,
  the tool WILL FAIL.

2) Code format

- code MUST be in the form shown in the legend, e.g.:
    (1)(A)(c), (3)(B)(d), (2)(C), (4)(D)
- Each level MUST be wrapped in parentheses, for example:
    "(3)(A)(b)" is valid.
    "3.A.b", "[3][A][b]", "3(A)(b)", or "3-AB" are INVALID.

3) Surface and deduplication

- The "surface" on the right-hand side MUST be copied EXACTLY from the input text.
  Do NOT normalize, translate, or reformat it.
- If a given surface string appears multiple times in the text with the same (code, desc),
  you MUST output at most ONE badge line for that surface.
- If you are unsure whether something should be redacted, OMIT it instead of guessing.

4) Aliases and inventory

- You are given an inventory snapshot listing already-known items.
- If you see exactly the same surface as an existing item, you may reuse the same (code, desc),
  but you STILL output a badge line in the same format; the caller deduplicates later.
- Do NOT try to output "aliases" yourself; the caller handles alias creation.
""".strip()

def _build_badge_prompt(
    policy_text: str,
    inventory: Inventory,
    document_text: str,
) -> Tuple[str, List[ChatMessage]]:
    """
    Build the full prompt for the LLM for a single document.

    Args:
        policy_text: The redaction policy text to include
        inventory: The current redaction inventory
        document_text: The text of the document to analyze

    Returns:
        A tuple of (system_content, messages) for the chat LLM
    """
    inventory_snippet = _render_inventory_for_prompt(inventory)

    user_content = f"""\
The following is your redaction policy and category legend.
Use it ONLY to decide *what* should be redacted and which (code, desc) to use.
Ignore any instructions there about output formats, lists, or tables; your actual
output format is defined later in this prompt.

---
Redaction policy (reference only)
---

{policy_text}

---
Implementation notes (alias & output format)
---

{_DEFAULT_ALIAS_AND_FORMAT_GUIDANCE}

---
Current inventory snapshot
---

{inventory_snippet}

---
Input text to analyze
---

{document_text}

---
Your task
---

From ONLY the input text above, extract redaction items and output
badge lines in the required format.

Remember:
- ONE badge line per DISTINCT (code, desc, surface)
- NO explanations, NO prose, NO extra text
"""

    system_content = (
        "You are a precise redaction-badge generator. "
        "You must follow the user's formatting constraints exactly. "
        "If constraints say 'only badge lines', you MUST output only that."
    )

    messages = [
        ChatMessage(role="system", content=system_content),
        ChatMessage(role="user", content=user_content),
    ]

    return system_content, messages

# ---------------------------------------------
# Core per-file processing
# ---------------------------------------------

def _generate_badges_for_file(
    engine: Qwen3ChatEngine,
    policy_text: str,
    inventory: Inventory,
    text: str
) -> List[Tuple[str, str, str]]:
    """
    Call the LLM once for this document and return parsed badges.

    Args:
        engine: The Qwen3ChatEngine instance to use
        policy_text: The redaction policy text
        inventory: The current redaction inventory
        text: The document text to analyze

    Returns:
        A list of parsed badges as (code, desc, surface) tuples
        May be empty([]) if no badges were found.
    """
    _, messages = _build_badge_prompt(
        policy_text=policy_text,
        inventory=inventory,
        document_text=text,
    )
    raw = engine.chat(messages=messages)

    # Split into logical lines, feed into existing badge parser
    lines = [line for line in raw.splitlines() if line.strip()]
    if not lines:
        return []

    try:
        badges = list(parse_badges(lines))
    except ValueError as e:
        # Make it crystal clear which output failed
        raise ValueError(
            f"Failed to parse LLM badge output: {e}\n"
            f"--- Raw LLM output start ---\n"
            f"{raw}\n"
            f"--- Raw LLM output end ---"
        ) from e

    return badges

# ---------------------------------------------
# Public API: full autoredact run
# ---------------------------------------------

def run_autoredact(
    policy_text: str,
    src_dir: Path,
    out_dir: Path,
    inventory_file: Path,
    *,
    engine: Qwen3ChatEngine | None = None,
    text_exts: Iterable[str] = DEFAULT_TEXT_EXTS,
) -> AutoredactStats:
    """
    High-level autoredact pipeline.

    1. Loads or initializes Inventory from `inventory_file`.
    2. Enumerates text files under `src_dir` with given extensions.
    3. For each file:
      a. Calls local LLM once to obtain badge lines.
      b. Parses badges and merges them into Inventory.
    4. Saves updated Inventory to `inventory_file`
    5. Applies deterministic redaction to each file using Aho-Corasick and writes
       redacted copies under `out_dir / "redacted"`, preserving relative structure,
       with `.redacted` inserted before the extension.

    This is purely local: all model calls go through vLLM.
    """
    src_dir = src_dir.resolve()
    out_dir = out_dir.resolve()
    out_redact_dir = out_dir / "redacted"

    # Load or initialize inventory
    if inventory_file.exists():
        inv = load_inventory(inventory_file)
    else:
        inv = Inventory(items=[])

    before_items = len(inv.items) # If the inventory is created new, this is 0

    files = _iter_source_files(src_dir, text_exts)
    if not files:
        rprint(f"[yellow]No text files found in '{src_dir}'.[/yellow]")
        return AutoredactStats(
            files_processed=0,
            badges_generated=0,
            new_items_created=0,
            total_items_after=len(inv.items),
        )

    if engine is None:
        engine = Qwen3ChatEngine(config=Qwen3Config())

    total_badges: int = 0

    # 1) Badge geneeration + inventory update
    for path in files:
        rel = path.relative_to(src_dir)
        rprint(f"[blue]Analyzing file:[/blue] {rel}")
        text = path.read_text(encoding="utf-8", errors="ignore")

        badges = _generate_badges_for_file(
            engine=engine,
            policy_text=policy_text,
            inventory=inv,
            text=text,
        )
        total_badges += len(badges)

        for code, desc, surface in badges:
            inv.add_or_merge(code=code, desc=desc, surface=surface)

    # 1b) Save updated inventory
    save_inventory(inv, inventory_file)
    after_items = len(inv.items)

    A = build_automaton_for_inventory(inv)

    # 2) Apply deterministic redaction with the final inventory
    out_redact_dir.mkdir(parents=True, exist_ok=True)

    for path in files:
        rel = path.relative_to(src_dir)
        text = path.read_text(encoding="utf-8", errors="ignore")
        redacted, matches = apply_redactions(
            text=text,
            inventory=inv,
            automaton=A)

        # e.g. foo.md -> foo.redacted.md
        stem = path.stem
        suffix = path.suffix
        out_path = out_redact_dir / rel.with_name(f"{stem}.redacted{suffix}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(redacted, encoding="utf-8")

        rprint(
            f"[green]Redacted[/green] {rel}  "
            f"(matches: {len(matches)}) -> {out_path.relative_to(out_dir)}"
        )

    stats = AutoredactStats(
        files_processed=len(files),
        badges_generated=total_badges,
        new_items_created=max(after_items - before_items, 0),
        total_items_after=after_items,
    )

    rprint(
        "[bold]Autoredact complete.[/bold] "
        f"files={stats.files_processed}, "
        f"badges={stats.badges_generated}, "
        f"new_items={stats.new_items_created}, "
        f"total_items={stats.total_items_after}"
    )

    return stats
