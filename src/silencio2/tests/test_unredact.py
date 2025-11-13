# src/silencio2/tests/test_unredact.py

import pytest
from silencio2.unredact import unredact_text
from silencio2.models import Inventory, RedactionItem, Alias

def make_inventory_for_unredact():
    inv = Inventory(items=[])
    item = RedactionItem(
        id=10, 
        code="(1)(A)(c)", 
        desc="email address", 
        surface="user@example.com", 
        aliases=[
            Alias(
                id=1, 
                surface="user_alt@example.com"
            )
        ], 
        scope="global")
    inv.items.append(item)
    return inv

def test_unredact_missing_item_keeps_tag():
    inv = make_inventory_for_unredact()
    text = "[REDACTED(#999|var=c): (1)(A)(c), email address]"
    out = unredact_text(text, inv)
    assert out == text

def test_unredact_canonical_variant():
    inv = make_inventory_for_unredact()
    text = "[REDACTED(#10|var=c): (1)(A)(c), email address]"
    out = unredact_text(text, inv)
    assert out == "user@example.com"

def test_unredact_alias_variant():
    inv = make_inventory_for_unredact()
    text = "[REDACTED(#10|var=a1): (1)(A)(c), email address]"
    out = unredact_text(text, inv)
    assert out == "user_alt@example.com"

def test_unredact_multiple_tags():
    inv = make_inventory_for_unredact()
    text = "First [REDACTED(#10|var=c): (1)(A)(c), email address] then [REDACTED(#10|var=a1): (1)(A)(c), email address]"
    out = unredact_text(text, inv)
    assert out == "First user@example.com then user_alt@example.com"

