# src/silencio2/unredact.py
from __future__ import annotations

import re
from .models import Inventory

TAG_WITH_ID = re.compile(
    r"\[REDACTED(?:\(#([0-9]+)\))?: \(([0-9]+)\)\(([A-Z])\)(?:\(([a-z])\))?, (.*?)\]"
)

def unredact_text(text: str, inventory: Inventory) -> str:
    """
    Replace REDACTED tags with the canonical surface from inventory.
    If an item ID is missing, the original tag is kept.
    """
    def repl(m: re.Match[str]) -> str:
        item_id = int(m.group(1))
        item = inventory.find(item_id)
        return item.surface if item else m.group(0) # m.group(0) for entire match

    return TAG_WITH_ID.sub(repl, text)
