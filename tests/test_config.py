"""Tests for ConfigHandler - profile CRUD, get/set, and file I/O."""

import pytest
from pathlib import Path
from ConfigHandler import ConfigHandler


@pytest.fixture
def cfg(tmp_path):
    """Create a ConfigHandler backed by a temporary directory."""
    config_file = tmp_path / "test_config.ini"
    return ConfigHandler(str(config_file))


# ---------------------------------------------------------------------------
# Basic file creation
# ---------------------------------------------------------------------------

def test_config_file_is_created(tmp_path):
    config_file = tmp_path / "new_config.ini"
    assert not config_file.exists()
    ConfigHandler(str(config_file))
    assert config_file.exists()


def test_default_values_are_set(cfg):
    assert cfg.get_library_name() == "CustomLibrary"
    assert cfg.get_library_variable() == "${CUSTOM_LIBRARY}"


# ---------------------------------------------------------------------------
# get / set paths
# ---------------------------------------------------------------------------

def test_set_and_get_src_path(cfg, tmp_path):
    new_src = str(tmp_path / "my_src")
    cfg.set_SRC_PATH(new_src)
    assert cfg.get_SRC_PATH() == new_src


def test_set_and_get_dest_path(cfg, tmp_path):
    new_dest = str(tmp_path / "my_dest")
    cfg.set_DEST_PATH(new_dest)
    assert cfg.get_DEST_PATH() == new_dest


# ---------------------------------------------------------------------------
# Library name / variable
# ---------------------------------------------------------------------------

def test_set_and_get_library_name(cfg):
    cfg.set_library_name("MictlanTeam")
    assert cfg.get_library_name() == "MictlanTeam"


def test_set_and_get_library_variable(cfg):
    cfg.set_library_variable("${MY_VAR}")
    assert cfg.get_library_variable() == "${MY_VAR}"


# ---------------------------------------------------------------------------
# Generic get/set value
# ---------------------------------------------------------------------------

def test_set_value_creates_key(cfg):
    cfg.set_value("custom_key", "custom_value")
    assert cfg.get_value("custom_key") == "custom_value"


def test_get_value_missing_key_returns_none(cfg):
    assert cfg.get_value("nonexistent_key_xyz") is None


def test_set_value_custom_section(cfg):
    cfg.set_value("foo", "bar", section="mysection")
    assert cfg.get_value("foo", section="mysection") == "bar"


# ---------------------------------------------------------------------------
# Profile CRUD
# ---------------------------------------------------------------------------

def test_predefined_profiles_exist(cfg):
    profiles = cfg.get_available_profiles()
    assert "MictlanTeam" in profiles
    assert "CustomLibrary" in profiles


def test_save_and_load_profile(cfg, tmp_path):
    new_dest = str(tmp_path / "profile_dest")
    cfg.set_DEST_PATH(new_dest)
    cfg.set_library_name("TestLib")
    cfg.save_current_as_profile("TestProfile")

    # Overwrite current settings before loading
    cfg.set_library_name("OverwrittenLib")

    result = cfg.load_profile("TestProfile")
    assert result is True
    assert cfg.get_library_name() == "TestLib"


def test_load_nonexistent_profile_returns_false(cfg):
    assert cfg.load_profile("ghost_profile_xyz") is False


def test_delete_custom_profile(cfg):
    cfg.save_current_as_profile("DeleteMe")
    assert "DeleteMe" in cfg.get_available_profiles()
    result = cfg.delete_profile("DeleteMe")
    assert result is True
    assert "DeleteMe" not in cfg.get_available_profiles()


def test_cannot_delete_predefined_profile(cfg):
    result = cfg.delete_profile("MictlanTeam")
    assert result is False
    assert "MictlanTeam" in cfg.get_available_profiles()


def test_delete_nonexistent_profile_returns_false(cfg):
    assert cfg.delete_profile("i_do_not_exist") is False


# ---------------------------------------------------------------------------
# organize_by_category
# ---------------------------------------------------------------------------

def test_organize_by_category_default_false(cfg):
    assert cfg.get_organize_by_category() is False


def test_set_organize_by_category(cfg):
    cfg.set_organize_by_category(True)
    assert cfg.get_organize_by_category() is True
    cfg.set_organize_by_category(False)
    assert cfg.get_organize_by_category() is False


# ---------------------------------------------------------------------------
# Persistence: values survive a reload
# ---------------------------------------------------------------------------

def test_values_persist_after_reload(tmp_path):
    config_file = tmp_path / "persist.ini"
    c1 = ConfigHandler(str(config_file))
    c1.set_library_name("PersistLib")
    c1.set_library_variable("${PERSIST_VAR}")

    c2 = ConfigHandler(str(config_file))
    assert c2.get_library_name() == "PersistLib"
    assert c2.get_library_variable() == "${PERSIST_VAR}"
