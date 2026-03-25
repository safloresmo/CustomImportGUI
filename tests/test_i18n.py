"""Tests for i18n module - key coverage, fallback, and nested access."""

import json
import pytest
from pathlib import Path

import i18n


LOCALES_DIR = Path(__file__).parent.parent / "Origen" / "locales"


def _load_json(filename):
    path = LOCALES_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _collect_leaf_keys(d, prefix=""):
    """Recursively collect all dot-notation leaf keys from a nested dict."""
    keys = set()
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys |= _collect_leaf_keys(v, full_key)
        else:
            keys.add(full_key)
    return keys


# ---------------------------------------------------------------------------
# Key coverage between locales
# ---------------------------------------------------------------------------

def test_en_and_es_have_same_keys():
    en = _load_json("en_US.json")
    es = _load_json("es_ES.json")

    en_keys = _collect_leaf_keys(en)
    es_keys = _collect_leaf_keys(es)

    only_in_en = en_keys - es_keys
    only_in_es = es_keys - en_keys

    assert not only_in_en, f"Keys only in en_US.json: {sorted(only_in_en)}"
    assert not only_in_es, f"Keys only in es_ES.json: {sorted(only_in_es)}"


# ---------------------------------------------------------------------------
# Fallback: unknown key returns the key itself
# ---------------------------------------------------------------------------

def test_tr_returns_key_when_not_found():
    i18n.init("en_US")
    result = i18n._("this.key.does.not.exist")
    assert result == "this.key.does.not.exist"


def test_tr_returns_key_for_partial_path():
    i18n.init("en_US")
    # "gui" exists but "gui.nonexistent_key_xyz" does not
    result = i18n._("gui.nonexistent_key_xyz")
    assert result == "gui.nonexistent_key_xyz"


# ---------------------------------------------------------------------------
# Nested key access
# ---------------------------------------------------------------------------

def test_nested_key_gui_start():
    i18n.init("en_US")
    result = i18n._("gui.start")
    assert result == "Start"


def test_nested_key_gui_close():
    i18n.init("en_US")
    result = i18n._("gui.close")
    assert result == "Close"


def test_nested_key_messages_drag_drop_hint():
    i18n.init("en_US")
    result = i18n._("messages.drag_drop_hint")
    assert "drag" in result.lower() or "zip" in result.lower()


def test_nested_key_import_success():
    i18n.init("en_US")
    result = i18n._("import.success")
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Spanish locale returns different strings
# ---------------------------------------------------------------------------

def test_es_locale_returns_spanish():
    i18n.init("es_ES")
    result = i18n._("gui.start")
    # English is "Start", Spanish should be different
    assert result != "Start"
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Format arguments
# ---------------------------------------------------------------------------

def test_tr_with_format_kwargs():
    i18n.init("en_US")
    result = i18n._("messages.profile_loaded", name="TestProfile")
    assert "TestProfile" in result


def test_tr_with_missing_format_kwargs_returns_raw_string():
    """When kwargs are missing the format falls back to raw string."""
    i18n.init("en_US")
    # Pass no kwargs for a key that needs {name}; should not raise
    result = i18n._("messages.profile_loaded")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# get_language / set_language
# ---------------------------------------------------------------------------

def test_get_language_after_init():
    i18n.init("en_US")
    assert i18n.get_language() == "en_US"


def test_set_language_changes_locale():
    i18n.init("en_US")
    i18n.set_language("es_ES")
    assert i18n.get_language() == "es_ES"
    # Reset for other tests
    i18n.init("en_US")
