"""Tests for ImportHistory - add, get, clear, is_already_imported."""

import json
import pytest
from ImportHistory import ImportHistory


@pytest.fixture
def history(tmp_path):
    return ImportHistory(history_dir=tmp_path)


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------

def test_initial_count_is_zero(history):
    assert history.get_count() == 0


def test_initial_entries_are_empty(history):
    assert history.get_entries() == []


def test_is_already_imported_on_empty_returns_none(history):
    assert history.is_already_imported("SomeComponent") is None


# ---------------------------------------------------------------------------
# add_entry / get_entries / get_count
# ---------------------------------------------------------------------------

def test_add_entry_increments_count(history):
    history.add_entry("Resistor", "EasyEDA", "MyLib")
    assert history.get_count() == 1


def test_add_multiple_entries(history):
    history.add_entry("Resistor", "EasyEDA", "MyLib")
    history.add_entry("Capacitor", "JLCPCB", "MyLib")
    assert history.get_count() == 2


def test_get_entries_newest_first(history):
    history.add_entry("First", "EasyEDA", "MyLib")
    history.add_entry("Second", "EasyEDA", "MyLib")
    entries = history.get_entries()
    assert entries[0]["component"] == "Second"
    assert entries[1]["component"] == "First"


def test_get_entries_with_limit(history):
    for i in range(5):
        history.add_entry(f"Component{i}", "EasyEDA", "MyLib")
    entries = history.get_entries(limit=3)
    assert len(entries) == 3


def test_get_entries_limit_zero_returns_all(history):
    for i in range(5):
        history.add_entry(f"Component{i}", "EasyEDA", "MyLib")
    entries = history.get_entries(limit=0)
    assert len(entries) == 5


def test_entry_fields_are_correct(history):
    history.add_entry(
        component_name="ESP32",
        source="EasyEDA",
        library_name="MyLib",
        zip_file="esp32.zip",
        profile="Default",
    )
    entry = history.get_entries()[0]
    assert entry["component"] == "ESP32"
    assert entry["source"] == "EasyEDA"
    assert entry["library"] == "MyLib"
    assert entry["file"] == "esp32.zip"
    assert entry["profile"] == "Default"
    assert "date" in entry


# ---------------------------------------------------------------------------
# is_already_imported
# ---------------------------------------------------------------------------

def test_is_already_imported_case_insensitive(history):
    history.add_entry("ESP32", "EasyEDA", "MyLib")
    assert history.is_already_imported("esp32") is not None
    assert history.is_already_imported("ESP32") is not None
    assert history.is_already_imported("Esp32") is not None


def test_is_already_imported_returns_entry(history):
    history.add_entry("LM7805", "JLCPCB", "MyLib")
    result = history.is_already_imported("LM7805")
    assert result is not None
    assert result["component"] == "LM7805"


def test_is_already_imported_returns_none_for_unknown(history):
    history.add_entry("ESP32", "EasyEDA", "MyLib")
    assert history.is_already_imported("STM32") is None


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

def test_clear_removes_all_entries(history):
    history.add_entry("Resistor", "EasyEDA", "MyLib")
    history.add_entry("Capacitor", "EasyEDA", "MyLib")
    history.clear()
    assert history.get_count() == 0
    assert history.get_entries() == []


# ---------------------------------------------------------------------------
# Persistence: JSON file is written and reloaded
# ---------------------------------------------------------------------------

def test_history_persists_to_disk(tmp_path):
    h1 = ImportHistory(history_dir=tmp_path)
    h1.add_entry("Diode", "Snapeda", "MyLib")

    h2 = ImportHistory(history_dir=tmp_path)
    assert h2.get_count() == 1
    assert h2.get_entries()[0]["component"] == "Diode"


def test_history_file_is_valid_json(tmp_path):
    h = ImportHistory(history_dir=tmp_path)
    h.add_entry("Transistor", "Samacsys", "MyLib")
    history_file = tmp_path / "import_history.json"
    data = json.loads(history_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data[0]["component"] == "Transistor"


def test_clear_writes_empty_json(tmp_path):
    h = ImportHistory(history_dir=tmp_path)
    h.add_entry("X", "Y", "Z")
    h.clear()
    history_file = tmp_path / "import_history.json"
    data = json.loads(history_file.read_text(encoding="utf-8"))
    assert data == []


# ---------------------------------------------------------------------------
# Corrupt file handling
# ---------------------------------------------------------------------------

def test_corrupt_json_file_results_in_empty_history(tmp_path):
    history_file = tmp_path / "import_history.json"
    history_file.write_text("this is not valid json", encoding="utf-8")
    h = ImportHistory(history_dir=tmp_path)
    assert h.get_count() == 0
