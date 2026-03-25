"""Tests for backend-related logic that does NOT require wx or KiCad.

Covers:
- _check_single_library: file-system checks with mocked KiCad_Settings
- check_library_import: graceful handling of missing paths / no project
"""

import os
import pytest
from unittest.mock import MagicMock, patch


# We import only the standalone helpers, not ImpartBackend (which needs KiCad)
from impart_backend import _check_single_library, check_library_import


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_kicad_settings_mock():
    """Return a minimal KiCad_Settings mock."""
    ks = MagicMock()
    ks.check_symbollib.return_value = ""
    ks.check_footprintlib.return_value = ""
    ks.check_GlobalVar.return_value = ""
    return ks


# ---------------------------------------------------------------------------
# _check_single_library - symbol variants
# ---------------------------------------------------------------------------

def test_check_single_library_no_files_returns_empty(tmp_path):
    ks = _make_kicad_settings_mock()
    result = _check_single_library(ks, "Octopart", str(tmp_path), True)
    assert result == ""
    ks.check_symbollib.assert_not_called()
    ks.check_footprintlib.assert_not_called()


def test_check_single_library_finds_kicad_sym(tmp_path):
    (tmp_path / "Octopart.kicad_sym").write_text("", encoding="utf-8")
    ks = _make_kicad_settings_mock()

    _check_single_library(ks, "Octopart", str(tmp_path), True)

    ks.check_symbollib.assert_called_once_with("Octopart.kicad_sym", True)


def test_check_single_library_finds_variant_kicad_sym(tmp_path):
    """Prefers first variant, falls through to _kicad_sym variant."""
    (tmp_path / "Samacsys_kicad_sym.kicad_sym").write_text("", encoding="utf-8")
    ks = _make_kicad_settings_mock()

    _check_single_library(ks, "Samacsys", str(tmp_path), True)

    ks.check_symbollib.assert_called_once_with("Samacsys_kicad_sym.kicad_sym", True)


def test_check_single_library_finds_old_lib_variant(tmp_path):
    (tmp_path / "UltraLibrarian_old_lib.kicad_sym").write_text("", encoding="utf-8")
    ks = _make_kicad_settings_mock()

    _check_single_library(ks, "UltraLibrarian", str(tmp_path), True)

    ks.check_symbollib.assert_called_once_with("UltraLibrarian_old_lib.kicad_sym", True)


def test_check_single_library_only_first_sym_variant_used(tmp_path):
    """When multiple symbol variants exist, only the first match is used."""
    (tmp_path / "Snapeda.kicad_sym").write_text("", encoding="utf-8")
    (tmp_path / "Snapeda_kicad_sym.kicad_sym").write_text("", encoding="utf-8")
    ks = _make_kicad_settings_mock()

    _check_single_library(ks, "Snapeda", str(tmp_path), True)

    assert ks.check_symbollib.call_count == 1
    ks.check_symbollib.assert_called_once_with("Snapeda.kicad_sym", True)


# ---------------------------------------------------------------------------
# _check_single_library - footprint .pretty directory
# ---------------------------------------------------------------------------

def test_check_single_library_finds_pretty_dir(tmp_path):
    pretty_dir = tmp_path / "Octopart.pretty"
    pretty_dir.mkdir()
    ks = _make_kicad_settings_mock()

    _check_single_library(ks, "Octopart", str(tmp_path), True)

    ks.check_footprintlib.assert_called_once_with("Octopart", True)


def test_check_single_library_no_pretty_dir_skips_footprint(tmp_path):
    ks = _make_kicad_settings_mock()
    _check_single_library(ks, "Octopart", str(tmp_path), True)
    ks.check_footprintlib.assert_not_called()


def test_check_single_library_returns_combined_messages(tmp_path):
    (tmp_path / "EasyEDA.kicad_sym").write_text("", encoding="utf-8")
    (tmp_path / "EasyEDA.pretty").mkdir()

    ks = _make_kicad_settings_mock()
    ks.check_symbollib.return_value = "sym_ok"
    ks.check_footprintlib.return_value = "fp_ok"

    result = _check_single_library(ks, "EasyEDA", str(tmp_path), True)

    assert "sym_ok" in result
    assert "fp_ok" in result


def test_check_single_library_add_if_possible_false(tmp_path):
    (tmp_path / "Octopart.kicad_sym").write_text("", encoding="utf-8")
    ks = _make_kicad_settings_mock()

    _check_single_library(ks, "Octopart", str(tmp_path), False)

    ks.check_symbollib.assert_called_once_with("Octopart.kicad_sym", False)


# ---------------------------------------------------------------------------
# check_library_import - no KiCad project (local_lib mode)
# ---------------------------------------------------------------------------

def test_check_library_import_local_lib_no_project():
    """When local_lib=True and no project is open, return a graceful message."""
    backend = MagicMock()
    backend.local_lib = True
    backend.kicad_app.get_project_dir.return_value = None

    result = check_library_import(backend, add_if_possible=True)

    assert isinstance(result, str)
    assert "local" in result.lower() or "project" in result.lower()


def test_check_library_import_global_mode_calls_check_global_var(tmp_path):
    """In global mode, check_GlobalVar must be called with the dest path."""
    backend = MagicMock()
    backend.local_lib = False
    backend.kicad_settings = _make_kicad_settings_mock()
    backend.config.get_DEST_PATH.return_value = str(tmp_path)
    backend.config.get_library_variable.return_value = "${MY_LIB}"

    check_library_import(backend, add_if_possible=True)

    backend.kicad_settings.check_GlobalVar.assert_called_once_with(
        str(tmp_path), True, var_name="${MY_LIB}"
    )


def test_check_library_import_global_mode_checks_all_supported_libraries(tmp_path):
    """check_library_import iterates over all SUPPORTED_LIBRARIES."""
    from impart_backend import ImpartBackend

    backend = MagicMock()
    backend.local_lib = False
    backend.kicad_settings = _make_kicad_settings_mock()
    backend.config.get_DEST_PATH.return_value = str(tmp_path)
    backend.config.get_library_variable.return_value = "${MY_LIB}"

    with patch("impart_backend._check_single_library", return_value="") as mock_csl:
        check_library_import(backend, add_if_possible=False)

    assert mock_csl.call_count == len(ImpartBackend.SUPPORTED_LIBRARIES)


def test_check_library_import_returns_string(tmp_path):
    backend = MagicMock()
    backend.local_lib = False
    backend.kicad_settings = _make_kicad_settings_mock()
    backend.config.get_DEST_PATH.return_value = str(tmp_path)
    backend.config.get_library_variable.return_value = "${MY_LIB}"

    result = check_library_import(backend)

    assert isinstance(result, str)
