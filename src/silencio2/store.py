# src/silencio2/store.py
from __future__ import annotations

import json
from pathlib import Path
from .models import Inventory

def load_inventory(path: Path) -> Inventory:
    """
    Load the inventory from a JSON file.

    Args:
        path (Path): The path to the JSON file.

    Returns:
        Inventory: The loaded inventory.
    """
    if not path.exists():
        return Inventory()

    data = json.loads(path.read_text(encoding="utf-8"))

    return Inventory.model_validate(data)

def save_inventory(inventory: Inventory, path: Path) -> None:
    """
    Save the inventory to a JSON file.

    Args:
        inventory (Inventory): The inventory to save.
        path (Path): The path to the JSON file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(inventory.model_dump_json(indent=2), encoding="utf-8")
