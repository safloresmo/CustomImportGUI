"""Single source of truth for plugin version, read from metadata.json."""

import json
from pathlib import Path

_plugin_dir = Path(__file__).resolve().parent

# metadata.json can be in the same dir (dev) or parent dir (PCM install)
_candidates = [
    _plugin_dir / "metadata.json",
    _plugin_dir.parent / "metadata.json",
]

__version__ = "1.3.0"  # hardcoded fallback

for _path in _candidates:
    try:
        if _path.exists():
            with open(_path, "r", encoding="utf-8") as f:
                _metadata = json.load(f)
            __version__ = _metadata["versions"][0]["version"]
            break
    except Exception:
        continue

PLUGIN_NAME = "CustomImportGUI"
PLUGIN_VERSION_STRING = f"{PLUGIN_NAME} v{__version__}"
