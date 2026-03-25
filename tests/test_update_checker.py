"""Tests for update_checker - version comparison and update detection."""

import json
import pytest
from unittest.mock import patch, MagicMock
import update_checker
from update_checker import _parse_version, _do_update_check, check_for_updates


# ---------------------------------------------------------------------------
# _parse_version
# ---------------------------------------------------------------------------

def test_parse_version_basic():
    assert _parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_with_v_prefix():
    assert _parse_version("v1.2.3") == (1, 2, 3)


def test_parse_version_zeros():
    assert _parse_version("0.0.0") == (0, 0, 0)


def test_parse_version_large_numbers():
    assert _parse_version("10.20.300") == (10, 20, 300)


def test_parse_version_invalid_returns_zero_tuple():
    assert _parse_version("not-a-version") == (0, 0, 0)


def test_parse_version_empty_string_returns_zero_tuple():
    assert _parse_version("") == (0, 0, 0)


# ---------------------------------------------------------------------------
# Version comparison logic
# ---------------------------------------------------------------------------

def test_newer_version_detected():
    assert _parse_version("1.3.0") > _parse_version("1.2.0")


def test_same_version_not_newer():
    assert not (_parse_version("1.2.0") > _parse_version("1.2.0"))


def test_older_version_not_newer():
    assert not (_parse_version("1.1.0") > _parse_version("1.2.0"))


def test_patch_version_comparison():
    assert _parse_version("1.2.1") > _parse_version("1.2.0")


def test_major_version_takes_precedence():
    assert _parse_version("2.0.0") > _parse_version("1.99.99")


# ---------------------------------------------------------------------------
# _do_update_check with mocked HTTP
# ---------------------------------------------------------------------------

def _make_github_response(tag_name, html_url="https://github.com/example/releases/v1.0.0"):
    return json.dumps({
        "tag_name": tag_name,
        "html_url": html_url,
    }).encode("utf-8")


def _mock_urlopen(raw_bytes):
    mock_response = MagicMock()
    mock_response.read.return_value = raw_bytes
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


def test_callback_called_when_newer_version_available():
    callback_args = []

    def callback(version, url):
        callback_args.append((version, url))

    raw = _make_github_response("v2.0.0", "https://github.com/example/v2.0.0")

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(raw)):
        _do_update_check("1.0.0", callback)

    assert len(callback_args) == 1
    assert callback_args[0][0] == "2.0.0"


def test_callback_not_called_when_same_version():
    callback_called = []

    with patch("urllib.request.urlopen",
               return_value=_mock_urlopen(_make_github_response("v1.2.0"))):
        _do_update_check("1.2.0", lambda v, u: callback_called.append(v))

    assert callback_called == []


def test_callback_not_called_when_older_version():
    callback_called = []

    with patch("urllib.request.urlopen",
               return_value=_mock_urlopen(_make_github_response("v1.0.0"))):
        _do_update_check("1.2.0", lambda v, u: callback_called.append(v))

    assert callback_called == []


def test_no_callback_when_tag_name_is_empty():
    callback_called = []
    raw = json.dumps({"tag_name": "", "html_url": ""}).encode("utf-8")

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(raw)):
        _do_update_check("1.0.0", lambda v, u: callback_called.append(v))

    assert callback_called == []


def test_network_error_does_not_raise():
    """A network failure should be swallowed silently."""
    with patch("urllib.request.urlopen", side_effect=Exception("network error")):
        # Should not raise
        _do_update_check("1.0.0", lambda v, u: None)


# ---------------------------------------------------------------------------
# check_for_updates - only-once guard
# ---------------------------------------------------------------------------

def test_check_for_updates_only_runs_once(monkeypatch):
    """check_for_updates should skip the second call in the same session."""
    # Reset the module-level flag
    monkeypatch.setattr(update_checker, "_update_checked", False)

    threads_started = []

    original_thread_start = None

    class FakeThread:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args
            self.daemon = daemon

        def start(self):
            threads_started.append(self)

    with patch("update_checker.Thread", FakeThread):
        check_for_updates("1.0.0", lambda v, u: None)
        check_for_updates("1.0.0", lambda v, u: None)

    assert len(threads_started) == 1


def test_check_for_updates_resets_flag(monkeypatch):
    """After resetting _update_checked, a new check should start."""
    monkeypatch.setattr(update_checker, "_update_checked", False)

    threads_started = []

    class FakeThread:
        def __init__(self, target, args, daemon):
            pass

        def start(self):
            threads_started.append(True)

    with patch("update_checker.Thread", FakeThread):
        check_for_updates("1.0.0", lambda v, u: None)

    assert len(threads_started) == 1
