# src/silencio2/tests/test_unredact.py

import pytest
from silencio2.unredact import unredact_text
from silencio2.models import Inventory

def make_inventory_for_unredact():
    inv = Inventory()
    item = inv.add_or_merge(
        code="(1)(A)(c)",
        desc="email address", 
        surface="user@example.com")
    inv.add_alias(item.id, "user_alt@example.com")
    return inv

def test_unredact_missing_item_keeps_tag():
    inv = make_inventory_for_unredact()
    text = "[REDACTED(#999|var=c): (1)(A)(c), email address]"
    out = unredact_text(text, inv)
    assert out == text

def test_unredact_canonical_variant():
    inv = make_inventory_for_unredact()
    text = "[REDACTED(#1|var=c): (1)(A)(c), email address]"
    out = unredact_text(text, inv)
    assert out == "user@example.com"

def test_unredact_alias_variant():
    inv = make_inventory_for_unredact()
    text = "[REDACTED(#1|var=a1): (1)(A)(c), email address]"
    out = unredact_text(text, inv)
    assert out == "user_alt@example.com"

def test_unredact_multiple_tags():
    inv = make_inventory_for_unredact()
    text = "First [REDACTED(#1|var=c): (1)(A)(c), email address] then [REDACTED(#1|var=a1): (1)(A)(c), email address]"
    out = unredact_text(text, inv)
    assert out == "First user@example.com then user_alt@example.com"

