"""
Update checker for CustomImportGUI plugin.
Checks GitHub releases API in a background thread on startup.
"""

import json
import logging
import urllib.request
import urllib.error
import ssl
from threading import Thread

logger = logging.getLogger(__name__)

GITHUB_RELEASES_URL = "https://api.github.com/repos/safloresmo/CustomImportGUI/releases/latest"
_update_checked = False


def _parse_version(version_str: str):
    """Parse a version string like '1.2.0' into a tuple of ints for comparison."""
    try:
        return tuple(int(x) for x in version_str.lstrip("v").split("."))
    except Exception:
        return (0, 0, 0)


def _do_update_check(current_version: str, callback) -> None:
    """Run in a background thread. Fetches latest release from GitHub and calls callback."""
    try:
        ctx = ssl.create_default_context()
        try:
            import certifi
            ctx.load_verify_locations(cafile=certifi.where())
        except (ImportError, Exception):
            pass

        req = urllib.request.Request(
            GITHUB_RELEASES_URL,
            headers={"User-Agent": "CustomImportGUI/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            data = json.loads(response.read())

        latest_tag = data.get("tag_name", "")
        html_url = data.get("html_url", GITHUB_RELEASES_URL)

        if not latest_tag:
            return

        latest_version = latest_tag.lstrip("v")
        if _parse_version(latest_version) > _parse_version(current_version):
            callback(latest_version, html_url)

    except Exception as e:
        logger.debug(f"Update check failed (no internet or error): {e}")


def check_for_updates(current_version: str, on_update_available) -> None:
    """
    Start a background thread to check for plugin updates.
    Only checks once per session.

    Args:
        current_version: Current plugin version string (e.g. '1.2.0')
        on_update_available: Callable(version: str, url: str) called if a newer version exists
    """
    global _update_checked
    if _update_checked:
        return
    _update_checked = True

    thread = Thread(
        target=_do_update_check,
        args=(current_version, on_update_available),
        daemon=True,
    )
    thread.start()
