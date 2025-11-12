# src/silencio2/unredact.py
from __future__ import annotations

import re
from .models import Inventory

# e.g., [REDACTED(#1|var=c): (3)(A)(b), Description]
TAG_WITH_VARIANT = re.compile(
    r"\[REDACTED\(#(?P<id>\d+)\|var=(?P<var>c|a\d+)\):\s*[^,]+,\s*[^]]+\]"
)

def unredact_text(text: str, inventory: Inventory) -> str:
    """
    Replace REDACTED tags with the canonical surface from inventory.
    If an item ID is missing, the original tag is kept.

    Args:
        text (str): The input text containing REDACTED tags.
        inventory (Inventory): The inventory to look up items.

    Returns:
        str: The text with REDACTED tags replaced by their canonical surfaces.
    """
    def repl(m: re.Match[str]) -> str:
        item_id = int(m.group("id"))
        var = m.group("var")
        item = inventory.find(item_id)
        if not item:
            return m.group(0)  # keep the whole tag as-is
        if var == "c":
            # canonical
            return item.surface

        # alias aN
        try:
            alias_id = int(var[1:])
        except ValueError:
            return item.surface

        alias_surface = inventory.get_alias_surface(item_id, alias_id)
        return alias_surface if alias_surface is not None else item.surface

    return TAG_WITH_VARIANT.sub(repl, text)
