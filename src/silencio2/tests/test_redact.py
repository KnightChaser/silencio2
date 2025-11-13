# src/silencio2/tests/test_redact.py

import pytest
from silencio2.redact import apply_redactions
from silencio2.models import Inventory

def test_apply_redactions_no_items(empty_inventory):
    inv = empty_inventory
    text = "No sensitive items here."
    red, matches = apply_redactions(text, inv)
    
    assert red == text
    assert matches == []

def test_apply_redactions_canonical_and_alias(sample_inventory):
    inv = sample_inventory
    item = inv.items[0]
    alias = item.aliases[0]
    text = f"Contact {item.surface} or {alias.surface} for details."
    red, matches = apply_redactions(text, inv)

    # should find two matches
    assert len(matches) == 2

    # ensure tags are present
    assert f"[REDACTED(#{item.id}|var=c): {item.code}, {item.desc}]" in red
    assert f"[REDACTED(#{item.id}|var=a{alias.id}): {item.code}, {item.desc}]" in red

def test_redact_roundtrip_unredact(sample_inventory):
    from silencio2.unredact import unredact_text
    inv = sample_inventory
    item = inv.items[0]
    alias = item.aliases[0]
    original = f"{item.surface} and {alias.surface}"
    red, _ = apply_redactions(original, inv)
    restored = unredact_text(red, inv)

    assert restored == original

