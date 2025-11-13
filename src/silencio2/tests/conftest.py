# src/silencio2/tests/conftest.py
import pytest
from silencio2.models import Inventory

@pytest.fixture
def empty_inventory() -> Inventory:
    """
    Fixture that provides an empty Inventory instance.

    Returns:
        Inventory: An Inventory object with no items.
    """
    return Inventory(items=[])

@pytest.fixture
def sample_inventory() -> Inventory:
    """
    Fixture that provides a sample Inventory instance with predefined RedactionItems.

    Returns:
        Inventory: An Inventory object populated with sample RedactionItems.
    """
    inventory = Inventory(items=[])
    item = inventory.add_or_merge(
        code="(1)(A)(c)",
        desc="email address",
        surface="kal@knight.club"
    )
    alias_id = inventory.add_alias(
        item_id=item.id,
        alias_surface="kal@day.club"
    )

    # Assert alias_id is a non-negative intenger
    assert isinstance(alias_id, int) and alias_id >= 0

    return inventory
