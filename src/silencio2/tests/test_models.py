# src/silencio2/tests/test_models.py

import pytest
from silencio2.models import Inventory, RedactionItem, Alias

def test_add_or_merge_creates_new_item(empty_inventory):
    inv = empty_inventory
    item = inv.add_or_merge(code="(1)(A)(c)", desc="email address", surface="alice@example.com")

    assert item.id == 1
    assert item.code == "(1)(A)(c)"
    assert item.desc == "email address"
    assert item.surface == "alice@example.com"
    assert item.aliases == []

    # adding same surface again yields same object
    item2 = inv.add_or_merge(code="(1)(A)(c)", desc="email address", surface="alice@example.com")
    assert item2 is item

def test_add_alias_creates_alias_id(sample_inventory):
    inv = sample_inventory
    item = inv.items[0]
    alias_surface = "alice_alt@example.com"
    alias_id = inv.add_alias(item.id, alias_surface)

    assert alias_id > 0

    # alias should appear in item.aliases
    assert any(a.surface == alias_surface and a.id == alias_id for a in item.aliases)

def test_add_alias_duplicate_returns_zero_or_no_change(sample_inventory):
    inv = sample_inventory
    item = inv.items[0]
    alias_surface = item.aliases[0].surface
    alias_id = inv.add_alias(item.id, alias_surface)

    assert alias_id == 0  # expect duplicate alias returns zero

    # unchanged alias list length
    assert len(item.aliases) == 1

def test_get_alias_surface_valid(sample_inventory):
    inv = sample_inventory
    item = inv.items[0]
    alias = item.aliases[0]
    surface = inv.get_alias_surface(item.id, alias.id)

    assert surface == alias.surface

def test_get_alias_surface_invalid(sample_inventory):
    inv = sample_inventory
    # nonexistent alias id

    surface = inv.get_alias_surface(item_id=inv.items[0].id, alias_id=9999)

    assert surface is None
