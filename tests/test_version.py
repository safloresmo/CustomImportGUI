"""Tests for version module - PLUGIN_VERSION is a valid semver string."""

import re
import pytest
import version as ver


def test_version_string_exists():
    assert hasattr(ver, "__version__")
    assert isinstance(ver.__version__, str)
    assert len(ver.__version__) > 0


def test_version_is_valid_semver():
    """Version must follow MAJOR.MINOR.PATCH format."""
    semver_re = re.compile(r"^\d+\.\d+\.\d+$")
    assert semver_re.match(ver.__version__), (
        f"'{ver.__version__}' is not a valid semver (MAJOR.MINOR.PATCH)"
    )


def test_version_components_are_non_negative_integers():
    parts = ver.__version__.split(".")
    assert len(parts) == 3
    for part in parts:
        assert part.isdigit(), f"Version component '{part}' is not a digit"
        assert int(part) >= 0


def test_plugin_name_exists():
    assert hasattr(ver, "PLUGIN_NAME")
    assert isinstance(ver.PLUGIN_NAME, str)
    assert len(ver.PLUGIN_NAME) > 0


def test_plugin_version_string_exists():
    assert hasattr(ver, "PLUGIN_VERSION_STRING")
    assert isinstance(ver.PLUGIN_VERSION_STRING, str)


def test_plugin_version_string_contains_version():
    assert ver.__version__ in ver.PLUGIN_VERSION_STRING


def test_plugin_version_string_contains_name():
    assert ver.PLUGIN_NAME in ver.PLUGIN_VERSION_STRING


def test_plugin_version_string_format():
    """Should be 'PluginName vX.Y.Z'."""
    expected = f"{ver.PLUGIN_NAME} v{ver.__version__}"
    assert ver.PLUGIN_VERSION_STRING == expected
